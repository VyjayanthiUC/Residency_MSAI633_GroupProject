# MSAI 633 Residency — Retrieval-Augmented Chatbot

Team project for MSAI 633 (Ethics in Artificial Intelligence), Fall 2026 residency, October 9–11.

We are building a chatbot that answers real user questions using **only** content scraped from one public website.
Every factual claim cites the page it came from, and when the corpus does not support an answer, the chatbot says so instead of guessing.

> **Status:** end-to-end pipeline running (hybrid retrieval + reranker, cited generation, two ethics safeguards); evaluation in progress. Proposal: `reports/00_proposal.md`.

## Team

| Member | GitHub | Role |
|---|---|---|
| Gudla, Shyamala Keerthi | @ShyamalaKeerthi | Product Manager |
| Kamath, Vyjayanthi (VJ) | @VyjayanthiUC | Lead Analyst |
| Konkayala, Deep | @deepkse | AI Engineer / Architect |
| Daniel, Ibukun | @ibkcode | AI Engineer |
| Ban, Sohyun | @Eva103 | QA & Evaluation Engineer |
| Akpe, Oyin | @oyinakpe2-firstgrandprince | Project Manager |
| Li, Yanwei | @Saweisra | Data & Evaluation Engineer |

## Pipeline

```
scrape → extraction → chunking → embedding → vector database
       → retrieval (dense / BM25 / hybrid) → reranking → generation → chat interface
```

| Stage | Requirement (summary) |
|---|---|
| 1. Scrape | Honor robots.txt in code, ≤1 request/second, descriptive User-Agent; save raw bytes with URL, timestamp, and content hash; ≥150 pages incl. ≥5 PDFs and ≥3 table pages |
| 2. Extraction | Strip boilerplate, extract PDF text, keep tables as tables, dedupe by content hash, store per-document metadata |
| 3. Chunking | Fixed-size with overlap vs. structure-aware (heading path carried into each chunk) |
| 4. Embedding | Record model, version, dimension, metric, and normalization; metric must match normalization |
| 5. Vector database | Deterministic chunk IDs, metadata filtering on page type, working delete path |
| 6. Re-chunk | Re-index from saved normalized text (no re-crawl), delete stale chunks, prove no orphans remain |
| 7. Retrieval | Dense, BM25, and hybrid fusion, all measured; candidate pool ≥20 |
| 8. Reranking | Cross-encoder or LLM reranker to top ≤5; report lift, latency, and Recall@20 ceiling |
| 9. Generation | Answer only from retrieved context, cite a URL per claim, quote ≤25 consecutive words, refuse when context is insufficient |

## Deliverables

- Working chatbot with conversation history, clickable citations, visible refusals, an expandable retrieval trace (pre- and post-rerank scores), and referral to a qualified human for high-stakes questions
- Golden evaluation set (≥40 items, human-verified, written before tuning)
- Reports under `reports/`: `00_proposal` · `01_ingestion` · `02_chunking` · `03_golden_set` · `04_retrieval_reranking` · `05_generation` · `06_final_performance` · `07_ethics`
- Live demo (8–10 minutes) on Sunday

## Schedule

| Day | Goals |
|---|---|
| Friday | Domain chosen, proposal submitted, repo + issues set up, crawl running (≥150 pages), ≥15 golden items |
| Saturday | End-to-end chatbot via reviewed PRs, golden set at 40, chunking comparison + re-chunk, BM25 / hybrid / reranker measured, reports 01–04, two ethics safeguards in code |
| Sunday | Freeze config, run test split once, confidence intervals, ≥15 labeled failures, reports 05–07 + README, live presentation |

## How we work

- **`main` is protected** — no direct pushes. Work on a short-lived branch (`scrape/crawler`, `chunk/structure-aware`, `eval/golden-set`) and open a pull request.
- **Every PR needs one teammate's approval** before merging.
- **Commit messages** are short and present-tense: `feat: add hybrid retrieval fusion`, `fix: dedupe near-duplicate PDFs`. No `wip` or `updates`.
- **Commit under your own account.** Make sure `git config user.email` matches an email on your GitHub account, or your commits will not be credited to you.
- **Never commit secrets.** `.env` and any API keys are git-ignored from the first commit.
- **Use the shared corpus snapshot** in `data/` instead of re-crawling the live site. Don't hand-edit it; a new crawl goes in as a new snapshot via PR.
- **Track work in Issues** — each pipeline stage and each report has an owner.

## Repository layout

