"""MSAI633 RAG chatbot: Chainlit chat interface.

Start with ./run.sh or run.ps1 from the repo root (port 8800). Retrieval is rag.retrieval.Pipeline configured from
rag.config (default: hybrid + rerank over strategy B); if artifacts/chroma/ does not exist it falls back to BM25 over
the chunk file.
"""
from __future__ import annotations

import asyncio
import re
import time

import chainlit as cl
import openai
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

from chat.persistence import history_from_thread, init_db
from rag import config, index, retrieval
from rag import generation as llm
from rag.contract import Chunk
from rag.grounding import (MAX_QUOTE_WORDS, REFERRAL_TEXT, SPEND_PROMPT_NOTE, SPEND_TEXT, cited_indices, is_chinese,
                       is_refusal, is_spend_question, long_quotes, needs_referral, normalize_citations,
                       recommends_spending, refusal_for, strip_citations, unsupported_numbers)

DB_URL = init_db(config.THREADS_DB)
K_POOL, K_FINAL = config.K_POOL, config.K_FINAL

if config.CHROMA_DIR.exists():
    RETRIEVER = retrieval.from_config()
    if RETRIEVER.mode != "bm25":
        index.check_in_sync(RETRIEVER.strategy)
else:
    RETRIEVER = retrieval.Pipeline(strategy=config.CHUNK_STRATEGY, mode="bm25", rerank=False)
CHUNKS = retrieval.bm25_for(RETRIEVER.strategy).chunks  # also builds the BM25 index at startup
if RETRIEVER.mode != "bm25" or RETRIEVER.rerank:
    RETRIEVER.retrieve("warmup")  # load the embedder and reranker now (~25s), not on the first user question
REFUSE_BELOW = config.REFUSE_BELOW if RETRIEVER.rerank else 0.0
POST_LABEL = "rerank" if RETRIEVER.rerank else "= pre"
SNAPSHOT = max((c.crawled_at for c in CHUNKS if c.crawled_at), default="unknown")[:10] + " (UTC)"


@cl.data_layer
def data_layer():
    return SQLAlchemyDataLayer(conninfo=DB_URL)


@cl.header_auth_callback
def auth(headers: dict) -> cl.User | None:
    # Bound to 127.0.0.1 with one local user: auth exists only because Chainlit's history sidebar requires it.
    return cl.User(identifier="local", metadata={"role": "local"})


def where(c: Chunk) -> str:
    return " › ".join([c.title, *c.heading_path])


def trace_table(chunks: list[Chunk], final_ids: set[str]) -> str:
    rows = [f"| # | pre ({RETRIEVER.score_label}) | post ({POST_LABEL}) | used | source |", "|---|---|---|---|---|"]
    rows += [f"| {i} | {c.score_pre:.3f} | {c.score_post:.3f} | {'✅' if c.chunk_id in final_ids else ''} | [{where(c)}]({c.url}) |"
             for i, c in enumerate(chunks, 1)]
    return "\n".join(rows)


def source_element(i: int, c: Chunk) -> cl.Text:
    body = (f"**{where(c)}**\n\n[{c.url}]({c.url})\n\n_Snapshot: {c.crawled_at[:10] or 'unknown'} · "
            f"applies to game version dated {c.effective_date or 'undated'}_\n\n---\n\n{c.text}")
    return cl.Text(name=f"S{i}", content=body, display="side")


def safeguard_notes(question: str, answer: str, final: list[Chunk], used: list[int]) -> tuple[list[str], list[str]]:
    """Post-generation checks. Returns (warnings shown under the answer, number-check bad values)."""
    notes = []
    cited = [final[i - 1] for i in used] or final
    bad = unsupported_numbers(answer, [c.text for c in cited])
    if bad:
        notes.append(f"⚠️ **Number check:** {', '.join(f'`{n}`' for n in bad)} does not appear in the cited sources "
                     "— open the source before relying on it.")
    if quotes := long_quotes(answer, [c.text for c in final]):
        notes.append(f"⚠️ **Quote limit:** {len(quotes)} passage(s) copy more than {MAX_QUOTE_WORDS} consecutive words "
                     "from a source.")
    recommends = recommends_spending(answer)
    if recommends:
        notes.append("⚠️ **Spend-advice guard:** this answer appears to recommend spending — disregard that part.")
    if recommends or is_spend_question(question):
        notes.append(f"💸 {SPEND_TEXT}")
    return notes, bad


