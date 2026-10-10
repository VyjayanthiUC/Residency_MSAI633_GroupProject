# Report 06 — Final Performance

**MSAI 633 Residency · Day 2 · October 10, 2026** · **dev split only.** The test split has not been run; it runs once on
Sunday after the configuration is frozen, and its results will be added as a separate section.

## 1. Setup

| | |
|---|---|
| Golden set | 53 items, all human-verified (`evaluation/golden.jsonl`); split seed 633, dev 32 / test 21, stratified by category |
| Dev items by expected behavior | 23 answer · 6 refuse · 2 no spend advice · 1 no injection |
| Generation model | `glm-5.3-flash` (Zhipu), called through the Z.ai API, `temperature=0`, `reasoning_effort=low` |
| Index | chunks A 1,345 + B 2,218 = 3,563, 0 orphans; `BAAI/bge-m3` embeddings, `BAAI/bge-reranker-v2-m3` reranker |
| Retrieval | `K_POOL` 20 → `K_FINAL` 5; B3 refuses without an LLM call when the top rerank score < 0.52 (Report 04 §4) |
| Hardware | CPU only (AMD Ryzen Z2 Extreme); all latencies are CPU latencies |

**Configurations.** B0 closed-book (same model, no retrieval); B1 BM25 over fixed-size chunks (A); B2 dense over A; then one change
at a time: structure-aware chunks (B) → hybrid fusion → reranker + refusal gate = B3, the final system.

**Scoring** (`evaluation/run.py`, automatic, per item):

- *answer* items pass when the answer is not a refusal and contains every answer key (number- and word-boundary aware).
- *refuse* items pass on a refusal (or, for adversarial items, a clarifying question without citations).
- *no spend advice* items pass when the answer recommends no spending; the *no injection* item passes when the planted instruction is
  not followed and the system prompt is not leaked.
- Citation valid: the answer cites at least one source, and at least one cited chunk satisfies an evidence requirement of the item.

## 2. Results

Mean over the 32 dev items, [95% bootstrap CI] (10,000 resamples, seed 633).

| Config | Pass rate | Correct (answerable, n=23) | Correct refusal (unanswerable, n=6) | Over-refusal (answerable) | Citation valid |
|---|---|---|---|---|---|
| B0 closed-book | 0.375 [0.22, 0.56] | 0.130 [0.00, 0.26] | 1.000 | 0.696 [0.52, 0.87] | n/a |
| B1 BM25 / A | 0.719 [0.56, 0.88] | 0.696 [0.52, 0.87] | 0.667 [0.33, 1.00] | 0.043 [0.00, 0.13] | 0.727 [0.55, 0.91] |
| B2 dense / A | 0.781 [0.62, 0.91] | 0.739 [0.57, 0.91] | 0.833 [0.50, 1.00] | 0.043 [0.00, 0.13] | 0.818 [0.64, 0.95] |
| + structure-aware chunks (B) | 0.719 [0.56, 0.88] | 0.739 [0.57, 0.91] | 0.500 [0.17, 0.83] | 0.043 [0.00, 0.13] | 0.727 [0.55, 0.91] |
| + hybrid fusion | 0.750 [0.59, 0.88] | 0.739 [0.57, 0.91] | 0.667 [0.33, 1.00] | 0.043 [0.00, 0.13] | 0.727 [0.55, 0.91] |
| **B3 + reranker + refusal gate** | **0.812 [0.66, 0.94]** | **0.739 [0.57, 0.91]** | **1.000** | **0.043 [0.00, 0.13]** | **0.864 [0.73, 1.00]** |

No configuration recommended spending on the two spend-advice items. Unsupported numbers per answer (numbers that do not appear
verbatim in the cited sources): 0.03 for every RAG configuration except B1 (0.09).

**Paired tests** (exact McNemar on per-item pass/fail):

| Comparison | A fail → B pass | A pass → B fail | p |
|---|---|---|---|
| B0 → B3 | 14 | 0 | < 0.001 |
| B1 → B3 | 3 | 0 | 0.25 |
| B2 → B3 | 2 | 1 | 1.00 |

**What the numbers say.**

- **Retrieval is what makes the system work.** B0 → B3 is the only significant difference (14 items fixed, none broken).
- **B2 → B3 is not significant on 32 items.** The gain is concentrated in *refusal*: B3 refuses all 6 unanswerable items, and all 6
  are stopped by the rerank-score gate before any LLM call; B2 answers one of them (syn05), and the no-reranker B configurations answer
  two or three. Correctness on answerable items is identical (17 of 23) for B2 and the three B-chunk configurations. We report this as a
  consistent direction, not a proven gain.
- **Over-refusal stays at 1 of 23** for every RAG configuration; the refused item is the same in all of them (unans07, §5).

## 3. B0 leakage: what the model already knew

B0 answers 3 of 23 answerable dev items correctly from memory, refuses 16 (the closed-book prompt tells it to refuse when unsure) and
answers 4 wrongly. The 3 items it knew do not measure retrieval, so we also report every configuration on the 20 dev items B0 got wrong:

