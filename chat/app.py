"""MSAI633 RAG chatbot: chat interface (Chainlit).

Start with ./run.sh (port 8800). Corpus path comes from CHUNKS_PATH, default data/chunks.jsonl.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

import llm
from contract import Chunk
from grounding import REFERRAL_TEXT, REFUSAL, cited_indices, is_refusal, needs_referral, unsupported_numbers
from persistence import history_from_thread, init_db
from stub_retriever import StubBM25Retriever, load_chunks

HERE = Path(__file__).parent
CHUNKS_PATH = Path(os.environ.get("CHUNKS_PATH", HERE / "data" / "chunks.jsonl"))
THREADS_DB = Path(os.environ.get("THREADS_DB", HERE / "data" / "threads.sqlite"))
DB_URL = init_db(THREADS_DB)


@cl.data_layer
def data_layer():
    return SQLAlchemyDataLayer(conninfo=DB_URL)


@cl.header_auth_callback
def auth(headers: dict) -> cl.User | None:
    # Local demo bound to 127.0.0.1: no password, every visitor is the same local user.
    # The history sidebar needs auth + persistence; this auth exists only to satisfy that requirement.
    return cl.User(identifier="local", metadata={"role": "local"})

CHUNKS = load_chunks(CHUNKS_PATH)
RETRIEVER = StubBM25Retriever(CHUNKS)
SNAPSHOT = max((c.crawled_at for c in CHUNKS if c.crawled_at), default="unknown")[:10] + " (UTC)"
K_POOL, K_FINAL = 20, 5


def trace_table(chunks: list[Chunk], final_ids: set[str]) -> str:
    rows = ["| # | pre (BM25) | post (stub) | used | source |", "|---|---|---|---|---|"]
    for i, c in enumerate(chunks, 1):
        where = " › ".join([c.title, *c.heading_path])
        used = "✅" if c.chunk_id in final_ids else ""
        rows.append(f"| {i} | {c.score_pre:.2f} | {c.score_post:.2f} | {used} | [{where}]({c.url}) |")
    return "\n".join(rows)


def source_element(i: int, c: Chunk) -> cl.Text:
    where = " › ".join([c.title, *c.heading_path])
    body = f"**{where}**\n\n[{c.url}]({c.url})\n\n_Snapshot: {c.crawled_at[:10] or 'unknown'}_\n\n---\n\n{c.text}"
    return cl.Text(name=f"S{i}", content=body, display="side")


@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])
    await cl.Message(
        content=(
            "Ask me about Genshin Impact's **Nod-Krai** and **Snezhnaya** content — characters, talents, "
            "constellations, weapons, versions.\n\n"
            f"Answers come only from a wiki snapshot taken **{SNAPSHOT}** ({len(CHUNKS)} passages) and may be outdated. "
            "Every claim links to its source — check the source before relying on a number."
        )
    ).send()


@cl.on_chat_resume
async def resume(thread: dict):
    # Chainlit replays messages and panels from the DB; here we only restore LLM history so follow-ups work
    cl.user_session.set("history", history_from_thread(thread))


@cl.on_message
async def on_message(message: cl.Message):
    history: list[dict] = cl.user_session.get("history")
    question = message.content

    async with cl.Step(name="Retrieval trace", type="retrieval", default_open=False) as trace:
        t0 = time.perf_counter()
        async with cl.Step(name="Query rewrite", type="llm") as s:
            s.input = question
            query = await llm.rewrite_query(history, question)
            s.output = query
        async with cl.Step(name=f"Candidate pool (BM25, top {K_POOL})", type="retrieval") as s:
            pool, final = RETRIEVER.retrieve(query, K_POOL, K_FINAL)
            s.output = trace_table(pool, {c.chunk_id for c in final}) if pool else "No matching passages."
        async with cl.Step(name=f"Rerank → top {K_FINAL} (STUB: normalized BM25)", type="rerank") as s:
            s.output = trace_table(final, {c.chunk_id for c in final}) if final else "—"
        trace.output = (f"Query: `{query}` · retriever: `{RETRIEVER.name}` · "
                        f"{len(pool)} candidates → {len(final)} used · {time.perf_counter() - t0:.1f}s")

    # Send an empty placeholder first: implicitly created streamed messages lack createdAt and vanish on replay
    msg = cl.Message(content="")
    await msg.send()
    if final:
        async for tok in llm.stream_answer(history, question, final):
            await msg.stream_token(tok)
        answer = msg.content
    else:
        answer = REFUSAL

    if is_refusal(answer):
        msg.content = f"> ⚠️ **{REFUSAL}**\n>\n> Searched the snapshot for: `{query}`"
    else:
        used = cited_indices(answer, len(final))
        msg.elements = [source_element(i, final[i - 1]) for i in used]
        # Chainlit renders "S3" in the text as a clickable badge; drop the brackets so it doesn't show as "[ S3 ]"
        msg.content = re.sub(r"\[(S\d+)\]", r" \1", answer)
        if used:
            links = " · ".join(f"S{i} [{final[i - 1].title}]({final[i - 1].url})" for i in used)
            msg.content += f"\n\n---\n**Sources:** {links}\n\n_Wiki snapshot {SNAPSHOT}_"
        else:
            msg.content += "\n\n---\n⚠️ _This answer cites no source — treat it as unverified._"

        # Safeguard: every number in the answer must appear verbatim in a cited source (the model once wrote 218.8 for 218.88)
        checked = [final[i - 1] for i in used] or final
        bad = unsupported_numbers(answer, [c.text for c in checked])
        async with cl.Step(name="Number check", type="tool") as s:
            s.output = (f"⚠️ Not found verbatim in cited sources: {', '.join(bad)}" if bad
                        else "All numbers in the answer appear verbatim in the cited sources.")
        if bad:
            msg.content += (f"\n\n> ⚠️ **Number check:** {', '.join(f'`{n}`' for n in bad)} "
                            "does not appear in the cited sources — open the source before relying on it.")

    if needs_referral(question):
        msg.content += f"\n\n> 🧑‍💼 {REFERRAL_TEXT}"

    await msg.update()

    history += [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    cl.user_session.set("history", history)
