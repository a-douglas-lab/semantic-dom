"""Retriever variants for the spec-008/009 bake-offs. Structural edges, schema rules and quoted-text
location are common to every variant; only the matching method changes."""

from __future__ import annotations

from sdom.dom import Document
from sdom.graph import Matcher, SemanticGraph

VARIANTS = {  # name -> (use regex facts, matcher kinds)
    "regex": (True, ()),
    "bm25": (False, ("bm25",)),
    "regex+bm25": (True, ("bm25",)),
    "emb": (False, ("emb",)),
    "all": (True, ("bm25", "emb")),
    # spec 009: stronger transformer embeddings (BAAI/bge-small-en-v1.5 via fastembed)
    "emb-bge": (False, ("emb-bge",)),
    "all-bge": (True, ("bm25", "emb-bge")),
}

# Frozen after tuning on the dev set only (synthetic + spec-006 real docs).
# bm25 / emb: spec 008. emb-bge: spec 009 (placeholder until tuned).
PARAMS: dict[str, dict[str, float]] = {
    "bm25": {"top_k": 8, "min_ratio": 0.25},
    "emb": {"top_k": 5, "min_sim": 0.45},
    "emb-bge": {"top_k": 8, "min_sim": 0.6},  # spec 009: tuned on dev only; 0.6 is the grid edge
}

# Untuned arm (spec 009), pre-registered before bge tuning: pre-tuning code defaults for BM25 and a
# data-independent per-query percentile threshold for both embedding models. Never adjusted.
UNTUNED: dict[str, dict[str, float]] = {
    "bm25": {"top_k": 8, "min_ratio": 0.35},
    "emb": {"top_k": 8, "min_sim_pct": 90},
    "emb-bge": {"top_k": 8, "min_sim_pct": 90},
}


def make_matchers(
    doc: Document, kinds: tuple[str, ...], params: dict[str, dict[str, float]] | None = None
) -> list[Matcher]:
    params = params or PARAMS
    out: list[Matcher] = []
    for k in kinds:
        if k == "bm25":
            from retrieval.bm25 import BM25Matcher

            out.append(BM25Matcher(doc, **params.get("bm25", {})))  # type: ignore[arg-type]
        elif k in ("emb", "emb-bge"):
            from retrieval.embed import EmbeddingMatcher

            backend = "potion" if k == "emb" else "bge"
            out.append(EmbeddingMatcher(doc, backend=backend, **params.get(k, {})))  # type: ignore[arg-type]
    return out


def make_graph(
    doc: Document, variant: str, params: dict[str, dict[str, float]] | None = None, **kwargs: object
) -> SemanticGraph:
    use_facts, kinds = VARIANTS[variant]
    return SemanticGraph(doc, use_facts=use_facts, matchers=make_matchers(doc, kinds, params), **kwargs)  # type: ignore[arg-type]
