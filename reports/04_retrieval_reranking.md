# Report 04 — Retrieval and Reranking

**MSAI 633 Residency · Day 2 · October 10, 2026** · dev split only (the test split has not been run)

## 1. What we built

| Stage | Implementation (`rag/retrieval.py`) | Setting |
|---|---|---|
| BM25 | `rank_bm25.BM25Okapi` over title + heading path + chunk text | — |
| Dense | `BAAI/bge-m3` embeddings (1024-d, L2-normalised) in Chroma, cosine | — |
| Hybrid | Reciprocal Rank Fusion, score = Σ 1 / (k + rank), each ranker cut at `FUSION_DEPTH` | k = 60, depth = 30 |
| Candidate pool | BM25, dense, or hybrid | `K_POOL` = 20 |
| Reranker | Cross-encoder `BAAI/bge-reranker-v2-m3` (sigmoid score) over the 20 candidates | `K_FINAL` = 5 |
| Refusal gate | Refuse without calling the LLM when the top rerank score < `REFUSE_BELOW` | 0.52 |
| Metadata filter | `page_types` → Chroma `where` clause (dense) and a post-filter (BM25), applied before fusion | optional |

**Relevance label.** A chunk satisfies an evidence requirement when it comes from the named page *and* contains every needle string
from the golden item. Chunk IDs differ between chunking strategies A and B, so IDs cannot be the gold label (`evaluation/golden.py`).
Recall@k is the fraction of an item's evidence requirements met in the top k; multi-hop and comparative items have two requirements.

**Setup.** Golden set 51 items, all human-verified; split seed 633, dev 31 / test 20. Of the 31 dev items, 23 have evidence and are
scored for retrieval; the other 8 (6 unanswerable, 1 injection, 1 spend-advice) have nothing to retrieve and are used only for the
refusal threshold. Index: A 1,345 + B 2,218 = 3,563 chunks, 0 orphans. Hardware: CPU only (AMD Ryzen Z2 Extreme), so latencies are
CPU latencies.

## 2. Results — six configurations, one change at a time

Mean over 23 dev items, [95% bootstrap CI], 10,000 resamples, seed 633.

| Config | Recall@5 | Recall@20 (pool) | MRR | nDCG@10 | p50 / p95 latency (s) |
|---|---|---|---|---|---|
| **B1** BM25 / chunks A | 0.663 [0.48, 0.83] | 0.739 [0.57, 0.89] | 0.534 [0.37, 0.70] | 0.539 [0.39, 0.68] | 0.00 / 0.00 |
| **B2** dense / chunks A | 0.707 [0.54, 0.85] | 0.739 [0.57, 0.89] | 0.750 [0.58, 0.90] | 0.684 [0.52, 0.84] | 0.14 / 0.20 |
| + structure-aware chunks (dense / B) | 0.652 [0.48, 0.83] | 0.804 [0.65, 0.93] | 0.632 [0.46, 0.80] | 0.637 [0.49, 0.78] | 0.13 / 0.16 |
| + hybrid fusion (hybrid / B) | 0.717 [0.54, 0.87] | 0.826 [0.70, 0.93] | 0.583 [0.41, 0.75] | 0.583 [0.43, 0.73] | 0.14 / 0.20 |
| **B3** + reranker (hybrid / B + rerank) | **0.761** [0.59, 0.91] | 0.826 [0.70, 0.93] | 0.699 [0.53, 0.85] | 0.693 [0.53, 0.84] | 15.14 / 18.70 |
| (extra) BM25 / chunks B | 0.620 [0.43, 0.79] | 0.674 [0.50, 0.85] | 0.487 [0.32, 0.65] | 0.504 [0.35, 0.65] | 0.00 / 0.01 |

**Paired differences per step** (bootstrap CI over per-item deltas; exact McNemar on "all evidence in the top 5", pass/fail per item):

