"""Stage 9 — LLM calls: query rewriting and cited generation over any OpenAI-compatible API (settings in rag.config).

GLM: only the coding/paas endpoint works; reasoning_effort must be low, otherwise ~6.7x slower.
When streaming, the answer is in delta.content; reasoning (if any) goes to a separate field and is ignored here.
"""
from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from functools import lru_cache

from openai import AsyncOpenAI

from rag import config
from rag.contract import Chunk
from rag.grounding import REFUSAL, REFUSAL_ZH, is_chitchat, is_spend_question, needs_referral

MODEL = config.LLM_MODEL

# Provider-specific request options: keep reasoning short and out of the answer text
if "openrouter.ai" in config.LLM_BASE_URL:
    EXTRA = {"extra_body": {"reasoning": {"effort": "low", "exclude": True}},
             "extra_headers": {"X-Title": "MSAI633 Genshin RAG"}}
else:
    EXTRA = {"reasoning_effort": "low"}

# Free OpenRouter models rate-limit hard (429). The eval harness backs off and retries; the chat UI fails fast
# instead, since 4 backed-off retries keep a user waiting ~7s per call only to fail on an exhausted quota.
EVAL_RETRIES, CHAT_RETRIES = 4, 1
_clients: dict[int, AsyncOpenAI] = {}


def client(max_retries: int = EVAL_RETRIES) -> AsyncOpenAI:
    if max_retries not in _clients:
        if not config.LLM_API_KEY:
            raise RuntimeError("LLM_API_KEY is not set: copy .env.example to .env and add it")
        _clients[max_retries] = AsyncOpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL,
                                            max_retries=max_retries)
    return _clients[max_retries]


class EmptyCompletion(RuntimeError):
    """The model returned no answer text (seen intermittently through OpenRouter, with tokens still billed)."""


# An empty answer is retried, then raised: returned as "", it would be cached and scored as a wrong answer
EMPTY_RETRIES = 2


REWRITE_PROMPT = """Rewrite the user's latest message into ONE standalone English search query for a Genshin Impact wiki.
Resolve pronouns and follow-ups using the conversation (e.g. "her C2?" -> "Lauma constellation 2").
Translate non-English questions into English. Keep character, talent, weapon and version names exactly; when official
English names are listed below the message, use them instead of translating those terms yourself.
Keep the user's intent: do not add words they did not express (e.g. "recommendations", "best", "guide", "tier").
If the latest message is not a question about Genshin Impact (a greeting, thanks, small talk, or a question about you),
output exactly CHITCHAT.
Do not answer the question. Output only the query, nothing else."""

CHITCHAT = "CHITCHAT"
# Room for the model's hidden reasoning (measured up to ~630 tokens): at 200 the reasoning used the whole budget, the
# reply was empty, and every Chinese question or follow-up was searched untranslated (#77)
REWRITE_MAX_TOKENS = 2000

_CJK_NAME = re.compile(r"[㐀-鿿·・]+")


