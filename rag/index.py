"""Stages 4–6 — embedding, vector store, re-chunk.

Embedding: config.EMBED_MODEL (default BAAI/bge-m3) dense vectors, L2-normalized; the store uses cosine distance, so
metric matches normalization. Vector store: Chroma, local and persistent (artifacts/chroma/, git-ignored, rebuilt from
the chunk files), one collection per embedding model. Every strategy shares the collection; `strategy`, `doc_id` and
`page_type` are metadata, so filtering and delete-by-strategy are one call.

Usage:
  uv run python -m rag.index build  --strategy B      # embed chunks_B.jsonl and upsert (IDs are deterministic)
  uv run python -m rag.index rechunk --old A --new B   # index B, delete every A chunk, prove no orphans remain
  uv run python -m rag.index delete --strategy A       # delete path
  uv run python -m rag.index status
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from rag import chunking, config
from rag.contract import Chunk, load_chunks

# CHROMA_DIR can point at a copy so the re-chunk demo doesn't delete the evaluated index
CHROMA_DIR = config.CHROMA_DIR
MANIFEST = config.ARTIFACTS / "index_manifest.json"


def device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def embedder():
    import torch
    from sentence_transformers import SentenceTransformer
    kw = {"torch_dtype": torch.float16} if device() == "cuda" else {}
    model = SentenceTransformer(config.EMBED_MODEL, device=device(), model_kwargs=kw)
    model.max_seq_length = min(1024, model.max_seq_length)  # chunks are <= 513 tokens; never exceed the model's limit
    return model


def model_revision() -> str:
    """HF commit hash of the downloaded embedding model, recorded so results are reproducible."""
    try:
        from huggingface_hub import model_info
        return model_info(config.EMBED_MODEL).sha or "unknown"
    except Exception:
        return "unknown (offline)"


def embed(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    vecs = embedder().encode(texts, batch_size=batch_size, normalize_embeddings=True,
                             convert_to_numpy=True, show_progress_bar=len(texts) > 200)
    return vecs.astype("float32").tolist()


@lru_cache(maxsize=1)
def client():
    import chromadb
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def collection():
    return client().get_or_create_collection(
        config.COLLECTION, configuration={"hnsw": {"space": "cosine"}}, embedding_function=None,
        metadata={"embed_model": config.EMBED_MODEL, "normalized": True, "metric": "cosine"},
    )


def _meta(c: Chunk) -> dict:
    return {"doc_id": c.doc_id, "strategy": c.strategy, "page_type": c.page_type, "title": c.title,
            "url": c.url, "heading_path": " > ".join(c.heading_path), "crawled_at": c.crawled_at,
            "effective_date": c.effective_date}


def chunk_from_record(cid: str, text: str, m: dict) -> Chunk:
    return Chunk(chunk_id=cid, url=m["url"], title=m["title"],
                 heading_path=[p for p in m["heading_path"].split(" > ") if p], page_type=m["page_type"],
                 text=text, crawled_at=m["crawled_at"], doc_id=m["doc_id"], strategy=m["strategy"],
                 effective_date=m.get("effective_date", ""))


def index_chunks(chunks: list[Chunk], batch: int = 256) -> float:
    col, t0 = collection(), time.perf_counter()
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        col.upsert(ids=[c.chunk_id for c in part], embeddings=embed([c.text for c in part]),
                   documents=[c.text for c in part], metadatas=[_meta(c) for c in part])
    return time.perf_counter() - t0


def count(where: dict | None = None) -> int:
    col = collection()
    if not where:
        return col.count()
    return len(col.get(where=where, include=[])["ids"])


def delete_strategy(strategy: str) -> int:
    n = count({"strategy": strategy})
    collection().delete(where={"strategy": strategy})
    return n


def stored_ids(strategy: str) -> set[str]:
    return set(collection().get(where={"strategy": strategy}, include=[])["ids"])


def remove_stale(strategy: str, keep: set[str]) -> int:
    """Delete stored chunks of `strategy` that are not in `keep` (e.g. a page that now yields fewer chunks)."""
    stale = list(stored_ids(strategy) - keep)
    if stale:
        collection().delete(ids=stale)
    return len(stale)


def check_in_sync(strategy: str) -> None:
    """BM25 reads the chunk file and dense search reads Chroma; hybrid fusion is wrong if they disagree."""
    file_ids = {c.chunk_id for c in load_strategy(strategy)}
    if file_ids != stored_ids(strategy):
        raise SystemExit(f"Chunk file and vector store disagree for strategy {strategy}: "
                         f"run `uv run python -m rag.index build --strategy {strategy}`")


def delete_doc(doc_id: str) -> int:
    n = count({"doc_id": doc_id})
    collection().delete(where={"doc_id": doc_id})
    return n


def orphan_report(expected: dict[str, set[str]]) -> dict:
    """Compare the store against the current chunk files.

    orphans = stored IDs that are not in the current chunk set of their strategy, or whose doc_id is not in docs.jsonl.
    """
    doc_ids = {d["doc_id"] for d in chunking.load_docs()}
    got = collection().get(include=["metadatas"])
    stale_doc, stale_id, by_strategy = [], [], {}
    for cid, m in zip(got["ids"], got["metadatas"]):
        by_strategy[m["strategy"]] = by_strategy.get(m["strategy"], 0) + 1
        if m["doc_id"] not in doc_ids:
            stale_doc.append(cid)
        if cid not in expected.get(m["strategy"], set()):
            stale_id.append(cid)
    return {"total": len(got["ids"]), "by_strategy": by_strategy,
            "orphan_doc_ids": len(stale_doc), "orphan_chunk_ids": len(stale_id), "examples": (stale_doc + stale_id)[:5]}


def write_manifest(extra: dict) -> None:
    m = json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else {}
    m.update({"embed_model": config.EMBED_MODEL, "embed_model_revision": model_revision(),
              "dim": len(embed(["dimension probe"])[0]),
              "normalization": "L2 (unit length)", "metric": "cosine", "vector_store": "chromadb (persistent, local)",
              "collection": config.COLLECTION, "device": device(), "updated_at": datetime.now(timezone.utc).isoformat()})
    m.update(extra)
    MANIFEST.write_text(json.dumps(m, indent=2), "utf-8")


def load_strategy(strategy: str) -> list[Chunk]:
    path = chunking.out_path(strategy)
    if not path.exists():
        raise SystemExit(f"{path} missing: run `uv run python -m rag.chunking --strategy {strategy}` first")
    return load_chunks(path)


def cmd_build(strategy: str) -> dict:
    """Upsert the strategy's chunk file and delete its stored chunks that the file no longer contains."""
    chunks = load_strategy(strategy)
    ids = {c.chunk_id for c in chunks}
    secs = index_chunks(chunks)
    removed = remove_stale(strategy, ids)
    rep = orphan_report({strategy: ids})
    stored = count({"strategy": strategy})
    if stored != len(chunks) or rep["orphan_doc_ids"]:
        raise SystemExit(f"index out of sync after build: stored {stored} vs {len(chunks)} chunks; {rep}")
    write_manifest({f"strategy_{strategy}": {"chunks": len(chunks), "stale_removed": removed, "embed_seconds": round(secs, 1)}})
    print(f"indexed strategy {strategy}: {len(chunks)} chunks ({removed} stale removed) in {secs:.1f}s on {device()} -> {CHROMA_DIR}")
    return {"chunks": len(chunks), "stale_removed": removed}


