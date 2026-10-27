"""Human-paced comparison across repeated live runs (rubrics R1, R3, R6): per arm (strategy + cache TTL),
mean ± sd of session cost, fact checks, API latency and end-to-end latency (harness prep + API).

Usage: python -m tools.paced results/live-A.json results/live-B.json ...
Each file is one session of one arm. Preloaded sessions (V3) are labelled as such, and their
prewarm spend counts towards session cost. Files without an `e2e` field (V1) get e2e = API latency for B0/B1,
whose harness time was an unused graph build, and harness_s + API latency for the other strategies.
"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def e2e(row: dict) -> float:
    if "e2e" in row:
        return float(row["e2e"])
    if row["strategy"] in ("B0", "B1") or row["stop"] == "local":
        return float(row["latency"])
    return float(row["harness_s"] + row["latency"])


def session(rows: list[dict]) -> dict[str, float]:
    ends = [e2e(r) for r in rows]
    return {
        "cost": sum(r["cost"] + r.get("preload_usd", 0.0) for r in rows),  # preload: spend at document open
        "passed": sum(r["checks_passed"] for r in rows),
        "total": sum(r["checks_total"] for r in rows),
        "api": statistics.mean(r["latency"] for r in rows),
        "e2e": statistics.mean(ends),
        "first": ends[0],
        "later": statistics.mean(ends[1:]) if len(ends) > 1 else float("nan"),
    }


def summarise(paths: list[str]) -> dict[str, list[dict[str, float]]]:
    arms: dict[str, list[dict[str, float]]] = defaultdict(list)
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        ttl = data["meta"]["ttl"] + (" preload" if data["meta"].get("preload") else "")
        by_strategy: dict[str, list[dict]] = defaultdict(list)
        for r in data["rows"]:
            by_strategy[r["strategy"]].append(r)
        for strat, rs in by_strategy.items():
            arms[f"{strat} {ttl}"].append(session(rs))
    return dict(arms)


def ms(xs: list[float], fmt: str = ".3f") -> str:
    return f"{statistics.mean(xs):{fmt}} ± {statistics.stdev(xs):{fmt}}" if len(xs) > 1 else f"{xs[0]:{fmt}}"


def render(arms: dict[str, list[dict[str, float]]]) -> str:
    lines = [
        "| arm | runs | session cost $ | checks | API latency s | end-to-end s | first edit e2e s | later edits e2e s |",
        "|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for arm, ss in sorted(arms.items()):
        checks = ", ".join(f"{int(s['passed'])}/{int(s['total'])}" for s in ss)
        lines.append(
            f"| {arm} | {len(ss)} | {ms([s['cost'] for s in ss])} | {checks} | {ms([s['api'] for s in ss], '.1f')} | "
            f"{ms([s['e2e'] for s in ss], '.1f')} | {ms([s['first'] for s in ss], '.1f')} | "
            f"{ms([s['later'] for s in ss], '.1f')} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(summarise(sys.argv[1:])))
