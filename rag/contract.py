"""Interface contract between the chat UI and the retrieval layer.

Any retriever that implements the Retriever protocol plugs into the UI without UI changes.
Chunk files (data/chunks_A.jsonl, data/chunks_B.jsonl) hold one Chunk per line, without score fields.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class Chunk:
    chunk_id: str                 # deterministic ID: "{doc_id}#{strategy}#{seq:04d}", e.g. "gi-lauma-1a2b3c4d#B#0007"
    url: str                      # citation URL with #section anchor
    title: str                    # page title
    heading_path: list[str] = field(default_factory=list)  # ["Talents", "Elemental Skill"]
    page_type: str = ""           # page_type from the page selection
    text: str = ""
    crawled_at: str = ""          # crawl timestamp; shown in the UI to signal content age
    doc_id: str = ""              # docs.jsonl doc_id this chunk came from (orphan check)
    strategy: str = ""            # "A" fixed-size | "B" structure-aware
    effective_date: str = ""      # game-version date the content applies to ("" = undated, e.g. mechanics pages)
    score_pre: float | None = None   # retrieval score (pre-rerank)
    score_post: float | None = None  # post-rerank score

    def to_json(self) -> dict:
        d = asdict(self)
        d.pop("score_pre"); d.pop("score_post")
        return d


class Retriever(Protocol):
    name: str

    def retrieve(self, query: str, k_pool: int = 20, k_final: int = 5) -> tuple[list[Chunk], list[Chunk]]:
        """Return (candidate pool, final results): pool sorted by score_pre desc, final by score_post desc."""
        ...


def load_chunks(path: Path) -> list[Chunk]:
    with open(path, encoding="utf-8") as f:
        return [Chunk(**json.loads(line)) for line in f if line.strip()]