async def retrieve(history: list[dict], question: str) -> tuple[str, list[Chunk]]:
    """Rewrite + retrieve + rerank inside one collapsible trace step. Returns (query, final chunks or [] to refuse)."""
    async with cl.Step(name="Retrieval trace", type="retrieval", default_open=False) as trace:
        t0 = time.perf_counter()
        async with cl.Step(name="Query rewrite", type="llm") as s:
            s.input = question
            try:
                query = await llm.rewrite_query(history, question)
            except openai.APIError:
                query = question  # rewrite is an optimization; retrieve with the raw question
            s.output = query
        if query == llm.CHITCHAT:
            trace.output = "Small talk → no retrieval, replying with the welcome message."
            return query, []
        async with cl.Step(name=f"Candidate pool ({RETRIEVER.score_label}, top {K_POOL})", type="retrieval") as s:
            pool, final = await asyncio.to_thread(RETRIEVER.retrieve, query, K_POOL, K_FINAL)
            s.output = trace_table(pool, {c.chunk_id for c in final}) if pool else "No matching passages."
        async with cl.Step(name=f"Final top {K_FINAL} ({POST_LABEL})", type="rerank") as s:
            s.output = trace_table(final, {c.chunk_id for c in final}) if final else "—"
            if final and final[0].score_post < REFUSE_BELOW:
                s.output += (f"\n\nTop rerank score {final[0].score_post:.3f} < threshold {REFUSE_BELOW} "
                             "→ refusing without calling the LLM.")
                final = []
        trace.output = (f"Query: `{query}` · retriever: `{RETRIEVER.name}` · {len(pool)} candidates → "
                        f"{len(final)} used · {time.perf_counter() - t0:.1f}s")
    return query, final


def welcome(chinese: bool = False) -> str:
    if chinese:
        return (f"我可以回答原神**挪德卡莱**和**至冬**相关的问题：角色、天赋、命之座、武器、版本。\n\n"
                f"答案只来自 **{SNAPSHOT}** 的维基快照（{len(CHUNKS)} 个段落），可能已经过时；每条结论都附出处，"
                "涉及数字时请先点开出处核对。\n\n可以这样问：\n- 菈乌玛是什么元素？\n- 阿蕾奇诺的生日是哪天？")
    return ("Ask me about Genshin Impact's **Nod-Krai** and **Snezhnaya** content — characters, talents, "
            "constellations, weapons, versions.\n\n"
            f"Answers come only from a wiki snapshot taken **{SNAPSHOT}** ({len(CHUNKS)} passages) and may be outdated. "
            "Every claim links to its source — check the source before relying on a number.\n\n"
            "Try:\n- What element is Lauma?\n- When is Arlecchino's birthday?")


@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])
    await cl.Message(content=welcome()).send()


@cl.on_chat_resume
async def resume(thread: dict):
    # Chainlit replays the messages itself; only the LLM history needs restoring for follow-ups
    cl.user_session.set("history", history_from_thread(thread))


@cl.on_message
async def on_message(message: cl.Message):
    history: list[dict] = cl.user_session.get("history")
    question = message.content
    query, final = await retrieve(history, question)
    if query == llm.CHITCHAT:
        await cl.Message(content=welcome(is_chinese(question))).send()
        return

    # Send an empty placeholder first: implicitly created streamed messages lack createdAt and vanish on replay
    msg = cl.Message(content="")
    await msg.send()
    refusal = refusal_for(question)
    answer = refusal
    if final:
        try:
            async for tok in llm.stream_answer(history, question, final,
                                               SPEND_PROMPT_NOTE if is_spend_question(question) else ""):
                await msg.stream_token(tok)
            answer = normalize_citations(msg.content)
        except (openai.APIError, llm.EmptyCompletion) as e:
            msg.content = f"> ⚠️ The language model is unavailable right now ({type(e).__name__}). Please try again shortly."
            await msg.update()
            return

    if is_refusal(answer):
        searched = "检索词" if is_chinese(question) else "Searched the snapshot for"
        msg.content = f"> ⚠️ **{refusal}**\n>\n> {searched}: `{query}`"
        notes = [f"💸 {SPEND_TEXT}"] if is_spend_question(question) else []
    else:
        used = cited_indices(answer, len(final))
        msg.elements = [source_element(i, final[i - 1]) for i in used]
        # Chainlit turns a bare "S3" into a clickable badge; "[S3]" would render as "[ S3 ]"
        msg.content = re.sub(r"\[(S\d+)\]", r" \1", answer)
        if used:
            links = " · ".join(f"S{i} [{final[i - 1].title}]({final[i - 1].url})" for i in used)
            msg.content += f"\n\n---\n**Sources:** {links}\n\n_Wiki snapshot {SNAPSHOT}_"
        else:
            msg.content += "\n\n---\n⚠️ _This answer cites no source — treat it as unverified._"
        notes, bad = safeguard_notes(question, answer, final, used)
        async with cl.Step(name="Number check", type="tool") as s:
            s.output = (f"⚠️ Not found verbatim in cited sources: {', '.join(bad)}" if bad
                        else "All numbers in the answer appear verbatim in the cited sources.")
    if needs_referral(question):
        notes.append(f"🧑‍💼 {REFERRAL_TEXT}")
    msg.content += "".join(f"\n\n> {n}" for n in notes)
    await msg.update()

    # [Sn] numbering is only valid for this turn's sources
    history += [{"role": "user", "content": question}, {"role": "assistant", "content": strip_citations(answer)}]
    cl.user_session.set("history", history)
