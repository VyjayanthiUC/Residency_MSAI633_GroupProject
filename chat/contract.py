"""Interface contract between the chat UI and the retrieval layer.

Any real retriever that implements the Retriever protocol and returns Chunk lists plugs into the UI without UI changes.
chunks.jsonl holds one Chunk per line (without score fields) and is the only corpus format the UI reads.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol


@dataclass
class Chunk:
    chunk_id: str                 # deterministic ID, e.g. "Lauma#Talents#0"
    url: str                      # citation URL with #section anchor
    title: str                    # page title
    heading_path: list[str] = field(default_factory=list)  # ["Talents", "Elemental Skill"]
    page_type: str = ""           # page_type from the page selection
    text: str = ""
    crawled_at: str = ""          # crawl timestamp; shown in the UI to signal content age
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
