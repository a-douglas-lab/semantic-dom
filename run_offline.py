"""Offline simulator: token / cost / latency per strategy over editing sessions, plus
impact-analysis recall/precision against gold. No API calls.

Usage: python run_offline.py [--model claude-opus-5-5] [--passes 2]
Writes results/offline.json and results/offline.md.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from evalset.build import OUT as CORPUS
from evalset.build import build
from retrieval import make_graph
from sdom.costs import (
    MIN_CACHEABLE,
    PLAIN_OVERHEAD,
    SCHEMA_OVERHEAD,
    TOKEN_SCALE,
    TOKEN_SCALE_TAGGED,
    Usage,
    cost_usd,
    latency_s,
)
from sdom.dom import Document, est_tokens
from sdom.graph import SemanticGraph
from sdom.local_ops import plan_local
from sdom.strategies import est_output_tokens, pack

# minutes between consecutive edit requests
SCENARIOS = {"rapid": [1], "human": [2, 7, 3, 12, 4], "async": [20, 45, 30]}
VARIANTS = [("B0", "5m"), ("B1", "5m"), ("B1", "1h"), ("B2", "5m"), ("S", "5m"), ("SL", "5m")]
TTL_MIN = {"5m": 5, "1h": 60}


def simulate(
    doc: Document,
    graph: SemanticGraph,
    cases: list[dict],
    strategy: str,
    ttl: str,
    gaps: list[int],
    passes: int,
    skeleton: str | None = None,
) -> dict:
    total, turns = Usage(), []
    prev_cacheable, prev_time, hist, prev_frac, t = 0, None, 0, 1.0, 0.0
    seq = [c for _ in range(passes) for c in cases]
    for i, case in enumerate(seq):
        if i:
            t += gaps[(i - 1) % len(gaps)]
        if strategy == "SL" and plan_local(case["instruction"]):
            # harness applies the rename locally: no request, cache timer not refreshed
            turns.append(
                {
                    "case": case["id"],
                    "in": 0,
                    "read": 0,
                    "write": 0,
                    "uncached": 0,
                    "out": 0,
                    "cost": 0.0,
                    "ttft": 0.0,
                    "latency": 0.0,
                }
            )
            continue
        p = pack("S" if strategy == "SL" else strategy, doc, graph, case["instruction"], skeleton)

        scale = TOKEN_SCALE if strategy in ("B0", "B1") else TOKEN_SCALE_TAGGED
        overhead = PLAIN_OVERHEAD if strategy == "B0" else SCHEMA_OVERHEAD
        sys_t = round(est_tokens(p.system) * scale) + overhead
        stable_t, vol_t = round(est_tokens(p.stable) * scale), round(est_tokens(p.volatile) * scale)
        out = round(est_output_tokens("S" if strategy == "SL" else strategy, doc, case["gold"]["must"]) * scale)
        if strategy == "B0":
            cacheable, tail = sys_t + stable_t, vol_t
            shared = sys_t + int(stable_t * prev_frac)  # doc changed from the previous edit point onwards
        elif strategy == "B1":  # conversation grows; auto cache breakpoint at the end
            cacheable, tail = sys_t + stable_t + hist + vol_t, 0
            shared = prev_cacheable
        elif strategy == "B2":  # no cache breakpoint (nothing stable worth caching)
            cacheable, tail, shared = 0, sys_t + vol_t, 0
        else:  # S: stateless requests; system + session-frozen skeleton are the reusable prefix
            cacheable, tail = sys_t + stable_t, vol_t
            shared = cacheable
        warm = prev_time is not None and (t - prev_time) <= TTL_MIN[ttl]
        u = Usage(out=out)
        if cacheable >= MIN_CACHEABLE:
            u.cache_read = min(shared, cacheable) if warm else 0
            u.cache_write = cacheable - u.cache_read
            u.uncached_in = tail
        else:
            u.uncached_in = cacheable + tail
        ttft, lat = latency_s(u)
        turns.append(
            {
                "case": case["id"],
                "in": u.total_in,
                "read": u.cache_read,
                "write": u.cache_write,
                "uncached": u.uncached_in,
                "out": out,
                "cost": cost_usd(u, ttl=ttl),
                "ttft": ttft,
                "latency": lat,
            }
        )
        total += u
        prev_cacheable, prev_time = cacheable, t
        if strategy == "B1":
            hist += vol_t + out
        if strategy == "B0" and case["gold"]["must"]:
            prev_frac = min(doc.offset_fraction(m) for m in case["gold"]["must"])
    return {
        "cost": sum(x["cost"] for x in turns),
        "in": total.total_in,
        "out": total.out,
        "read": total.cache_read,
        "write": total.cache_write,
        "uncached": total.uncached_in,
        "ttft_mean": sum(x["ttft"] for x in turns) / len(turns),
        "latency_mean": sum(x["latency"] for x in turns) / len(turns),
        "turns": turns,
    }


def context_quality(doc: Document, graph: SemanticGraph, cases: list[dict], strategy: str) -> list[dict]:
    rows = []
    for c in cases:
        p = pack(strategy, doc, graph, c["instruction"])
        must = set(c["gold"]["must"])
        ctx_items = {i for i in p.context_ids if doc.nodes[i].kind != "doc"}
        relevant = must | set(c["gold"]["allowed"])
        rows.append(
            {
                "case": c["id"],
                "kind": c["kind"],
                "must": len(must),
                "recall": len(must & ctx_items) / len(must) if must else 1.0,
                "precision": len(relevant & ctx_items) / len(ctx_items) if ctx_items else 0.0,
                "ctx_nodes": len(ctx_items),
                "ctx_tokens": est_tokens(p.stable) + est_tokens(p.volatile),
                "missed": sorted(must - ctx_items)[:5],
                "distractors_in_ctx": len(set(c["gold"]["no_change"]) & ctx_items),
            }
        )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=2, help="times each doc's case list is replayed per session")
    ap.add_argument(
        "--retriever", default="all-bge", help="matching method (spec 009 default); 'regex' is the stdlib-only fallback"
    )
    args = ap.parse_args()
    manifest = build()
    results = {"sessions": [], "quality": []}
    for m in manifest:
        md = (CORPUS / f"{m['doc']}.md").read_text(encoding="utf-8")
        cases = json.loads((CORPUS / f"{m['doc']}.cases.json").read_text(encoding="utf-8"))
        doc = Document.parse(md, m["type"])
        graph = make_graph(doc, args.retriever)
        for scen, gaps in SCENARIOS.items():
            for strat, ttl in VARIANTS:
                r = simulate(doc, graph, cases, strat, ttl, gaps, args.passes)
                results["sessions"].append(
                    {
                        "doc": m["doc"],
                        "tokens": m["tokens_est"],
                        "scenario": scen,
                        "strategy": strat + ("" if ttl == "5m" else "-1h"),
                        **{k: v for k, v in r.items() if k != "turns"},
                    }
                )
        for strat in ("B2", "S"):
            for row in context_quality(doc, graph, cases, strat):
                results["quality"].append({"doc": m["doc"], "strategy": strat, **row})
    out = Path("results")
    out.mkdir(exist_ok=True)
    (out / "offline.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    report = render_report(results, manifest, args.passes)
    (out / "offline.md").write_text(report, encoding="utf-8")
    print(report)


def render_report(results: dict, manifest: list[dict], passes: int) -> str:
    L = [
        "# Offline simulation results",
        "",
        f"Model pricing: Claude Opus 5.5. Session = each doc's edit cases x{passes}. "
        "Tokens are estimates (chars/4); output assumes exact gold edits; thinking tokens excluded.",
        "",
    ]
    by = defaultdict(dict)
    for s in results["sessions"]:
        by[(s["doc"], s["scenario"])][s["strategy"]] = s
    strategies = ["B0", "B1", "B1-1h", "B2", "S", "SL"]
    for scen in SCENARIOS:
        L += [
            f"## Scenario: {scen} (gaps {SCENARIOS[scen]} min)",
            "",
            "| doc | ~tokens | "
            + " | ".join(f"{s} $" for s in strategies)
            + " | S vs B1 | S vs best B1 | SL vs best B1 | S latency vs B1 |",
            "|---|---:|" + "---:|" * (len(strategies) + 4),
        ]
        for m in manifest:
            row = by[(m["doc"], scen)]
            b1 = row["B1"]["cost"]
            best = min(row["B1"]["cost"], row["B1-1h"]["cost"])
            sv = row["S"]["cost"]
            lat = row["S"]["latency_mean"] / row["B1"]["latency_mean"]
            L.append(
                f"| {m['doc']} | {m['tokens_est']:,} | "
                + " | ".join(f"{row[s]['cost']:.4f}" for s in strategies)
                + f" | {1 - sv / b1:+.0%} | {1 - sv / best:+.0%} | {1 - row['SL']['cost'] / best:+.0%} | {lat:.2f}x |"
            )
        L.append("")
    L += [
        "## Context quality (does the packed context contain every node that must change?)",
        "",
        "| doc | case | kind | strategy | must | recall | precision | ctx nodes | ctx ~tokens | missed |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for q in results["quality"]:
        L.append(
            f"| {q['doc']} | {q['case'].split('-', 2)[-1]} | {q['kind']} | {q['strategy']} | {q['must']} | "
            f"{q['recall']:.0%} | {q['precision']:.0%} | {q['ctx_nodes']} | {q['ctx_tokens']:,} | {', '.join(q['missed'])} |"
        )
    agg = defaultdict(list)
    for q in results["quality"]:
        agg[(q["strategy"], q["kind"])].append(q["recall"])
    L += ["", "### Mean context recall by edit kind", "", "| kind | B2 | S |", "|---|---:|---:|"]
    for kind in sorted({k for _, k in agg}):
        b2, s = agg[("B2", kind)], agg[("S", kind)]
        L.append(f"| {kind} | {sum(b2) / len(b2):.0%} | {sum(s) / len(s):.0%} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