| Step | ΔRecall@5 | ΔMRR | ΔRecall@20 | McNemar (gained / lost, p) |
|---|---|---|---|---|
| B1 → B2 (BM25 → dense) | +0.043 [−0.09, +0.17] | **+0.216 [+0.04, +0.39]** | +0.000 [−0.17, +0.15] | +1 / −1, p = 1.00 |
| B2 → dense / B (chunking A → B) | −0.054 [−0.16, +0.02] | −0.118 [−0.27, +0.02] | +0.065 [−0.07, +0.22] | +1 / −1, p = 1.00 |
| dense / B → hybrid / B | +0.065 [−0.04, +0.22] | −0.049 [−0.14, +0.02] | +0.022 [−0.07, +0.13] | +2 / −0, p = 0.50 |
| hybrid / B → B3 (reranker) | +0.043 [−0.09, +0.17] | +0.116 [−0.01, +0.26] | +0.000 | +2 / −1, p = 1.00 |
| B2 → B3 (end to end) | +0.054 [−0.07, +0.21] | −0.051 [−0.18, +0.06] | +0.087 [−0.07, +0.26] | +3 / −0, p = 0.25 |
| B1 → B3 (end to end) | +0.098 [−0.08, +0.27] | +0.165 [−0.01, +0.34] | +0.087 [+0.00, +0.22] | +4 / −1, p = 0.38 |

**Reading the tables.**

- **Direction is consistent, significance is not.** Items with all evidence in the top 5 go 13 (B1) → 13 (B2) → 13 → 15 → 16 (B3).
  The only step whose CI excludes zero is B1 → B2 on MRR (+0.216): dense ranks the right chunk higher than BM25. Every Recall@5 step,
  including B2 → B3, is within noise at n = 23, so we do **not** claim that B3 beats B2. Our proposal's hypothesis is therefore
  not confirmed on dev; the test split (report 06) will be the confirmatory run.
- **Chunking B raises the ceiling but hurts the ranking.** Recall@20 rises 0.739 → 0.804, while MRR falls 0.750 → 0.632. B produces
  1.6× more, smaller chunks, so the right section is more often in the pool but has more near-duplicate competitors from the same
  page. Fusion adds a little more pool recall (0.826); the reranker is what turns that larger pool back into a good top 5.
- **BM25 is not a weak baseline here.** B1's Recall@5 is within 0.05 of B2's, in line with BEIR's finding (cited in our proposal)
  that BM25 stays competitive out of domain: game-specific names make exact-term matching strong. BM25 gets worse on chunks B
  (0.620), because short structured chunks give it fewer terms to match.
- **Nothing is removed.** No component, taken out, makes the system clearly better, so we keep the designed pipeline.

## 3. Reranker: lift, cost, and ceiling

- **Lift on the same pool:** Recall@5 0.717 before reranking → 0.761 after; MRR 0.583 → 0.699.
  Rescued: `sh11`, `sh12` (evidence at pool ranks > 5, moved into the top 5). Demoted: `unans07` (in the top 5 before, pushed out after).
- **Ceiling:** Recall@20 of the pool is 0.826, the most the reranker could reach. B3 reaches 0.761 of it. The remaining gap is items
  whose evidence never enters the pool (section 6), which no reranker can fix.
- **Cost:** +15.0 s p50 per query on CPU (0.14 s → 15.14 s; p95 18.70 s), for 20 query–chunk pairs at max length 1,024.
  This is the dominant latency of the whole retrieval stage. On a GPU the same model runs in fp16 (`rag/retrieval.py`); the live demo
  should run on a GPU machine. Lowering `K_POOL` or the max length would cut the cost, but we did not tune it.
- **Board item 3.4, "Lauma constellation 2"** (its answer sat at pool ranks 7 and 10 in the first chat prototype on 10-09):
  with the current chunker and pipeline the chunk holding her C2 is at rank 1 in B3 (rank 1–3 in every configuration we tried),
  so it is in the top 5. A natural phrasing, "What does Lauma's 2nd constellation do?", is also rank 1 but has a top rerank score of
  only 0.531, just above the refusal gate (`evaluation/results/retrieval_checks.json`).

## 4. Refusal threshold