```
rag/          the pipeline — one module per stage, all settings in rag/config.py
  config.py     paths, models, chunk sizes, k, fusion depth, refusal threshold (each overridable in .env)
  contract.py   Chunk dataclass + Retriever protocol: the interface between pipeline and UI
  chunking.py   stage 3: strategies A (fixed 512/64) and B (structure-aware), deterministic chunk IDs
  index.py      stages 4–6: embeddings, Chroma store, delete path, re-chunk + orphan check
  retrieval.py  stages 7–8: BM25 / dense / hybrid RRF, cross-encoder reranker (Pipeline)
  generation.py stage 9: query rewrite + cited answers over any OpenAI-compatible LLM
  grounding.py  citation parsing, refusal, number check, quote limit, spend-advice and referral guards
ingest/       stages 1–2: crawler + extractor (see ingest/README.md for the output contract), PDF path
evaluation/   golden set, frozen dev/test split, harness (run.py), report tables (report.py), results/
chat/         Chainlit UI (app.py, persistence, chainlit config), mounted at /chat
web/          site at / built only from data/genshin/normalized/md (wiki.py), with a chat pop-up that opens /chat;
              server.py serves both on one port (FastAPI + mount_chainlit), templates/, static/
tests/        pytest suite
data/         committed corpus snapshot (CC BY-SA, see data/ATTRIBUTION.md)
reports/      00 proposal … 07 ethics
artifacts/    generated, git-ignored: chunks, vectors, PDFs, LLM cache, chat history
```

## Setup

One [uv](https://docs.astral.sh/uv/) project at the repo root (Python 3.12); `uv sync` installs the packages in editable
mode, so every command runs from the repo root. An NVIDIA GPU is used automatically for embedding and reranking when
present (CUDA build of torch on Windows/Linux); CPU works, just slower. First runs download `BAAI/bge-m3` and
`BAAI/bge-reranker-v2-m3` (~2.3 GB each) to the Hugging Face cache.

```bash
cp .env.example .env                                  # add LLM_API_KEY (OpenRouter key; default model z-ai/glm-5.3-flash needs a few dollars of credit)
uv sync
uv run python -m rag.chunking                         # docs.jsonl -> artifacts/chunks_A.jsonl, chunks_B.jsonl
uv run python -m rag.index build --strategy A         # embeddings -> local Chroma (artifacts/chroma/)
uv run python -m rag.index build --strategy B
uv run pytest -q
./run.sh                                              # Windows PowerShell: powershell -ExecutionPolicy Bypass -File run.ps1
# -> http://127.0.0.1:8800       site (every wiki page in the snapshot) with the chat pop-up (bottom-right)
# -> http://127.0.0.1:8800/chat  full chat UI with history
```

To change a model, chunk size, `k` or threshold, set it in `.env` (all options are listed in `.env.example`).

Reproducing the reported numbers (results land in `evaluation/results/`):

| Command | Produces |
|---|---|
| `uv run python -m evaluation.golden validate` | checks every golden-set needle against the corpus and both chunkings |
| `uv run python -m evaluation.run retrieval --split dev` | Recall@5/@20, MRR, nDCG@10, latency for B1, B2, the ablation and B3 |
| `uv run python -m evaluation.run threshold --split dev` | rerank refusal threshold (dev only) |
| `uv run python -m evaluation.run generation --split dev --max-calls 40` | B3, B2, B0, B1 answers (cached; resumable under rate limits) |
| `uv run python -m evaluation.run report --split dev` | `summary_dev.md` with 95% bootstrap CIs and McNemar |
| `uv run python -m ingest.pdfs` | rendered-PDF extraction vs HTML extraction |
| `CHROMA_DIR=artifacts/chroma_rechunk_demo uv run python -m rag.index rechunk --old A --new B` | re-chunk without re-crawl, stale deletion, orphan check (on a copy of the index) |
| `... --split test --final` | the single held-out test run, after the configuration is frozen |

The corpus snapshot is CC BY-SA; see [`data/ATTRIBUTION.md`](data/ATTRIBUTION.md).

## AI usage

AI tools are allowed and documented here at every milestone: which tool, what it was used for, on which artifact, and who checked it.

| Date | Tool | Used for | Artifact | Human check |
|---|---|---|---|---|
| 2026-10-10 | Claude Code (Claude Opus 5.5) | Code review of proposal, chat UI and data snapshot; bug fixes (referral false positives, partial-answer refusal, stale citations in history); spend-advice guard; quote-limit check | `rag/grounding.py`, `chat/app.py`, `rag/generation.py`, tests | Deep Konkayala reviewed the diffs and ran the app; teammate PR review pending |
| 2026-10-10 | Claude Code (Claude Opus 5.5) | Implemented chunking A/B, bge-m3 + Chroma index, re-chunk/orphan check, hybrid retrieval + reranker, PDF path, evaluation harness | `rag/`, `ingest/pdfs.py`, `evaluation/run.py`, `evaluation/report.py` | Deep Konkayala; unit tests (27) pass; teammate PR review pending |
| 2026-10-10 | Claude Code (Claude Opus 5.5) | **Drafted** all 46 golden-set items from corpus pages (question, gold answer, evidence needles, quote) | `evaluation/golden.jsonl` | **Not yet verified** — each item needs a teammate to check it against the live page and set `verified_by` |