| Config | Pass rate on B0-incorrect items (n=20) |
|---|---|
| B0 | 0.000 |
| B1 | 0.700 [0.50, 0.90] |
| B2 | 0.750 [0.55, 0.90] |
| + structure-aware chunks | 0.750 [0.55, 0.90] |
| + hybrid | 0.750 [0.55, 0.90] |
| B3 | 0.700 [0.50, 0.90] |

On this subset B3 is not ahead of B2: its advantage on the full set comes from refusing unanswerable items, which B0 also "gets right" by
refusing, so those items drop out of the subset.

## 4. Latency and cost

| Config | Retrieval p50 / p95 (s) | Generation p50 / p95 (s) | LLM calls (of 32) | Tokens / query | Cost / query |
|---|---|---|---|---|---|
| B0 | — | 2.01 / 8.68 | 32 | 156 | $0.00005 |
| B1 | 0.00 / 0.00 | 1.75 / 3.05 | 32 | 2,401 | $0.00038 |
| B2 | 0.14 / 0.20 | 1.58 / 4.02 | 32 | 2,310 | $0.00037 |
| + structure-aware chunks | 0.13 / 0.16 | 1.69 / 5.27 | 32 | 1,622 | $0.00027 |
| + hybrid | 0.14 / 0.20 | 1.55 / 3.53 | 32 | 1,609 | $0.00026 |
| B3 | 15.14 / 18.70 | 1.73 / 2.75 | 22 | 1,697 | $0.00019 |

- Retrieval latency comes from `evaluation/results/retrieval_dev.json` (23 items with evidence); generation latency from
  `generation_dev.json`. End-to-end latency is the sum.
- **The reranker dominates B3's latency on CPU**: about 15 s per query for scoring 20 candidates with `bge-reranker-v2-m3`. This
  is the main cost of the reranker and the first thing a GPU deployment would remove; we did not measure GPU latency.
- Cost uses OpenRouter's list price for `z-ai/glm-5.3-flash` ($0.15 / M input, $0.50 / M output tokens); our runs went through a
  flat-rate Z.ai subscription. B3 is the cheapest RAG configuration because the refusal gate skips 10 of 32 LLM calls and
  structure-aware chunks are shorter.

## 5. Scoring caveats (to be resolved by hand-labeling)

Six dev items fail under B3. Reading them, two failures are artefacts of automatic scoring rather than wrong answers:

| Item | B3 answer | Why it failed automatically |
|---|---|---|
| sh06 | "a 5-star claymore", which is correct | answer key is "5 Stars"; the answer says "5-star" |
| cmp04 | "Tartaglia was released earlier", which is correct | answer key also requires "November 11, 2020", which the question does not ask for |
| mh01, mh04, mh06 | answers the first hop, says the second fact is not in the snapshot | genuine: the second-hop page was not retrieved (Report 04 §6) |
| unans07 | full refusal | genuine: the question has a false premise and should have been corrected; the reranker pushed the relevant chunk below the refusal gate |

We do **not** edit answer keys after seeing system outputs, since that would tune the golden set to the system. Instead, every failure is
hand-labeled (≥ 15 failures, the assignment's 10 categories) and the final report shows the automatic pass rate next to the
human-adjudicated one, listing every item where they differ.

## 6. Metric verification

The metric code is unit-tested on synthetic cases (`tests/test_evaluation.py`: Recall@k, MRR, nDCG, bootstrap CI, McNemar). We also
recomputed Recall@5 and MRR by hand for three real dev items under B3, matching each of the top-5 chunks against the evidence needles:

| Item | Case | By hand (Recall@5 / MRR) | Harness |
|---|---|---|---|
| sh05 | single hop, evidence at rank 1 | 1.000 / 1.000 | 1.000 / 1.000 |
| sh11 | single hop, evidence at rank 2 | 1.000 / 0.500 | 1.000 / 0.500 |
| mh01 | multi hop, 1 of 2 requirements met, at rank 3 | 0.500 / 0.333 | 0.500 / 0.333 |

## 7. Test split

Not run yet. It runs once, on Sunday, after the configuration (model, prompts, K values, refusal threshold, chunking) is frozen.

## 8. Reproduce

```bash
# .env: either LLM_API_KEY (OpenRouter, model z-ai/glm-5.3-flash) or ZAI_API_KEY + GLM_BASE_URL + GLM_MODEL=glm-5.3-flash
uv run python -m evaluation.run generation --split dev --max-calls 400 \
  --configs "B3 hybrid/B+rerank" "B2 dense/A" "B0 closed-book" "B1 bm25/A" "+struct dense/B" "+hybrid hybrid/B"
uv run python -m evaluation.run report --split dev    # -> evaluation/results/summary_dev.md
```

Answers are cached per (endpoint, model, config, item, sources, prompt) under `artifacts/llm_cache/`, so a re-run with the same settings
makes no new LLM calls. The first run stopped once on an API timeout (B3, item 30 of 32); the re-run resumed from the cache.
