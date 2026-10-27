"""Live runner: real API calls per strategy, measured usage/latency, patches applied and scored.

Usage:
  python run_live.py --docs cv-S,contract-S --strategies B1,B2,S        # needs credentials
  python run_live.py --dry-run                                           # oracle responses, no API calls

Each doc's cases run in order as one editing session per strategy (state carries over).
Every run spends real money; start with S/M docs.
"""

import argparse
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from evalset.build import OUT as CORPUS
from evalset.build import build
from retrieval import VARIANTS, make_graph
from sdom.budget import BudgetExceeded, Ledger
from sdom.costs import Usage, cost_usd
from sdom.dom import Document, diff_ids, est_tokens
from sdom.local_ops import apply_local, plan_local
from sdom.strategies import SCHEMA, Packed, apply_output, followup_pack, pack


def load_dotenv(path: Path) -> None:
    """Set KEY=VALUE lines from a gitignored .env into the environment (existing vars win)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():  # tolerate BOM from PowerShell 5.1
        key, sep, value = line.strip().partition("=")
        if sep and key and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def make_client():  # type: ignore[no-untyped-def]
    """Anthropic client; adds the workspace header when the key isn't workspace-scoped."""
    import anthropic

    ws = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    return anthropic.Anthropic(default_headers={"anthropic-workspace-id": ws} if ws else None)


class Oracle:
    """Dry-run stand-in for the API: returns well-formed edits touching exactly the gold nodes."""

    def respond(self, strategy, doc, packed, case):
        must = [m for m in case["gold"]["must"] if m in doc.nodes]
        if strategy == "B0":
            for m in must:
                doc.nodes[m].text += " (edited)"
            md = doc.render()
            for m in must:
                doc.nodes[m].text = doc.nodes[m].text.removesuffix(" (edited)")
            return md
        if strategy == "B1":
            return json.dumps(
                {"edits": [{"old": doc.nodes[m].text, "new": doc.nodes[m].text + " (edited)"} for m in must]}
            )
        ops = [
            {"id": m, "find": "", "replace": doc.nodes[m].text + " (edited)"} for m in must if m in packed.context_ids
        ]
        return json.dumps({"ops": ops, "flagged": []})


def build_request(strategy, packed, history, model, effort, ttl="5m", salt=""):
    """`salt` tags the system prompt so separate runs never share a cache entry (V2 repeats)."""
    cc = {"type": "ephemeral", "ttl": "1h"} if ttl == "1h" else {"type": "ephemeral"}
    system = f"{packed.system}\n\nSession: {salt}" if salt else packed.system
    sys_blocks = [{"type": "text", "text": system}]
    if strategy == "B1":
        if not history:
            user = [
                {"type": "text", "text": packed.stable, "cache_control": cc},
                {"type": "text", "text": packed.volatile},
            ]
        else:
            user = [{"type": "text", "text": packed.volatile}]
        messages = [*history, {"role": "user", "content": user}]
        # second breakpoint at the end so the growing conversation is cached too
        messages[-1]["content"][-1] = {**messages[-1]["content"][-1], "cache_control": cc}
    elif packed.stable:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": packed.stable, "cache_control": cc},
                    {"type": "text", "text": packed.volatile},
                ],
            }
        ]
    else:
        messages = [{"role": "user", "content": [{"type": "text", "text": packed.volatile}]}]
    output_config = {"effort": effort}
    if strategy in SCHEMA:
        output_config["format"] = {"type": "json_schema", "schema": SCHEMA[strategy]}
    return {
        "model": model,
        "max_tokens": 64000,
        "system": sys_blocks,
        "messages": messages,
        "output_config": output_config,
    }


PREWARM_MAX_TOKENS = 64
PRELOAD_TEXT = "The document is open. No edit yet: return an empty edit list."


