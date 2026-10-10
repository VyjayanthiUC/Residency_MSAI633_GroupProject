from pathlib import Path

from rag.contract import Chunk, load_chunks
from rag import retrieval
from rag.grounding import (REFUSAL, cited_indices, is_refusal, is_spend_question, long_quotes, needs_referral,
                           normalize_citations, recommends_spending, strip_citations, unsupported_numbers)

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


def test_bm25_pipeline_shapes_and_order(monkeypatch):
    monkeypatch.setattr(retrieval, "bm25_for", lambda strategy: retrieval.BM25(load_chunks(FIXTURE)))
    pool, final = retrieval.Pipeline(mode="bm25", rerank=False).retrieve("Lauma elemental skill press DMG", 20, 5)
    assert 0 < len(final) <= 5 <= len(pool) <= 20
    assert final == pool[:5]
    assert all(a.score_pre >= b.score_pre for a, b in zip(pool, pool[1:]))
    assert all(c.score_post == c.score_pre for c in pool)


def test_bm25_no_match_and_page_type_filter():
    # >= 3 docs: with one doc every term is in every doc and BM25's IDF is non-positive
    bm25 = retrieval.BM25([Chunk(chunk_id=i, url="u", title="t", text=t, page_type=p)
                           for i, t, p in [("x", "alpha beta", "talent"), ("y", "gamma", "weapon"), ("z", "delta", "weapon")]])
    assert bm25.search("zzzz", 20) == []
    assert bm25.search("alpha", 20, page_types=["weapon"]) == []
    assert len(bm25.search("alpha", 20, page_types=["talent"])) == 1


def test_referral_ignores_game_terms():
    # "Charged Attack", shop purchases and "account for" are gameplay, not billing
    assert not needs_referral("What is Lauma's Charged Attack multiplier at level 10?")
    assert not needs_referral("Can I purchase this weapon from Paimon's Bargains?")
    assert not needs_referral("Does her burst take into account Elemental Mastery?")
    assert needs_referral("I was charged twice for Welkin")
    assert needs_referral("My account was hacked, how do I recover it?")


def test_partial_answer_is_not_refusal():
    partial = "Lauma's skill is Runo [S1]. " + REFUSAL + " for her C6."
    assert not is_refusal(partial)


def test_spend_question_and_recommendation():
    assert is_spend_question("Should I pull for Columbina?")
    assert is_spend_question("Is it worth spending my rent on this banner?")
    assert not is_spend_question("When does the Columbina banner end?")
    assert recommends_spending("You should definitely pull for her [S1].")
    assert not recommends_spending("Soft pity starts at 74 pulls [S1].")


def test_strip_citations():
    assert strip_citations("A [S1]. B [S2][S3].") == "A. B."


def test_fullwidth_citations_count_as_citations():
    # issue #70: the model sometimes writes 【S2】 instead of [S2]
    answer = normalize_citations("Nod-Krai is a region 【S2】 【S4】. Lauma is Dendro【 S1 】.")
    assert answer == "Nod-Krai is a region [S2] [S4]. Lauma is Dendro[S1]."
    assert cited_indices(answer, 5) == [2, 4, 1]
    assert strip_citations(answer) == "Nod-Krai is a region. Lauma is Dendro."
    assert not is_refusal(normalize_citations("Lauma is Dendro【S1】. " + REFUSAL))
    assert normalize_citations("A [S1]. 【note】") == "A [S1]. 【note】"


def test_long_quotes():
    src = [" ".join(f"w{i}" for i in range(40))]
    copied = " ".join(f"w{i}" for i in range(5, 35))  # 30 words
    assert long_quotes(f"Intro {copied} [S1].", src) == [copied]
    assert long_quotes(" ".join(f"w{i}" for i in range(0, 25)), src) == []  # exactly 25 is allowed
