"""Aggregate live result files into results/live.md (rubrics R2/R3 + token calibration).

Usage: python report_live.py results/live-A.json [results/live-B.json ...]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

STRATS = ["B0", "B1", "B2", "S", "SL"]


def load(paths: list[str]) -> tuple[list[dict], list[dict]]:
    rows, metas = [], []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        metas.append({"file": Path(p).name, **data["meta"]})
        rows += data["rows"]
    return rows, metas


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def summarise(rows: list[dict]) -> dict:
    checks_t = sum(r["checks_total"] for r in rows)
    return {
        "n": len(rows),
        "cost": sum(r["cost"] for r in rows),
        "in": sum(r["in"] for r in rows),
        "out": sum(r["out"] for r in rows),
        "latency": mean([r["latency"] for r in rows]),
        "ttft": mean([r["ttft"] for r in rows]),
        "recall": mean([r["must_recall"] for r in rows]),
        "checks": sum(r["checks_passed"] for r in rows) / checks_t if checks_t else float("nan"),
        "collateral": sum(r["collateral"] for r in rows),
        "distractor": sum(r["distractor_changed"] for r in rows),
        "errors": sum(len(r["errors"]) for r in rows),
        "est_ratio": sum(r["in"] for r in rows) / max(1, sum(r["est_in"] for r in rows)),
    }


def render(rows: list[dict], metas: list[dict]) -> str:
    L = [
        "# Live results",
        "",
        "Runs: " + ", ".join(f"{m['file']} ({m['model']}, effort {m['effort']}, git {m['git']})" for m in metas),
        "",
    ]
    by_doc: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_doc[r["doc"]][r["strategy"]].append(r)
    head = "| doc | strategy | calls | cost $ | in tok | out tok | latency s | TTFT s | must recall | checks | collateral | distractors | errors | real/est in |"
    L += ["## Per document and strategy", "", head, "|" + "---|" * 2 + "---:|" * 12]
    for doc in sorted(by_doc):
        for s in STRATS:
            if s not in by_doc[doc]:
                continue
            x = summarise(by_doc[doc][s])
            L.append(
                f"| {doc} | {s} | {x['n']} | {x['cost']:.4f} | {x['in']:,} | {x['out']:,} | {x['latency']:.1f} | {x['ttft']:.1f} | "
                f"{x['recall']:.0%} | {x['checks']:.0%} | {x['collateral']} | {x['distractor']} | {x['errors']} | {x['est_ratio']:.2f} |"
            )
    L += [
        "",
        "## By edit kind (all docs)",
        "",
        "| kind | " + " | ".join(f"{s} recall / checks" for s in STRATS) + " |",
        "|---|" + "---:|" * len(STRATS),
    ]
    kinds: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        kinds[r["kind"]][r["strategy"]].append(r)
    for k in sorted(kinds):
        cells = []
        for s in STRATS:
            if kinds[k][s]:
                x = summarise(kinds[k][s])
                cells.append(f"{x['recall']:.0%} / {x['checks']:.0%}")
            else:
                cells.append("—")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    L += ["", "## Failures (must-change missed or checks failed)", ""]
    for r in rows:
        if r["must_recall"] < 1 or r["checks_passed"] < r["checks_total"] or r["errors"]:
            L.append(
                f"- {r['doc']} {r['strategy']} {r['case'].split('-', 2)[-1]}: recall {r['must_recall']:.0%}, "
                f"checks {r['checks_passed']}/{r['checks_total']}, collateral {r['collateral']}, errors {r['errors'][:2]}"
            )
    return "\n".join(L) + "\n"


def main() -> None:
    paths = sys.argv[1:]
    rows, metas = load(paths)
    out = render(rows, metas)
    Path("results/live.md").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