def prewarm_request(strategy, packed, model, effort, ttl="5m", salt=""):
    """Tiny request that writes the same cached prefix the first edit will read (cache prewarm at document open)."""
    req = build_request(strategy, Packed(packed.system, packed.stable, PRELOAD_TEXT), [], model, effort, ttl, salt)
    req["max_tokens"] = PREWARM_MAX_TOKENS
    return req


def preload(args, eff, doc, skeleton, client, ledger, edges, note):
    """Work a product would do when the document opens, outside per-edit timing: build the retrieval index
    (graph + embeddings, cached per node text) and write the prompt cache. Its spend still counts."""
    t0 = time.perf_counter()
    graph = None if eff in ("B0", "B1") else make_graph(doc, args.retriever, edges=edges)
    index_s = time.perf_counter() - t0 if graph is not None else 0.0
    t1, usd = time.perf_counter(), 0.0
    packed = pack(eff, doc, graph, PRELOAD_TEXT, skeleton)
    if packed.stable and not args.dry_run:
        req = prewarm_request(eff, packed, args.model, args.effort, args.ttl, args.salt)
        ledger.check(
            cost_usd(Usage(cache_write=est_tokens(packed.stable), out=PREWARM_MAX_TOKENS), args.model, args.ttl)
        )
        _, usage, _, _, _ = call_api(client, req)
        usd = cost_usd(usage, args.model, args.ttl)
        ledger.record(usd, f"{note}/preload")
    return {"preload_index_s": index_s, "preload_cache_s": time.perf_counter() - t1, "preload_usd": usd}


def strip_cache_markers(messages):
    """Keep only the first breakpoint in stored history (max 4 per request)."""
    out = []
    for i, m in enumerate(messages):
        content = m["content"]
        if isinstance(content, list):
            content = [
                {k: v for k, v in b.items() if k != "cache_control" or (i == 0 and j == 0)}
                for j, b in enumerate(content)
            ]
        out.append({**m, "content": content})
    return out


def call_api(client, req):
    t0 = time.perf_counter()
    ttft = None
    with client.messages.stream(**req) as stream:
        for event in stream:
            if ttft is None and event.type == "content_block_delta":
                ttft = time.perf_counter() - t0
        msg = stream.get_final_message()
    total = time.perf_counter() - t0
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"refusal: {msg.stop_details}")
    text = "".join(b.text for b in msg.content if b.type == "text")
    u = msg.usage
    usage = Usage(
        uncached_in=u.input_tokens,
        cache_read=u.cache_read_input_tokens or 0,
        cache_write=u.cache_creation_input_tokens or 0,
        out=u.output_tokens,
    )
    return text, usage, ttft or total, total, msg.stop_reason


def _covered(node_id: str, allowed: set[str]) -> bool:
    """True if the node or any ancestor (by ID prefix) is allowed to change."""
    parts = node_id.split(".")
    return any(".".join(parts[: i + 1]) in allowed for i in range(len(parts)))


