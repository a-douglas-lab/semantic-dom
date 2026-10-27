"""Offline ablation of S: which components earn their keep?

Variants: full S; without outline; without schema / literal / structural edges.
Reports mean context recall by edit kind and calibrated `human`-scenario session cost.
Usage: python -m tools.ablation
"""

import json
from collections import defaultdict

import run_offline as sim
from evalset.build import OUT as CORPUS
from evalset.build import build
from sdom.dom import Document
from sdom.graph import SemanticGraph

ALL = frozenset({"structural", "schema", "literal"})
VARIANTS = {
    "S (full)": (ALL, True),
    "no outline": (ALL, False),
    "no schema edges": (ALL - {"schema"}, True),
    "no literal edges": (ALL - {"literal"}, True),
    "no structural edges": (ALL - {"structural"}, True),
    "targets only": (frozenset(), True),
}


def main() -> None:
    manifest = build()
    recall: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    cost: dict[str, float] = defaultdict(float)
    for m in manifest:
        doc = Document.parse((CORPUS / f"{m['doc']}.md").read_text(encoding="utf-8"), m["type"])
        cases = json.loads((CORPUS / f"{m['doc']}.cases.json").read_text(encoding="utf-8"))
        for name, (edges, outline) in VARIANTS.items():
            graph = SemanticGraph(doc, edges=edges)
            for row in sim.context_quality(doc, graph, cases, "S"):
                recall[name][row["kind"]].append(row["recall"])
            if m["tokens_est"] >= 15000:
                skeleton = None if outline else ""
                cost[name] += sim.simulate(
                    doc, graph, cases, "S", "5m", sim.SCENARIOS["human"], passes=2, skeleton=skeleton
                )["cost"]
    kinds = sorted({k for v in recall.values() for k in v})
    print("| variant | " + " | ".join(kinds) + " | cost, docs ≥15k (human) |")
    print("|---|" + "---:|" * (len(kinds) + 1))
    for name in VARIANTS:
        cells = [f"{sum(recall[name][k]) / len(recall[name][k]):.0%}" for k in kinds]
        print(f"| {name} | " + " | ".join(cells) + f" | ${cost[name]:.3f} |")


if __name__ == "__main__":
    main()
