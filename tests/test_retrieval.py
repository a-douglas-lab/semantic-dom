"""Retriever bake-off plumbing (spec 008): matchers plug into SemanticGraph via a Protocol."""

import pytest

from retrieval import VARIANTS, make_graph
from retrieval.bm25 import BM25Matcher, tokenize
from sdom.dom import Document
from sdom.graph import SemanticGraph

DOC = """# Decisions

## ADR010: Use the Luxon Date Library

We will use Luxon as the standard date library.

- All plugins should use Luxon for date manipulation.

## ADR012: Use presets

Use Luxon presets with toLocaleString for dates.

## ADR020: Catalog file

The catalog file should be named catalog-info.yaml by default.

## ADR021: Unrelated

Teams deploy services with Helm charts.
"""


@pytest.fixture
def doc() -> Document:
    return Document.parse(DOC, "adr")


def test_tokenize_keeps_file_names_and_drops_stopwords():
    toks = tokenize("The file should be named catalog-info.yaml, not 3× bigger")
    assert "catalog-info.yaml" in toks and "the" not in toks and "3" in toks


def test_bm25_locates_and_relates(doc):
    m = BM25Matcher(doc)
    assert m.locate("rename catalog-info.yaml to backstage.yaml") == ["s3.i1"]
    related = dict(m.related("replace Luxon with date-fns"))
    assert {"s1.i1", "s1.i2", "s2.i1"} <= set(related) and "s4.i1" not in related


def test_graph_without_facts_uses_matcher(doc):
    g = SemanticGraph(doc, use_facts=False, matchers=[BM25Matcher(doc)])
    imp = g.impact("We are replacing Luxon with date-fns.")
    assert imp.targets and "s1.i1" in imp.all  # no facts, no quotes: targets can only come from BM25
    imp = g.impact("Teams deploy with Helm charts", targets=["s3.i1"])
    assert any(r.startswith("bm25:") for rs in imp.reasons.values() for r in rs)  # related nodes are tagged


def test_variants_build(doc):
    assert set(VARIANTS) == {"regex", "bm25", "regex+bm25", "emb", "all", "emb-bge", "all-bge"}
    g = make_graph(doc, "regex")
    assert g.use_facts and not g.matchers
    g = make_graph(doc, "regex+bm25")
    assert g.use_facts and [m.name for m in g.matchers] == ["bm25"]


@pytest.mark.slow
def test_embedding_matcher_relates_paraphrase(doc):
    from retrieval.embed import EmbeddingMatcher

    m = EmbeddingMatcher(doc)
    top = [nid for nid, _ in m.related("switch the standard date library")]
    assert top and top[0] in {"s1", "s1.i1", "s1.i2", "s2", "s2.i1"}


class _FakeBge:
    """Records each call's texts; returns a vector per text that identifies it."""

    def __init__(self):
        self.calls: list[tuple[list[str], int]] = []

    def embed(self, texts, batch_size=256):
        self.calls.append((list(texts), batch_size))
        return [[float(len(t)), float(ord(t[0]))] for t in texts]


def test_bge_embeds_in_length_sorted_batches_and_keeps_input_order(monkeypatch):
    from retrieval import embed

    fake = _FakeBge()
    monkeypatch.setitem(embed._CACHE, "bge", fake)
    texts = ["a" * 300, "b", "c" * 40, "d" * 5]
    vecs = embed._encode_raw("bge", texts)
    (sent, batch_size), *_ = fake.calls
    assert [len(t) for t in sent] == sorted(len(t) for t in texts)  # similar lengths share a batch: less padding
    assert batch_size == embed.BGE_BATCH
    assert [v[0] for v in vecs] == [len(t) for t in texts]  # results come back in the caller's order


def test_untuned_percentile_threshold(doc):
    from retrieval.embed import EmbeddingMatcher

    m = EmbeddingMatcher(doc, backend="potion", top_k=8, min_sim_pct=90)
    related = m.related("standard date library")
    assert 1 <= len(related) <= 2  # 90th percentile of ~11 node similarities keeps the top one or two