def score(before: Document, after: Document, gold: dict) -> dict:
    changed = diff_ids(before.snapshot(), after.snapshot())
    must, allowed = set(gold["must"]), set(gold["allowed"])
    checks_ok = 0
    for nid, rx, want in gold["checks"]:
        if nid == "*":
            hit = any(re.search(rx, n.text) for n in after.nodes.values())
        else:
            hit = nid in after.nodes and bool(re.search(rx, after.nodes[nid].text))
        checks_ok += hit == want
    return {
        "must_recall": len(must & changed) / len(must) if must else 1.0,
        "collateral": sum(1 for c in changed - must if not _covered(c, allowed)),
        "distractor_changed": len(set(gold["no_change"]) & changed),
        "checks_passed": checks_ok,
        "checks_total": len(gold["checks"]),
        "changed": len(changed),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="cv-S,adr-S,contract-S")
    ap.add_argument("--strategies", default="B0,B1,B2,S")
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ttl", choices=["5m", "1h"], default="5m", help="cache TTL for cache breakpoints")
    ap.add_argument(
        "--retriever", default="all-bge", choices=list(VARIANTS), help="matching method; default per spec 009"
    )
    ap.add_argument("--edges", default="structural,schema,literal", help="edge types for impact analysis (ablation)")
    ap.add_argument("--gaps", default="", help="minutes to pause between edits, cycled, e.g. 2,7,3,12,4")
    ap.add_argument("--salt", default="", help="tag in the system prompt so runs never share a prompt cache")
    ap.add_argument(
        "--preload",
        action="store_true",
        help="at document open, outside edit timing: build the retrieval index and prewarm the prompt cache",
    )
    ap.add_argument("--tag", default="", help="results file name: results/live-<tag>.json (default: timestamp)")
    args = ap.parse_args()

    manifest = {m["doc"]: m for m in build()}
    load_dotenv(Path(".env"))
    client = None if args.dry_run else make_client()
    ledger = Ledger(Path("budget.json"), Path("results/spend.json"))
    oracle = Oracle()
    rows: list[dict] = []
    # load the embedding model once, outside per-edit timing, as a long-running service would
    t0 = time.perf_counter()
    if "S" in args.strategies or "B2" in args.strategies:
        make_graph(Document.parse("# Warm-up\n\nwarm up the retriever"), args.retriever)
    warmup_s = time.perf_counter() - t0
    try:
        run(args, manifest, client, ledger, oracle, rows)
    except BudgetExceeded as e:
        print(f"\nSTOPPED: budget guard — {e}")
    out = Path("results")
    out.mkdir(exist_ok=True)
    tag = args.tag or ("dry" if args.dry_run else datetime.now().strftime("%Y%m%d-%H%M%S"))
    meta = {
        "model": args.model,
        "effort": args.effort,
        "date": datetime.now().isoformat(timespec="seconds"),
        "git": git_sha(),
        "dry_run": args.dry_run,
        "spent_usd": round(ledger.run_spent, 4),
        "ttl": args.ttl,
        "gaps_min": args.gaps,
        "edges": args.edges,
        "retriever": args.retriever,
        "salt": args.salt,
        "preload": args.preload,
        "warmup_s": round(warmup_s, 2),
    }
    (out / f"live-{tag}.json").write_text(json.dumps({"meta": meta, "rows": rows}, indent=2), encoding="utf-8")
    print(f"\nwrote results/live-{tag}.json  (spent ${ledger.run_spent:.4f} this run, ${ledger.total_spent:.4f} total)")


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def run(args, manifest, client, ledger, oracle, rows):
    gaps = [float(g) for g in args.gaps.split(",") if g]
    edges = frozenset(args.edges.split(","))
    for doc_name in args.docs.split(","):
        m = manifest[doc_name]
        md = (CORPUS / f"{doc_name}.md").read_text(encoding="utf-8")
        cases = json.loads((CORPUS / f"{doc_name}.cases.json").read_text(encoding="utf-8"))
        for strategy in args.strategies.split(","):
            doc, history = Document.parse(md, m["type"]), []
            skeleton = doc.skeleton()  # frozen for the session so S's cached prefix stays byte-stable
            eff0 = "S" if strategy in ("SL", "SF") else strategy
            opened = (
                preload(args, eff0, doc, skeleton, client, ledger, edges, f"{doc_name}/{strategy}")
                if args.preload
                else {}
            )
            for ci, case in enumerate(cases):
                t0 = time.perf_counter()
                followups = 0
                eff = "S" if strategy in ("SL", "SF") else strategy  # SL: + local ops; SF: + flag follow-up
                local = plan_local(case["instruction"]) if strategy == "SL" else None
                if local:
                    new_doc, _ = apply_local(doc, local)
                    harness_s = time.perf_counter() - t0
                    text, est_in, usage, ttft, total, stop = "", 0, Usage(), 0.0, harness_s, "local"
                    errors, flagged = [], []
                else:
                    # baselines send the whole document: building a graph for them would only distort timing
                    graph = None if eff in ("B0", "B1") else make_graph(doc, args.retriever, edges=edges)
                    packed = pack(eff, doc, graph, case["instruction"], skeleton)
                    harness_s = time.perf_counter() - t0
                    req = build_request(eff, packed, history, args.model, args.effort, args.ttl, args.salt)
                    est_in = sum(est_tokens(b["text"]) for b in req["system"]) + sum(
                        est_tokens(b["text"]) if isinstance(b, dict) else est_tokens(b)
                        for msg in req["messages"]
                        for b in (msg["content"] if isinstance(msg["content"], list) else [msg["content"]])
                    )
                    if args.dry_run:
                        text = oracle.respond(eff, doc, packed, case)
                        usage, ttft, total, stop = Usage(uncached_in=est_in, out=est_tokens(text)), 0.0, 0.0, "dry_run"
                    else:
                        exp_out = est_tokens(md) if eff == "B0" else 2000  # incl. thinking headroom
                        ledger.check(cost_usd(Usage(cache_write=est_in, out=exp_out), args.model, args.ttl))
                        text, usage, ttft, total, stop = call_api(client, req)
                        ledger.record(cost_usd(usage, args.model, args.ttl), f"{doc_name}/{strategy}/{case['id']}")
                    new_doc, errors, flagged = apply_output(eff, doc, text)
                    fu = followup_pack(doc, new_doc, case["instruction"], flagged, packed.context_ids, skeleton)
                    if strategy == "SF" and fu is not None and not args.dry_run:
                        req2 = build_request("S", fu, [], args.model, args.effort, args.ttl, args.salt)
                        ledger.check(
                            cost_usd(Usage(cache_write=est_tokens(fu.volatile), out=2000), args.model, args.ttl)
                        )
                        text2, usage2, _, total2, stop = call_api(client, req2)
                        ledger.record(cost_usd(usage2, args.model, args.ttl), f"{doc_name}/SF-followup/{case['id']}")
                        new_doc, errors2, _ = apply_output("S", new_doc, text2)
                        usage += usage2
                        total += total2
                        errors += errors2
                        text += "\n--- follow-up ---\n" + text2
                        followups += 1
                s = score(doc, new_doc, case["gold"])
                rows.append(
                    {
                        "doc": doc_name,
                        "strategy": strategy
                        if args.retriever == "regex" or strategy in ("B0", "B1")
                        else f"{strategy}[{args.retriever}]",
                        "case": case["id"],
                        "kind": case["kind"],
                        "est_in": est_in,
                        "in": usage.total_in,
                        "uncached": usage.uncached_in,
                        "read": usage.cache_read,
                        "write": usage.cache_write,
                        "out": usage.out,
                        "cost": cost_usd(usage, args.model, args.ttl),
                        "ttft": ttft,
                        "latency": total,
                        "harness_s": harness_s,
                        # end-to-end = harness preparation + API time (rubric R3); local ops have no API call
                        "e2e": total if stop == "local" else harness_s + total,
                        "stop": stop,
                        "errors": errors,
                        "flagged": flagged,
                        "followups": followups,
                        "changed_ids": sorted(diff_ids(doc.snapshot(), new_doc.snapshot()))[:50],
                        "response": text if strategy != "B0" else text[:500],
                        **s,
                        **(opened if ci == 0 else {}),  # document-open work, reported once per session
                    }
                )
                print(
                    f"{doc_name:<11} {strategy:<3} {case['id'].split('-', 2)[-1]:<12} in={usage.total_in:>7} "
                    f"out={usage.out:>6} ${rows[-1]['cost']:.4f} recall={s['must_recall']:.0%} "
                    f"checks={s['checks_passed']}/{s['checks_total']} collateral={s['collateral']} err={len(errors)}"
                )
                if strategy == "B1":
                    history = [*strip_cache_markers(req["messages"]), {"role": "assistant", "content": text}]
                doc = new_doc
                if gaps and not args.dry_run and ci < len(cases) - 1:
                    time.sleep(60 * gaps[ci % len(gaps)])


if __name__ == "__main__":
    main()
