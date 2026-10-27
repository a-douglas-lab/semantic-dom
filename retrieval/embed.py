"""Embedding matchers over document nodes (cosine similarity).

Backends:
- "potion": model2vec static embeddings, minishlab/potion-base-8M (numpy only; ~30 MB)
- "bge":    fastembed ONNX transformer, BAAI/bge-small-en-v1.5 (~130 MB)
"""

from __future__ import annotations

import numpy as np

from sdom.dom import Document

MODELS = {"potion": "minishlab/potion-base-8M", "bge": "BAAI/bge-small-en-v1.5"}
# bge pads each batch to its longest text; sorting by length and keeping batches small avoids paying for padding
BGE_BATCH = 16
_CACHE: dict[str, object] = {}


_VECS: dict[tuple[str, str], np.ndarray] = {}


def encode(backend: str, texts: list[str]) -> np.ndarray:
    """Encode with per-process caches: one model per backend, one vector per (backend, text)."""
    missing = list(dict.fromkeys(t for t in texts if (backend, t) not in _VECS))
    if missing:
        for t, v in zip(missing, _encode_raw(backend, missing), strict=True):
            _VECS[(backend, t)] = v
    return np.stack([_VECS[(backend, t)] for t in texts])


def _encode_raw(backend: str, texts: list[str]) -> np.ndarray:
    """Cold model load: potion ~18 s, bge ~5 s once downloaded."""
    if backend not in _CACHE:
        if backend == "potion":
            from model2vec import StaticModel

            _CACHE[backend] = StaticModel.from_pretrained(MODELS[backend])
        else:
            from fastembed import TextEmbedding

            _CACHE[backend] = TextEmbedding(MODELS[backend])
    model = _CACHE[backend]
    if backend == "potion":
        return np.asarray(model.encode(texts))  # type: ignore[attr-defined]
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    vecs = list(model.embed([texts[i] for i in order], batch_size=BGE_BATCH))  # type: ignore[attr-defined]
    out: list[np.ndarray] = [np.empty(0)] * len(texts)
    for i, v in zip(order, vecs, strict=True):
        out[i] = np.asarray(v)
    return np.stack(out)


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.clip(np.linalg.norm(v, axis=-1, keepdims=True), 1e-9, None)


class EmbeddingMatcher:
    """Locate: nodes within `locate_margin` of the best cosine (max `locate_k`).
    Related: top `top_k` nodes with cosine >= `min_sim`."""

    def __init__(
        self,
        doc: Document,
        backend: str = "potion",
        top_k: int = 8,
        min_sim: float = 0.55,
        locate_margin: float = 0.03,
        locate_k: int = 3,
        min_sim_pct: float | None = None,
    ):
        """`min_sim_pct` (untuned arm): per-query threshold at that percentile of the query's own
        similarities across the document, instead of a fixed `min_sim`."""
        self.min_sim_pct = min_sim_pct
        self.name = "emb" if backend == "potion" else f"emb-{backend}"
        self.backend = backend
        self.ids = [n.id for n in doc.nodes.values() if n.kind != "doc"]
        self.vecs = _unit(encode(backend, [doc.nodes[i].text for i in self.ids]))
        self.top_k, self.min_sim = top_k, min_sim
        self.locate_margin, self.locate_k = locate_margin, locate_k

    def _sims(self, query: str) -> list[tuple[str, float]]:
        q = _unit(encode(self.backend, [query]))[0]
        sims = self.vecs @ q
        order = np.argsort(-sims)
        return [(self.ids[k], float(sims[k])) for k in order]

    def locate(self, query: str) -> list[str]:
        ranked = self._sims(query)
        best = ranked[0][1]
        return [i for i, s in ranked[: self.locate_k] if s >= best - self.locate_margin]

    def related(self, query: str) -> list[tuple[str, float]]:
        ranked = self._sims(query)
        if self.min_sim_pct is not None:
            threshold = float(np.percentile([s for _, s in ranked], self.min_sim_pct))
        else:
            threshold = self.min_sim
        return [(i, s) for i, s in ranked[: self.top_k] if s >= threshold]
