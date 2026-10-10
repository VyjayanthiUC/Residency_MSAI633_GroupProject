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
