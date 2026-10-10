# MSAI 633 Residency — Retrieval-Augmented Chatbot

Team project for MSAI 633 (Ethics in Artificial Intelligence), Fall 2026 residency, October 9–11.

We are building a chatbot that answers real user questions using **only** content scraped from one public website.
Every factual claim cites the page it came from, and when the corpus does not support an answer, the chatbot says so instead of guessing.

> **Status:** project kickoff. Domain, corpus plan, and stack are defined in the Day 1 proposal (`reports/00_proposal.md`).

## Team

| Member | GitHub | Role |
|---|---|---|
| | @VyjayanthiUC | |
| | @ibkcode | |
| | @ShyamalaKeerthi | |
| | @oyinakpe2-firstgrandprince | |
| Li, Yanwei | @Saweisra | |

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
- **Never commit secrets or scraped data.** `.env` and raw/processed data stay local and are git-ignored.
- **Track work in Issues** — each pipeline stage and each report has an owner.

## Setup

_To be added with the first code commit: environment, dependencies, and the commands that reproduce every reported number._

## AI usage

AI tools are allowed and documented here at every milestone: which tool, what it was used for, on which artifact, and who checked it.

| Date | Tool | Used for | Artifact | Human check |
|---|---|---|---|---|
| | | | | |
