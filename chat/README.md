# chat/ — Chainlit chat interface

The front end for the RAG pipeline in `rag/`. It implements every interface requirement in §3 of the assignment:

| Requirement | How |
|---|---|
| Conversation history, follow-ups work | The LLM rewrites each follow-up into a standalone query; threads persist in local SQLite and can be resumed |
| Clickable citations on every factual answer | `[n]` markers become clickable badges that open the source chunk in a side panel, plus a Sources list with wiki links |
| Visible refusal | Fixed refusal phrase rendered with a distinct style; low rerank scores refuse before the LLM is called |
| Expandable retrieval trace | A collapsible step shows the 20-chunk candidate pool and the final top 5, with pre- and post-rerank scores |
| Referral to a qualified human | Payment / refund / account questions get a referral to official HoYoverse support |

Ethics safeguards shown in the UI: the **number check** (every number must appear verbatim in a cited source — the
model once wrote 218.8 for 218.88), the **spend-advice guard** ("should I pull?" gets facts only), and the 25-word
**quote limit**.

## Run

From the repo root (see the root README for building the index first):

```bash
./run.sh                                               # http://127.0.0.1:8800
```
Windows PowerShell: `powershell -ExecutionPolicy Bypass -File run.ps1`.

The retriever, models and refusal threshold come from `rag/config.py` / `.env`. Without a built index the UI falls
back to BM25 over the chunk file.

## Files

| File | Role |
|---|---|
| `app.py` | chat flow: retrieval trace, streamed cited answer, refusal / referral, safeguard notes |
| `persistence.py` | SQLite schema and history restore for resumed threads |
| `chainlit.md`, `.chainlit/config.toml` | welcome page and Chainlit settings (Chainlit reads them from this folder) |
