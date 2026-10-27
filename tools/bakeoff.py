"""Offline retriever bake-off (spec 008): context recall / precision / size per variant and split.

Usage:
  python -m tools.bakeoff --split dev --tune     # grid-search matcher cut-offs on the dev set only
  python -m tools.bakeoff --split dev            # score variants with frozen PARAMS
  python -m tools.bakeoff --split fresh          # held-out: run once, after PARAMS are frozen
"""

import argparse
import itertools
import json
from collections import defaultdict

import run_offline as sim
from evalset.build import OUT as CORPUS
from evalset.build import build
from retrieval import PARAMS, UNTUNED, VARIANTS, make_graph
from sdom.dom import Document


def load_split(split: str) -> list[tuple[str, Document, list[dict]]]:
    manifest = build()
    out = []
    for m in manifest:
        name = m["doc"]
        in_split = name.startswith(f"{split}-") if split != "dev" else not name.startswith("fresh")
        if in_split:
            doc = Document.parse((CORPUS / f"{name}.md").read_text(encoding="utf-8"), m["type"])
            out.append((name, doc, json.loads((CORPUS / f"{name}.cases.json").read_text(encoding="utf-8"))))
    return out


def score(docs, variant: str, params) -> dict:  # type: ignore[no-untyped-def]
    rows = []
    for name, doc, cases in docs:
        graph = make_graph(doc, variant, params)
        for r in sim.context_quality(doc, graph, cases, "S"):
            rows.append({"doc": name, **r})
    by_kind = defaultdict(list)
    for r in rows:
        by_kind[r["kind"]].append(r["recall"])
    return {
        "recall": sum(r["recall"] for r in rows) / len(rows),
        "precision": sum(r["precision"] for r in rows) / len(rows),
        "ctx_tokens": sum(r["ctx_tokens"] for r in rows) / len(rows),
        "full_recall_cases": sum(r["recall"] == 1 for r in rows),
        "n": len(rows),
        "by_kind": {k: sum(v) / len(v) for k, v in sorted(by_kind.items())},
        "misses": [(r["doc"], r["case"], r["missed"]) for r in rows if r["recall"] < 1],
    }


def tune(docs, only=None) -> dict:  # type: ignore[no-untyped-def]
    """Pick each matcher's cut-offs by dev recall (pure variant), ties broken by smaller contexts."""
    grids = {
        "bm25": [{"top_k": k, "min_ratio": r} for k, r in itertools.product([5, 8, 12], [0.25, 0.35, 0.5])],
        "emb": [{"top_k": k, "min_sim": s} for k, s in itertools.product([5, 8, 12], [0.45, 0.55, 0.65])],
        "emb-bge": [{"top_k": k, "min_sim": s} for k, s in itertools.product([5, 8, 12], [0.6, 0.7, 0.8])],
    }
    best = {}
    if only:
        grids = {k: v for k, v in grids.items() if k in only}
    for kind, variant in (("bm25", "bm25"), ("emb", "emb"), ("emb-bge", "emb-bge")):
        if kind not in grids:
            continue
        results = []
        for p in grids[kind]:
            res = score(docs, variant, {kind: p})
            results.append((res["recall"], -res["ctx_tokens"], p, res))
            print(
                f"  {kind} {p}: recall {res['recall']:.3f} precision {res['precision']:.3f} ctx {res['ctx_tokens']:.0f}"
            )
        results.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best[kind] = results[0][2]
        print(f"best {kind}: {best[kind]}")
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "fresh", "fresh2"], default="dev")
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--arm", choices=["tuned", "untuned"], default="tuned")
    ap.add_argument("--only", default="", help="comma list of matcher kinds to tune, e.g. emb-bge")
    args = ap.parse_args()
    if args.tune and args.split != "dev":
        raise SystemExit("tuning on the fresh held-out split is not allowed")
    docs = load_split(args.split)
    only = set(args.only.split(",")) - {""} or None
    params = {**PARAMS, **tune(docs, only)} if args.tune else PARAMS
    if args.arm == "untuned":
        if args.tune:
            raise SystemExit("the untuned arm is never tuned")
        params = UNTUNED
    print(f"\n## {args.split} split, params {params}\n")
    print(
        "| variant | recall | cases at 100% | precision | mean ctx tokens | "
        + " | ".join(sorted({k for _, _, cs in docs for k in (c["kind"] for c in cs)}))
        + " |"
    )
    report = {}
    for variant in VARIANTS:
        res = score(docs, variant, params)
        report[variant] = res
        kinds = " | ".join(f"{v:.0%}" for v in res["by_kind"].values())
        print(
            f"| {variant} | {res['recall']:.1%} | {res['full_recall_cases']}/{res['n']} | {res['precision']:.1%} | "
            f"{res['ctx_tokens']:.0f} | {kinds} |"
        )
    for variant, res in report.items():
        for _doc, case, missed in res["misses"]:
            print(f"  miss [{variant}] {case}: {missed}")
    out = CORPUS.parent.parent / "results" / f"bakeoff-{args.split}-{args.arm}.json"
    out.write_text(json.dumps({"params": params, "report": report}, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
