"""STUB retriever: BM25 recall, then take the top k_final as the "post-rerank" result.

It only gives the chat UI something to display; it is not the real retrieval / rerank design.
score_post is score_pre normalized by the pool maximum, not a real rerank score; the UI labels it as stub.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from contract import Chunk

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?|[一-鿿]")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def load_chunks(path: Path) -> list[Chunk]:
    with open(path, encoding="utf-8") as f:
        return [Chunk(**json.loads(line)) for line in f if line.strip()]


class StubBM25Retriever:
    name = "stub-bm25"

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        # Title and section path are indexed too: users often ask by page name
        self.bm25 = BM25Okapi([tokenize(" ".join([c.title, *c.heading_path, c.text])) for c in chunks])

    def retrieve(self, query: str, k_pool: int = 20, k_final: int = 5) -> tuple[list[Chunk], list[Chunk]]:
        scores = self.bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k_pool]
        pool = []
        for i in order:
            if scores[i] <= 0:
                break
            c = copy.copy(self.chunks[i])
            c.score_pre = float(scores[i])
            pool.append(c)
        top = pool[0].score_pre if pool else 1.0
        for c in pool:
            c.score_post = c.score_pre / top
        return pool, pool[:k_final]
