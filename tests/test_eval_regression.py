"""Eval regression (rubric R4) and corpus determinism (Principle III)."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import run_offline as sim
from evalset.build import OUT as CORPUS
from sdom.graph import SemanticGraph

FLOOR = json.loads((Path(__file__).parent / "eval_floor.json").read_text(encoding="utf-8"))


def test_context_recall_meets_floor(corpus):
    by_kind: dict[str, list[float]] = defaultdict(list)
    for name, (doc, cases) in corpus.items():
        if name.startswith(("real-", "fresh")):  # held-out sets: reported, never used as a tuning floor
            continue
        for row in sim.context_quality(doc, SemanticGraph(doc), cases, "S"):
            by_kind[row["kind"]].append(row["recall"])
    for kind, recalls in by_kind.items():
        mean = sum(recalls) / len(recalls)
        assert mean >= FLOOR["S_recall_by_kind"][kind], f"{kind}: {mean:.2f} below floor"


def test_corpus_is_deterministic(corpus):
    digest = hashlib.sha256()
    for name in sorted(corpus):
        digest.update((CORPUS / f"{name}.md").read_bytes())
    assert digest.hexdigest()[:16] == FLOOR["corpus_sha256_16"], "corpus changed: regenerate floor deliberately"


def test_gold_local_cases_target_exactly_one_node(corpus):
    for _, cases in corpus.values():
        for c in cases:
            if c["kind"] == "local":
                assert len(c["gold"]["must"]) == 1, c["id"]
