import hashlib

import pytest

from rag import chunking, index, retrieval
from tests.test_chunking import DOC


def fake_embed(texts, batch_size=16):
    # deterministic 8-d unit vectors: no model download in tests
    out = []
    for t in texts:
        h = hashlib.sha256(t.encode()).digest()[:8]
        v = [b - 127.5 for b in h]
        n = sum(x * x for x in v) ** 0.5
        out.append([x / n for x in v])
    return out


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "CHROMA_DIR", tmp_path / "chroma")
    monkeypatch.setattr(index, "MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr(index, "embed", fake_embed)
    monkeypatch.setattr(index, "model_revision", lambda: "test")
    monkeypatch.setattr(chunking, "OUT_DIR", tmp_path)
    monkeypatch.setattr(chunking, "load_docs", lambda path=None: [DOC])
    index.client.cache_clear()
    yield
    index.client.cache_clear()


def test_rechunk_deletes_old_strategy_and_leaves_no_orphans(store):
    a = chunking.build("A")
    index.index_chunks(a)
    index.index_chunks(a)                                  # upsert is idempotent: same IDs, no duplicates
    assert index.count({"strategy": "A"}) == len(a)

    result = index.cmd_rechunk("A", "B")
    assert result["old_chunks_after"] == 0
    assert result["deleted"] == len(a)
    assert result["new_indexed"] == result["new_chunks"] > 0
    assert result["orphan_doc_ids"] == result["orphan_chunk_ids"] == 0


def test_orphan_report_flags_stale_chunks(store):
    b = chunking.build("B")
    index.index_chunks(b)
    expected = {"B": {c.chunk_id for c in b[1:]}}         # pretend the first chunk no longer exists
    assert index.orphan_report(expected)["orphan_chunk_ids"] == 1


def test_dense_filter_and_rrf(store):
    index.index_chunks(chunking.build("B"))
    hits = retrieval.dense_search("B", "Lv1", 3, page_types=["talent"])
    assert hits and all(c.strategy == "B" and c.page_type == "talent" for c, _ in hits)
    assert retrieval.dense_search("B", "Lv1", 3, page_types=["weapon"]) == []
    x, y = hits[0][0], hits[1][0]
    fused = retrieval.rrf([(x, 1.0), (y, 0.5)], [(y, 0.9)])
    assert fused[0][0].chunk_id == y.chunk_id              # in both lists beats rank 1 in one


def test_rechunk_into_same_strategy_is_rejected(store):
    index.index_chunks(chunking.build("B"))
    with pytest.raises(SystemExit):
        index.cmd_rechunk("B", "B")
    assert index.count({"strategy": "B"}) > 0                 # nothing was deleted


def test_rebuild_removes_chunks_a_shrunken_page_no_longer_has(store):
    chunks = chunking.build("B")
    index.index_chunks(chunks)
    chunking.write(chunks[:1], chunking.out_path("B"))       # the page now yields a single chunk
    result = index.cmd_build("B")
    assert result == {"chunks": 1, "stale_removed": len(chunks) - 1}
    assert index.stored_ids("B") == {chunks[0].chunk_id}


def test_check_in_sync_detects_unindexed_chunk_file(store):
    chunks = chunking.build("B")
    chunking.write(chunks, chunking.out_path("B"))
    index.index_chunks(chunks[1:])
    with pytest.raises(SystemExit):
        index.check_in_sync("B")
    index.cmd_build("B")
    index.check_in_sync("B")
