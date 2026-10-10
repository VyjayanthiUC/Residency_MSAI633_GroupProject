"""GLM calls: query rewriting + streamed, cited generation.

Tested settings: only the coding/paas endpoint works; reasoning_effort must be low, otherwise ~6.7x slower;
when streaming, the answer is in delta.content and reasoning goes to delta.reasoning_content (ignored here).
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from contract import Chunk
from grounding import REFUSAL

BASE_URL = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4")
MODEL = os.environ.get("GLM_MODEL", "glm-5.3-flash")

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        key = os.environ.get("ZAI_API_KEY")
        if not key:
            raise RuntimeError("ZAI_API_KEY is not set: put it in .env and start with run.sh, or export it yourself")
        _client = AsyncOpenAI(api_key=key, base_url=BASE_URL)
    return _client


REWRITE_PROMPT = """Rewrite the user's latest message into ONE standalone English search query for a Genshin Impact wiki.
Resolve pronouns and follow-ups using the conversation (e.g. "her C2?" -> "Lauma constellation 2").
Translate non-English questions into English. Keep character, talent, weapon and version names exactly.
Output only the query, nothing else."""

ANSWER_PROMPT = f"""You answer questions about Genshin Impact using ONLY the numbered wiki sources below.

Rules:
- Every factual sentence must end with its source tag, e.g. [S1] or [S2][S3]. Never cite a source that does not support the claim.
- Do not use outside knowledge, even if you believe it is correct. The sources are a snapshot and may differ from what you remember.
- Never copy more than 25 consecutive words from a source; paraphrase instead.
- If the sources do not contain the answer, reply with exactly: {REFUSAL}
  If they answer only part of the question, answer that part with citations and say what is missing.
- Reply in the same language as the user's question. Keep it concise."""


def format_sources(chunks: list[Chunk]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        where = " > ".join([c.title, *c.heading_path])
        parts.append(f"[S{i}] {where}\nURL: {c.url}\n{c.text}")
    return "\n\n".join(parts)


async def rewrite_query(history: list[dict], question: str) -> str:
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    resp = await client().chat.completions.create(
        model=MODEL,
        reasoning_effort="low",
        max_tokens=200,
        messages=[
            {"role": "system", "content": REWRITE_PROMPT},
            {"role": "user", "content": f"Conversation so far:\n{convo or '(none)'}\n\nLatest message: {question}"},
        ],
    )
    q = (resp.choices[0].message.content or "").strip().strip('"')
    return q or question


async def stream_answer(history: list[dict], question: str, chunks: list[Chunk]) -> AsyncIterator[str]:
    sources = format_sources(chunks) if chunks else "(no sources retrieved)"
    messages = [
        {"role": "system", "content": ANSWER_PROMPT},
        *history[-6:],
        {"role": "user", "content": f"Sources:\n\n{sources}\n\nQuestion: {question}"},
    ]
    stream = await client().chat.completions.create(
        model=MODEL, reasoning_effort="low", max_tokens=1500, stream=True, messages=messages,
    )
    async for ev in stream:
        if ev.choices and ev.choices[0].delta.content:
            yield ev.choices[0].delta.content
