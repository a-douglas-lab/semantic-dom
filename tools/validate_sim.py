"""Compare offline simulator predictions with measured live sessions (back-to-back calls).

Usage: python -m tools.validate_sim results/live-A.json [results/live-B.json ...]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import run_offline as sim
from evalset.build import OUT as CORPUS
from sdom.dom import Document
from sdom.graph import SemanticGraph

BACK_TO_BACK_MIN = [0.1]  # live calls run seconds apart: always a warm cache


def main(paths: list[str]) -> None:
    live: dict[tuple[str, str], float] = defaultdict(float)
    for p in paths:
        for r in json.loads(Path(p).read_text(encoding="utf-8"))["rows"]:
            live[(r["doc"], r["strategy"])] += r["cost"]
    manifest = {m["doc"]: m for m in json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))}
    print("| doc | strategy | live $ | simulated $ | sim/live |")
    print("|---|---|---:|---:|---:|")
    ratios = []
    for (doc_name, strategy), cost in sorted(live.items()):
        m = manifest[doc_name]
        doc = Document.parse((CORPUS / f"{doc_name}.md").read_text(encoding="utf-8"), m["type"])
        cases = json.loads((CORPUS / f"{doc_name}.cases.json").read_text(encoding="utf-8"))
        pred = sim.simulate(doc, SemanticGraph(doc), cases, strategy, "5m", BACK_TO_BACK_MIN, passes=1)["cost"]
        ratios.append(pred / cost)
        print(f"| {doc_name} | {strategy} | {cost:.4f} | {pred:.4f} | {pred / cost:.2f} |")
    ratios.sort()
    print(f"\nsim/live ratio: median {ratios[len(ratios) // 2]:.2f}, range {ratios[0]:.2f}-{ratios[-1]:.2f}")


if __name__ == "__main__":
    main(sys.argv[1:])
