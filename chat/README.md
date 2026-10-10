# chat/ — Chainlit chat interface

The chat front end for the RAG chatbot. It implements every interface requirement in §3 of the assignment:

| Requirement | How |
|---|---|
| Conversation history, follow-ups work | The LLM rewrites each follow-up into a standalone query; threads persist in local SQLite and can be resumed |
| Clickable citations on every factual answer | `[n]` markers become clickable badges that open the source chunk in a side panel, plus a Sources list with wiki links |
| Visible refusal | Fixed refusal phrase rendered with a distinct style |
| Expandable retrieval trace | A collapsible step shows the 20-chunk candidate pool and the final top 5, with pre- and post-rerank scores |
| Referral to a qualified human | Payment / refund / account questions get a referral to official HoYoverse support |

It also runs one **ethics safeguard**: every number in an answer must appear verbatim in a cited source,
otherwise a warning is shown (the model once wrote 218.8 for 218.88).

## Status

- **Retrieval is a STUB** (`stub_retriever.py`): BM25 top-20, then the top 5 are passed through as "reranked" with placeholder scores.
  The real dense / BM25 / hybrid retriever and the reranker plug in through `contract.py` (`Retriever.retrieve(query, k_pool, k_final) -> (pool, final)`) with no UI changes.
- **Chunking is interim** (`ingest_html.py`): split on h2/h3 sections, then at ~1500 characters. Not the formal chunking experiment.
- Generation uses GLM (`glm-5.3-flash`) via an OpenAI-compatible API.

## Run it

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and the corpus snapshot in `data/genshin/` (PR #2).

```bash
cd chat
cp .env.example .env              # add your ZAI_API_KEY
uv sync
uv run python ingest_html.py      # data/genshin/ -> chat/data/chunks.jsonl (~2.4k chunks)
./run.sh                          # http://127.0.0.1:8800
```

Tests: `uv run pytest tests` (citation parsing, refusal and referral detection, number check, retriever shape, HTML conversion, persistence).

## Files

| File | Role |
|---|---|
| `app.py` | Chainlit app: chat flow, citations, retrieval trace, refusal / referral, number check |
| `llm.py` | Query rewriting and streamed, cited generation |
| `grounding.py` | Pure functions: citation parsing, refusal detection, referral detection, number verification |
| `contract.py` | `Chunk` dataclass and `Retriever` protocol — the interface the real retriever implements |
| `stub_retriever.py` | Placeholder BM25 retriever |
| `ingest_html.py` | Rendered wiki HTML → `chunks.jsonl` |
| `persistence.py` | SQLite schema and history restore for resumed threads |

`chat/data/` (chunks, thread DB, auth secret) is generated locally and git-ignored.
