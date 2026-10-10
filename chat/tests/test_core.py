import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contract import Chunk
from grounding import REFUSAL, cited_indices, is_refusal, needs_referral, unsupported_numbers
from stub_retriever import StubBM25Retriever, load_chunks

FIXTURE = Path(__file__).parent / "fixtures" / "chunks_sample.jsonl"


def test_cited_indices_dedup_and_bounds():
    assert cited_indices("A [S2]. B [S1][S2]. C [S9].", 5) == [2, 1]
    assert cited_indices("no citations", 5) == []


def test_refusal_detection():
    assert is_refusal(REFUSAL)
    assert is_refusal("Sorry. " + REFUSAL.rstrip("."))
    assert not is_refusal("Lauma's skill deals 218.88% [S1].")


def test_referral():
    assert needs_referral("I topped up by mistake, can I get a refund?")
    assert needs_referral("我充值充错了能退款吗")
    assert not needs_referral("What is Lauma's elemental skill?")


def test_unsupported_numbers_catches_rounding():
    src = ["Press DMG (%) — Lv9: 206.72; Lv10: 218.88; Lv11: 231.04"]
    assert unsupported_numbers("At level 10 it is 218.8% [S1].", src) == ["218.8"]
    assert unsupported_numbers("At level 10 it is 218.88% [S1].", src) == []


def test_unsupported_numbers_ignores_citations_and_ids():
    src = ["Version 6.2 was released on December 3, 2025. Cost 1,600 Primogems."]
    ans = "Version 6.2 [S1] came out December 3, 2025 [S2] and C2 costs 1,600 [S1]."
    assert unsupported_numbers(ans, src) == []
    assert unsupported_numbers("It costs 160 Primogems.", src) == ["160"]


def test_retriever_shapes_and_order():
    r = StubBM25Retriever(load_chunks(FIXTURE))
    pool, final = r.retrieve("Lauma elemental skill press DMG", 20, 5)
    assert 0 < len(final) <= 5 <= len(pool) <= 20
    assert final == pool[:5]
    assert all(a.score_pre >= b.score_pre for a, b in zip(pool, pool[1:]))
    assert pool[0].score_post == 1.0


def test_retriever_no_match_returns_empty():
    r = StubBM25Retriever([Chunk(chunk_id="x", url="u", title="t", text="alpha beta")])
    assert r.retrieve("zzzz", 20, 5) == ([], [])