`evaluation.run threshold --split dev` picks the threshold that best separates answerable from unanswerable dev items
(Youden's J, with over-refusal capped at 10%): **0.5396**, which catches 100% of unanswerable items (6/6) and refuses 4.3% of answerable
ones (1/23). The score distribution has a wide gap: the highest unanswerable item scores 0.314 and every answerable item but one
scores ≥ 0.765. The configured 0.52 lies inside that gap and gives exactly the same dev outcome, so we keep it.

The one answerable item refused is `unans07`, a false-premise question ("Pyro-Dendro Resonance"): the expected behaviour is to correct
the premise from the Team Bonus page, but its top score is 0.10. It is counted as over-refusal.

## 5. Metadata filtering

`evaluation.retrieval_checks` runs three queries with and without a `page_types` filter (`weapon`, `character`, `mechanic`) through
BM25, dense, and hybrid + rerank on chunks B: **0 out-of-filter chunks across all filtered pools, and the target page is in the top 5
of every filtered run.** The filter also fixes one case: dense retrieval for "Lauma constellation 2" misses her page in the top 5
without a filter and ranks it first with `page_types=["character"]`. The vector-store level filter was verified separately under #21.

## 6. Retrieval failures (B3, dev)

Seven of the 23 scored items do not have all their evidence in the top 5. Six of them fail in **every** configuration.

| Item | Category | What happened | Label |
|---|---|---|---|
| `cmp03`, `mh03` | comparative, multi-hop | Need `Element: Pyro` / `Element: Dendro` from the character infobox. The right pages are in the top 5, but the infobox chunk is not; Arlecchino's infobox chunk is not even in a 50-chunk hybrid pool* | chunk boundary / rank failure |
| `cmp04` | comparative | Needs both release dates from infoboxes; they sit at hybrid pool ranks 10 and 24* | rank failure |
| `mh01` | multi-hop | Second hop (`Version/7.0`, the version title) never retrieved — the question names the event wish, not the version | retrieval miss |
| `mh04` | multi-hop | Second hop (weapon page *Nightweaver's Looking Glass*) never retrieved — the question does not name the weapon | retrieval miss |
| `mh06` | multi-hop | Gets the Illuga and Lunar-Crystallize pages but not the one sentence the golden item accepts; the item may be scored too strictly (it allows one source) | scoring strictness (golden set unchanged) |
| `unans07` | adversarial | Reranker pushes the Team Bonus chunk out of the top 5 (top score 0.10), so the item is refused | reranker demotion / over-refusal |

\* Manual diagnostic (`Pipeline("B", "hybrid", rerank=False).retrieve(question, 50)`), not part of the committed scripts.

**Two patterns.** (1) **Infobox facts are hard to retrieve.** An infobox chunk is a long list of `Field: value` lines: its embedding
is diffuse, and for BM25 the field names ("Element", "Release Date") occur on every character page. (2) **Second hops** that the
question does not name are out of reach for single-shot retrieval.

## 7. Limitations and future work

- n = 23 scored dev items: differences of one or two items are noise; confirmatory numbers come from the single test run (report 06).
- One golden-set evidence alternative per requirement can under-credit valid retrievals (`mh06`).
- Latency is measured on CPU only.
- **Infobox chunks:** emit each infobox as its own short "key facts" chunk (or prepend a one-line page summary) so field lookups
  stop competing with prose.
- **Multi-hop:** decompose the question and retrieve per hop, using the metadata filter for the second hop (e.g. `page_types=["weapon"]`).
- **Reranker cost:** tune `K_POOL` and max length on dev, or rerank on GPU.

## 8. Reproduce

```bash
uv run python -m rag.index build --strategy A && uv run python -m rag.index build --strategy B   # if the index is not built
uv run python -m evaluation.run retrieval --split dev     # -> evaluation/results/retrieval_dev.json (6 configs)
uv run python -m evaluation.run threshold --split dev     # -> evaluation/results/threshold_dev.json
uv run python -m evaluation.retrieval_checks              # -> evaluation/results/retrieval_checks.json (filter, Lauma C2)
uv run python -m evaluation.run report --split dev        # -> evaluation/results/summary_dev.md (tables above, with CIs)
```

Retrieval runs make no LLM calls. Measured on main `d10f264`.
