"""BM25 matcher over document nodes (rank_bm25.BM25Okapi)."""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from sdom.dom import Document

TOKEN = re.compile(r"[a-z0-9]+(?:[.\-/_][a-z0-9]+)*|[£$€×%]")
STOP = set(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "can",
        "do",
        "for",
        "from",
        "has",
        "have",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "may",
        "must",
        "not",
        "of",
        "on",
        "or",
        "our",
        "should",
        "so",
        "than",
        "that",
        "the",
        "their",
        "then",
        "there",
        "these",
        "they",
        "this",
        "to",
        "was",
        "we",
        "were",
        "will",
        "with",
        "would",
        "you",
        "your",
        "all",
        "any",
        "each",
        "other",
        "such",
        "also",
        "only",
    ]
)


def tokenize(text: str) -> list[str]:
    """Lower-case word/number tokens; keeps file and package names (catalog-info.yaml) whole."""
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


class BM25Matcher:
    """Locate: nodes scoring >= `locate_ratio` x best (max `locate_k`).
    Related: top `top_k` nodes scoring >= `min_ratio` x best."""

    name = "bm25"

    def __init__(
        self, doc: Document, top_k: int = 8, min_ratio: float = 0.35, locate_ratio: float = 0.8, locate_k: int = 3
    ):
        self.ids = [n.id for n in doc.nodes.values() if n.kind != "doc"]
        self.bm25 = BM25Okapi([tokenize(doc.nodes[i].text) or ["∅"] for i in self.ids])
        self.top_k, self.min_ratio = top_k, min_ratio
        self.locate_ratio, self.locate_k = locate_ratio, locate_k

    def _scores(self, query: str) -> list[tuple[str, float]]:
        q = tokenize(query)
        if not q:
            return []
        scores = self.bm25.get_scores(q)
        return sorted(((i, float(s)) for i, s in zip(self.ids, scores, strict=True) if s > 0), key=lambda x: -x[1])

    def locate(self, query: str) -> list[str]:
        ranked = self._scores(query)
        if not ranked:
            return []
        best = ranked[0][1]
        return [i for i, s in ranked[: self.locate_k] if s >= self.locate_ratio * best]

    def related(self, query: str) -> list[tuple[str, float]]:
        ranked = self._scores(query)
        if not ranked:
            return []
        best = ranked[0][1]
        return [(i, s / best) for i, s in ranked[: self.top_k] if s >= self.min_ratio * best]
