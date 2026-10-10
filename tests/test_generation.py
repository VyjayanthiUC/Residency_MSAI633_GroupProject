import asyncio
from types import SimpleNamespace

import pytest

from evaluation import run
from rag import generation as llm


def _response(content: str | None, provider: str = "Fireworks"):
    msg = SimpleNamespace(content=content)
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=20)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage, provider=provider)


def _fake_client(monkeypatch, responses: list):
    calls = []

    async def create(**kwargs):
        calls.append(kwargs)
        return responses[min(len(calls), len(responses)) - 1]

    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(llm, "client", lambda max_retries=llm.EVAL_RETRIES: fake)
    return calls


def test_complete_retries_empty_answer_and_records_provider(monkeypatch):
    calls = _fake_client(monkeypatch, [_response(""), _response("Shimi Chazuke [S1].", provider="Friendli")])
    text, usage = asyncio.run(llm.complete([{"role": "user", "content": "q"}]))
    assert text == "Shimi Chazuke [S1]."
    assert usage == {"prompt_tokens": 100, "completion_tokens": 20, "provider": "Friendli"}
    assert len(calls) == 2


def test_complete_raises_after_repeated_empty_answers(monkeypatch):
    calls = _fake_client(monkeypatch, [_response(None), _response("  ")])
    with pytest.raises(llm.EmptyCompletion):
        asyncio.run(llm.complete([{"role": "user", "content": "q"}]))
    assert len(calls) == llm.EMPTY_RETRIES + 1


def test_empty_stream_raises(monkeypatch):
    async def stream():
        for content in (None, ""):
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=content))])

    async def create(**kwargs):
        return stream()

    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(llm, "client", lambda max_retries=llm.EVAL_RETRIES: fake)

    async def collect():
        return [tok async for tok in llm.stream_answer([], "q", [])]

    with pytest.raises(llm.EmptyCompletion):
        asyncio.run(collect())


def test_empty_answer_is_not_cached_or_scored(monkeypatch, tmp_path):
    async def empty(question):
        raise llm.EmptyCompletion("no answer text")

    monkeypatch.setattr(run, "CACHE", tmp_path)
    monkeypatch.setattr(llm, "answer_closed_book", empty)
    item = {"id": "T01", "category": "single_hop", "question": "q", "expected_behavior": "answer", "answer_keys": ["x"]}
    out = asyncio.run(run.generation_eval([item], max_calls=5, configs=["B0 closed-book"]))
    assert out == {"B0 closed-book": []}  # stopped, not scored as a wrong answer
    assert not list(tmp_path.rglob("*.json"))  # nothing cached, so a re-run retries the item