@lru_cache(maxsize=1)
def zh_glossary() -> dict[str, str]:
    """Official Chinese name -> English name, from the "Other Languages" tables in the snapshot.

    Newer game terms (月感电 = Lunar-Charged) are unknown to the model, which otherwise guesses ("Electro-Charged").
    A page can have one table per term ("Other Languages > Verdant Dew"); each table's English row names its term.
    """
    names: dict[str, str] = {}
    with open(config.DOCS_PATH, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            for b in doc["blocks"]:
                if b["heading_path"][1:2] != ["Other Languages"] or not b.get("table"):
                    continue
                rows = [r for r in b["table"]["rows"] if len(r) > 1]
                english = next((r[1].strip() for r in rows if r[0] == "English" and r[1].strip()), doc["title"])
                for row in rows:
                    if row[0].startswith("Chinese") and (m := _CJK_NAME.match(row[1].strip())) and len(m.group(0)) > 1:
                        names.setdefault(m.group(0), english)
    return names


def glossary_hints(text: str) -> list[tuple[str, str]]:
    """(Chinese name, English title) for names in `text`, longest first, without overlaps (月感电 wins over 感电)."""
    hits, taken = [], [False] * len(text)
    for zh in sorted(zh_glossary(), key=len, reverse=True):
        for m in re.finditer(re.escape(zh), text):
            if not any(taken[m.start():m.end()]):
                taken[m.start():m.end()] = [True] * len(zh)
                hits.append((zh, zh_glossary()[zh]))
                break
    return hits

ANSWER_PROMPT = f"""You answer questions about Genshin Impact using ONLY the numbered wiki sources below.

Rules:
- Every factual sentence must end with its source tag, e.g. [S1] or [S2][S3]. Never cite a source that does not support the claim.
- Do not use outside knowledge, even if you believe it is correct. The sources are a snapshot and may differ from what you remember.
- Never copy more than 25 consecutive words from a source; paraphrase instead.
- If the sources do not contain the answer, reply with exactly: {REFUSAL}
  (for a question asked in Chinese, reply with exactly: {REFUSAL_ZH})
  If they answer only part of the question, answer that part with citations and say what is missing.
- Reply in the same language as the user's question. Keep it concise."""


def format_sources(chunks: list[Chunk]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        where = " > ".join([c.title, *c.heading_path])
        parts.append(f"[S{i}] {where}\nURL: {c.url}\n{c.text}")
    return "\n\n".join(parts)


async def rewrite_query(history: list[dict], question: str) -> str:
    """A standalone English search query, or CHITCHAT when the message is not a question to search for."""
    if is_chitchat(question):
        return CHITCHAT
    # Nothing to resolve or translate: skip the call (it would cost half of each turn's rate-limited requests)
    if not history and question.isascii():
        return question
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    hints = glossary_hints(question)
    names = ("\n\nOfficial English names: " + "; ".join(f"{zh} = {en}" for zh, en in hints)) if hints else ""
    resp = await client(CHAT_RETRIES).chat.completions.create(
        model=MODEL,
        max_tokens=REWRITE_MAX_TOKENS,
        **EXTRA,
        messages=[
            {"role": "system", "content": REWRITE_PROMPT},
            {"role": "user", "content": f"Conversation so far:\n{convo or '(none)'}\n\nLatest message: {question}{names}"},
        ],
    )
    q = (resp.choices[0].message.content or "").strip().strip('"')
    if q.upper().rstrip(".") == CHITCHAT:
        # Money and account questions are off-topic for the wiki but must still reach the referral/spend safeguards
        return question if needs_referral(question) or is_spend_question(question) else CHITCHAT
    return q or question


def _answer_messages(history: list[dict], question: str, chunks: list[Chunk], note: str = "") -> list[dict]:
    sources = format_sources(chunks) if chunks else "(no sources retrieved)"
    system = ANSWER_PROMPT + (f"\n- {note}" if note else "")
    return [
        {"role": "system", "content": system},
        *history[-6:],
        {"role": "user", "content": f"Sources:\n\n{sources}\n\nQuestion: {question}"},
    ]


async def stream_answer(history: list[dict], question: str, chunks: list[Chunk], note: str = "") -> AsyncIterator[str]:
    stream = await client(CHAT_RETRIES).chat.completions.create(
        model=MODEL, max_tokens=1500, temperature=0, stream=True,
        messages=_answer_messages(history, question, chunks, note), **EXTRA,
    )
    empty = True
    async for ev in stream:
        if ev.choices and ev.choices[0].delta.content:
            empty = False
            yield ev.choices[0].delta.content
    if empty:
        raise EmptyCompletion(f"{MODEL} streamed no answer text")


async def complete(messages: list[dict], max_tokens: int = 1500) -> tuple[str, dict]:
    """Non-streamed call for the evaluation harness: returns (text, token usage and serving provider)."""
    for _ in range(EMPTY_RETRIES + 1):
        resp = await client().chat.completions.create(
            model=MODEL, max_tokens=max_tokens, temperature=0, messages=messages, **EXTRA,
        )
        text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        if text:
            u = resp.usage
            usage = {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens} if u else {}
            # OpenRouter can serve one model from several providers; record which one answered
            if provider := getattr(resp, "provider", None):
                usage["provider"] = provider
            return text, usage
    raise EmptyCompletion(f"{MODEL} returned no answer text {EMPTY_RETRIES + 1} times")


async def answer(question: str, chunks: list[Chunk], note: str = "") -> tuple[str, dict]:
    return await complete(_answer_messages([], question, chunks, note))


CLOSED_BOOK_PROMPT = f"""Answer the question about Genshin Impact from your own knowledge. Be concise.
If you do not know or are unsure, reply with exactly: {REFUSAL}"""


async def answer_closed_book(question: str) -> tuple[str, dict]:
    """Baseline B0: same model, no retrieval."""
    return await complete([{"role": "system", "content": CLOSED_BOOK_PROMPT}, {"role": "user", "content": question}])
