"""Stages 7–8: BM25 / dense / hybrid (RRF) retrieval and cross-encoder reranking.

Pipeline implements contract.Retriever, so the chat UI and the evaluation harness run the same code:
pool = top k_pool by the retriever's own score (score_pre); final = top k_final by reranker score (score_post,
sigmoid 0–1), or pool[:k_final] when reranking is off.
"""
from __future__ import annotations

import copy
import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from rag import config, index
from rag.contract import Chunk

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?|[一-鿿]")

Ranked = list[tuple[Chunk, float]]


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class BM25:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        # title and heading path are indexed too: users ask by page name
        self.bm25 = BM25Okapi([tokenize(" ".join([c.title, *c.heading_path, c.text])) for c in chunks])

    def search(self, query: str, k: int, page_types: list[str] | None = None) -> Ranked:
        scores = self.bm25.get_scores(tokenize(query))
        out = []
        for i in sorted(range(len(scores)), key=scores.__getitem__, reverse=True):
            if scores[i] <= 0 or len(out) == k:
                break
            if not page_types or self.chunks[i].page_type in page_types:
                out.append((self.chunks[i], float(scores[i])))
        return out


@lru_cache(maxsize=2)
def bm25_for(strategy: str) -> BM25:
    return BM25(index.load_strategy(strategy))


def dense_search(strategy: str, query: str, k: int, page_types: list[str] | None = None) -> Ranked:
    where = {"strategy": strategy}
    if page_types:
        where = {"$and": [where, {"page_type": {"$in": page_types}}]}
    res = index.collection().query(query_embeddings=index.embed([query]), n_results=k, where=where,
                                   include=["documents", "metadatas", "distances"])
    return [(index.chunk_from_record(cid, doc, meta), 1.0 - dist)
            for cid, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0])]


def rrf(*rankings: Ranked, k: int = config.RRF_K) -> Ranked:
    """Reciprocal Rank Fusion (Cormack et al., 2009): score = Σ 1 / (k + rank)."""
    scores: dict[str, float] = {}
    by_id: dict[str, Chunk] = {}
    for ranking in rankings:
        for rank, (c, _) in enumerate(ranking, 1):
            scores[c.chunk_id] = scores.get(c.chunk_id, 0.0) + 1.0 / (k + rank)
            by_id.setdefault(c.chunk_id, c)
    return sorted(((by_id[i], s) for i, s in scores.items()), key=lambda x: x[1], reverse=True)


@lru_cache(maxsize=1)
def reranker():
    import torch
    from sentence_transformers import CrossEncoder
    kw = {"torch_dtype": torch.float16} if index.device() == "cuda" else {}
    return CrossEncoder(config.RERANK_MODEL, device=index.device(), max_length=1024, model_kwargs=kw)


def rerank_scores(query: str, chunks: list[Chunk]) -> list[float]:
    import torch
    pairs = [(query, " > ".join([c.title, *c.heading_path]) + "\n" + c.text) for c in chunks]
    return [float(s) for s in reranker().predict(pairs, batch_size=8, activation_fn=torch.nn.Sigmoid())]


class Pipeline:
    def __init__(self, strategy: str = "B", mode: str = "hybrid", rerank: bool = True,
                 page_types: list[str] | None = None):
        if mode not in ("bm25", "dense", "hybrid"):
            raise ValueError(f"unknown retriever mode {mode!r}")
        self.strategy, self.mode, self.rerank, self.page_types = strategy, mode, rerank, page_types
        self.name = f"{mode}{'+rerank' if rerank else ''} / chunks {strategy}"
        self.score_label = {"bm25": "BM25", "dense": "cosine", "hybrid": "RRF"}[mode]

    def candidates(self, query: str, k: int) -> Ranked:
        if self.mode == "bm25":
            return bm25_for(self.strategy).search(query, k, self.page_types)
        if self.mode == "dense":
            return dense_search(self.strategy, query, k, self.page_types)
        depth = max(config.FUSION_DEPTH, k)
        return rrf(bm25_for(self.strategy).search(query, depth, self.page_types),
                   dense_search(self.strategy, query, depth, self.page_types))[:k]

    def retrieve(self, query: str, k_pool: int = config.K_POOL, k_final: int = config.K_FINAL) -> tuple[list[Chunk], list[Chunk]]:
        pool = []
        for c, s in self.candidates(query, k_pool):
            c = copy.copy(c)  # cached BM25 chunks are shared; scores are per query
            c.score_pre = c.score_post = s
            pool.append(c)
        if self.rerank and pool:
            for c, s in zip(pool, rerank_scores(query, pool)):
                c.score_post = s
            return pool, sorted(pool, key=lambda c: c.score_post, reverse=True)[:k_final]
        return pool, pool[:k_final]


def from_config() -> Pipeline:
    return Pipeline(strategy=config.CHUNK_STRATEGY, mode=config.RETRIEVER, rerank=config.RERANK)