def cmd_rechunk(old: str, new: str) -> dict:
    """Re-chunk without re-crawling: chunks come from saved docs.jsonl; stale strategy deleted; orphans proven absent."""
    if old == new:
        raise SystemExit("old and new strategy are the same: to re-index one strategy, use `build`")
    before = count({"strategy": old})
    new_chunks = chunking.build(new)                 # reads saved normalized docs only — no network
    chunking.write(new_chunks, chunking.out_path(new))
    new_ids = {c.chunk_id for c in new_chunks}
    secs = index_chunks(new_chunks)
    remove_stale(new, new_ids)
    deleted = delete_strategy(old)
    after_old = count({"strategy": old})
    rep = orphan_report({new: new_ids})
    result = {"old": old, "new": new, "old_chunks_before": before, "deleted": deleted, "old_chunks_after": after_old,
              "new_chunks": len(new_chunks), "new_indexed": count({"strategy": new}), "embed_seconds": round(secs, 1),
              **rep}
    problems = [msg for bad, msg in [
        (after_old != 0, f"{after_old} '{old}' chunks still present"),
        (result["new_indexed"] != len(new_chunks), f"indexed {result['new_indexed']} of {len(new_chunks)} new chunks"),
        (rep["orphan_doc_ids"] or rep["orphan_chunk_ids"], f"orphans remain: {rep}"),
    ] if bad]
    if problems:
        raise SystemExit("; ".join(problems))
    write_manifest({"last_rechunk": result})
    print(json.dumps(result, indent=2))
    return result


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--strategy", choices=["A", "B"], required=True)
    r = sub.add_parser("rechunk"); r.add_argument("--old", default="A"); r.add_argument("--new", default="B")
    d = sub.add_parser("delete").add_mutually_exclusive_group(required=True)
    d.add_argument("--strategy"); d.add_argument("--doc-id")
    sub.add_parser("status")
    a = ap.parse_args()
    if a.cmd == "build":
        cmd_build(a.strategy)
    elif a.cmd == "rechunk":
        cmd_rechunk(a.old, a.new)
    elif a.cmd == "delete":
        n = delete_strategy(a.strategy) if a.strategy else delete_doc(a.doc_id)
        print(f"deleted {n} chunks")
    else:
        expected = {s: {c.chunk_id for c in load_strategy(s)} for s in ("A", "B") if chunking.out_path(s).exists()}
        print(json.dumps(orphan_report(expected), indent=2))


if __name__ == "__main__":
    main()
