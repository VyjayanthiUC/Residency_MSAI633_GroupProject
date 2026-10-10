import pytest

from evaluation import run
from rag.contract import Chunk


def test_report_module_imports():
    from evaluation.report import write_report  # noqa: F401  (the report command crashed on a stale import)


@pytest.mark.parametrize("key, text, expected", [
    ("5", "Lauma is a 5-star character", True),
    ("5", "It has 15 stacks", False),
    ("0.6%", "the base rate is 0.6 %", True),
    ("0.6%", "the rate is 10.6%", False),
    ("12", "the cooldown is 12s", True),
    ("218.88", "it is 218.8%", False),
    ("January 14", "born on January 14th", True),
    ("Luna I", "released in Luna II", False),
    ("Luna I", "released in Luna I (6.0)", True),
])
def test_answer_key_matching_respects_boundaries(key, text, expected):
    assert run.key_in(key, text) is expected


def test_cache_key_changes_with_question_and_chunk_text():
    item = {"id": "S01", "question": "What is Lauma's constellation?"}
    chunk = Chunk(chunk_id="d#B#0001", url="u", title="t", text="Constellation: Cerva Nivea")
    base = run._cache_path("B3", item, [chunk], "")
    assert run._cache_path("B3", {**item, "question": "Edited question"}, [chunk], "") != base
    edited = Chunk(chunk_id="d#B#0001", url="u", title="t", text="Constellation: something else")
    assert run._cache_path("B3", item, [edited], "") != base
    assert run._cache_path("B3", item, [chunk], "") == base


@pytest.mark.parametrize("split", ["test", "all"])
def test_splits_with_test_items_need_final(split):
    with pytest.raises(SystemExit):
        run.guard_test(split, final=False)
    run.guard_test("dev", final=False)

@pytest.mark.parametrize(
    "ranks, expected_recall5, expected_mrr",
    [
        ([1], 1.0, 1.0),
        ([3], 1.0, 1/3),
        ([8], 0.0, 1/8),
    ],
)
def test_retrieval_metrics_manual_cases(
    ranks, expected_recall5, expected_mrr
):
    assert run.recall_at(ranks,5)==pytest.approx(expected_recall5)
    assert run.mrr(ranks)==pytest.approx(expected_mrr)

@pytest.mark.parametrize(
    "correct_rank, expected",
    [
        (1,1.0),
        (3,0.5),
        (8,1/3.169925001442312),
    ],
)
def test_ndcg_manual_cases(correct_rank, expected):
    chunks=[
        Chunk(
            chunk_id=f"chunk_{i}",
            url="https://example.com",
            title="Test",
            text="correct evidence" if i==correct_rank else "irrelevant",
        )
        for i in range(1,11)
    ]

    item={
        "evidence":[
            [
                {
                    "title":"Test",
                    "needles":["correct evidence"]
                }
            ]
        ]
    }
    assert run.ndcg_at(chunks, item, k=10) == pytest.approx(expected)

# Bootstrap CI validation
def test_bootstrap_ci_constant_values():
    values=[1.0,1.0,1.0,1.0]
    
    low,high=run.bootstrap_ci(values,n=1000,seed=633)

    assert low==pytest.approx(1.0)
    assert high==pytest.approx(1.0)

def test_bootstrap_ci_reproducible():
    values=[0.0,1.0,0.0,1.0,1.0]

    result1=run.bootstrap_ci(values,n=1000,seed=633)
    result2=run.bootstrap_ci(values,n=1000,seed=633)
    assert result1==result2

# McNemar validation
def test_mcnemar_identical_results():
    a=[
        {"id":"1","passed":True},
        {"id":"2","passed":False},
        {"id":"3","passed":True},
    ]
    b=[
        {"id":"1","passed":True},
        {"id":"2","passed":False},
        {"id":"3","passed":True},
    ]
    result=run.mcnemar(a,b)

    assert result["n_items"]==3
    assert result["a_fail_b_pass"]==0
    assert result["a_pass_b_fail"]==0
    assert result["p_value"]==pytest.approx(1.0)

def test_mcnemar_discordant_results():
    a=[
        {"id":str(i),"passed":False}
        for i in range(1,7)
    ]
    b=[
        {"id":str(i),"passed":True}
        for i in range(1,7)
    ]

    result=run.mcnemar(a,b)

    assert result["n_items"]==6
    assert result["a_fail_b_pass"]==6
    assert result["a_pass_b_fail"]==0
    assert result["p_value"]==pytest.approx(0.03125)