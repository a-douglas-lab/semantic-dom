"""Variance across repeated live runs (rubric R6): per strategy, mean ± sd of session cost and fact checks,
and per-case pass rates across runs.

Usage: python -m tools.variance results/live-A.json results/live-B.json ...
Rows are grouped by (strategy label, doc); each file is one run.
"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def main(paths: list[str]) -> None:
    runs: dict[str, list[dict]] = defaultdict(list)  # strategy -> list of {cost, passed, total, cases}
    case_pass: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for p in paths:
        rows = json.loads(Path(p).read_text(encoding="utf-8"))["rows"]
        by_strategy: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            by_strategy[r["strategy"]].append(r)
        for strat, rs in by_strategy.items():
            runs[strat].append(
                {
                    "cost": sum(r["cost"] for r in rs),
                    "passed": sum(r["checks_passed"] for r in rs),
                    "total": sum(r["checks_total"] for r in rs),
                }
            )
            for r in rs:
                ok = r["checks_passed"] == r["checks_total"] and r["must_recall"] == 1.0
                case_pass[(strat, r["case"])].append(ok)

    def ms(xs: list[float]) -> str:
        return f"{statistics.mean(xs):.4f} ± {statistics.stdev(xs):.4f}" if len(xs) > 1 else f"{xs[0]:.4f}"

    print("| strategy | runs | session cost (mean ± sd) | checks passed per run | mean checks % |")
    print("|---|---:|---:|---|---:|")
    for strat, rs in sorted(runs.items()):
        checks = ", ".join(f"{r['passed']}/{r['total']}" for r in rs)
        pct = statistics.mean(r["passed"] / r["total"] for r in rs)
        print(f"| {strat} | {len(rs)} | {ms([r['cost'] for r in rs])} | {checks} | {pct:.1%} |")
    print("\nCases not passing in every run:")
    for (strat, case), oks in sorted(case_pass.items()):
        if not all(oks):
            print(f"  {strat:<16} {case:<42} passed {sum(oks)}/{len(oks)}")


if __name__ == "__main__":
    main(sys.argv[1:])
