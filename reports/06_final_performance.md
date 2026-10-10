# Report 06 — Final Performance

**MSAI 633 Residency · Day 2 · October 10, 2026** · **dev split only.** The test split has not been run; it runs once on
Sunday after the configuration is frozen, and its results will be added as a separate section.

## 1. Setup

| | |
|---|---|
| Golden set | 53 items, all human-verified (`evaluation/golden.jsonl`); split seed 633, dev 32 / test 21, stratified by category |
| Dev items by expected behavior | 23 answer · 6 refuse · 2 no spend advice · 1 no injection |
| Generation model | `glm-5.3-flash` (Zhipu), called through the Z.ai API, `temperature=0`, `reasoning_effort=low`; prompts as on main after PR #87 |
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
| B0 closed-book | 0.375 [0.22, 0.53] | 0.174 [0.04, 0.35] | 1.000 | 0.565 [0.35, 0.78] | n/a |
| B1 BM25 / A | 0.750 [0.59, 0.88] | 0.739 [0.57, 0.91] | 0.667 [0.33, 1.00] | 0.043 [0.00, 0.13] | 0.727 [0.55, 0.91] |
| B2 dense / A | 0.812 [0.66, 0.94] | 0.739 [0.57, 0.91] | 1.000 | 0.043 [0.00, 0.13] | 0.864 [0.73, 1.00] |
| + structure-aware chunks (B) | 0.750 [0.59, 0.88] | 0.739 [0.57, 0.91] | 0.667 [0.33, 1.00] | 0.043 [0.00, 0.13] | 0.727 [0.55, 0.91] |
| + hybrid fusion | 0.781 [0.62, 0.91] | 0.696 [0.52, 0.87] | 1.000 | 0.043 [0.00, 0.13] | 0.636 [0.45, 0.82] |
| **B3 + reranker + refusal gate** | **0.844 [0.72, 0.97]** | **0.783 [0.61, 0.91]** | **1.000** | **0.043 [0.00, 0.13]** | **0.773 [0.59, 0.95]** |

No configuration recommended spending on the two spend-advice items, and none followed the planted injection. Unsupported numbers per
answer (numbers that do not appear verbatim in the cited sources): 0.03 for every RAG configuration.

**Paired tests** (exact McNemar on per-item pass/fail):

| Comparison | A fail → B pass | A pass → B fail | p |
|---|---|---|---|
| B0 → B3 | 16 | 1 | < 0.001 |
| B1 → B3 | 3 | 0 | 0.25 |
| B2 → B3 | 1 | 0 | 1.00 |

**What the numbers say.**

- **Retrieval is what makes the system work.** B0 → B3 is the only significant difference: 16 items fixed, 1 broken (unans07, §5).
- **B2 → B3 differs on one item and is not significant.** The one item is cmp03 (the elements of two characters): B3 retrieves both
  characters' answers, while all four RAG configurations without the reranker answer only for Lauma. The five RAG configurations land
  between 16 and 18 correct answers out of 23. We report the direction, not a proven gain.
- **Every RAG configuration over-refuses the same single item** (unans07). B3 refuses all 6 unanswerable items without any LLM call:
  the rerank-score gate stops them first. B2 and the hybrid configuration also refuse all 6, through the LLM; BM25 and the
  structure-aware dense configuration answer two of them (unans02, syn05).
- **Citation validity does not follow pass rate.** B2 has the best citation validity (0.864) and the hybrid configuration the worst
  (0.636). A citation counts as valid only if a cited chunk satisfies the golden evidence needles, so an answer that cites the right page but a
  neighbouring chunk counts as invalid; hand-labeling (§5) separates the two cases.

## 3. B0 leakage: what the model already knew

B0 answers 4 of 23 answerable dev items correctly from memory, refuses 13 (the closed-book prompt tells it to refuse when unsure) and
answers 6 wrongly. It also passes all 6 unanswerable items by refusing, and passes unans07 by correcting the false premise from its own
knowledge. Items B0 already gets right do not measure retrieval, so we also report every configuration on the 20 dev items B0 got wrong:

| Config | Pass rate on B0-incorrect items (n=20) |
|---|---|
| B0 | 0.000 |
| B1 | 0.800 [0.60, 0.95] |
| B2 | 0.800 [0.60, 0.95] |
| + structure-aware chunks | 0.800 [0.60, 0.95] |
| + hybrid | 0.750 [0.55, 0.90] |
| B3 | 0.800 [0.60, 0.95] |

On the items the model did not know, every RAG configuration recovers about four out of five, and B3 is not ahead of B1 or B2.

## 4. Latency and cost

| Config | Retrieval p50 / p95 (s) | Generation p50 / p95 (s) | LLM calls (of 32) | Tokens / LLM call | Cost / query |
|---|---|---|---|---|---|
| B0 | — | 1.81 / 4.24 | 32 | 147 | $0.00005 |
| B1 | 0.00 / 0.00 | 1.66 / 2.71 | 32 | 2,417 | $0.00038 |
| B2 | 0.14 / 0.20 | 1.60 / 3.86 | 32 | 2,336 | $0.00037 |
| + structure-aware chunks | 0.13 / 0.16 | 1.55 / 4.81 | 32 | 1,643 | $0.00027 |
| + hybrid | 0.14 / 0.20 | 1.48 / 4.12 | 32 | 1,628 | $0.00027 |
| B3 | 15.14 / 18.70 | 1.65 / 3.10 | 22 | 1,710 | $0.00019 |

- Retrieval latency comes from `evaluation/results/retrieval_dev.json` (23 items with evidence); generation latency from
  `generation_dev.json`. End-to-end latency is the sum.
- **The reranker dominates B3's latency on CPU**: about 15 s per query for scoring 20 candidates with `bge-reranker-v2-m3`. This
  is the main cost of the reranker and the first thing a GPU deployment would remove; we did not measure GPU latency.
- Cost per query is averaged over all 32 items and uses OpenRouter's list price for `z-ai/glm-5.3-flash` ($0.15 / M input,
  $0.50 / M output tokens); our runs went through a flat-rate Z.ai subscription. B3 is the cheapest RAG configuration because the refusal
  gate skips 10 of 32 LLM calls and structure-aware chunks are shorter.

## 5. Scoring caveats (to be resolved by hand-labeling)

B3 fails five dev items. Reading every B3 answer, automatic scoring errs in both directions:

| Item | B3 answer | Automatic | By reading |
|---|---|---|---|
| sh06 | "a 5-star claymore" | fail: the answer key is "5 Stars" | correct |
| cmp04 | opens with the refusal sentence, gives Tartaglia's date, never says who was released earlier | pass: both answer keys appear and citations make it a partial answer | not an answer to the question |
| mh01, mh04, mh06 | answers the first hop, says the second fact is not in the snapshot | fail | genuine: the second-hop page was not retrieved (Report 04 §6) |
| unans07 | full refusal | fail | genuine: a false-premise question that should be corrected; B0 corrects it from memory, while retrieval finds no chunk above the refusal gate |

We do **not** edit answer keys after seeing system outputs, since that would tune the golden set to the system. Instead every failure is
hand-labeled with the assignment's categories (≥ 15 failures), and the final report shows the automatic pass rate next to the
human-adjudicated one, listing every item where they differ.

**Run-to-run variation.** The same model at `temperature=0` does not return identical answers: between our two dev runs (the second
after PR #87 added one line about Chinese refusals to the answer prompt), each RAG configuration's pass count moved by one item, and
cmp04's B3 answer changed wording and outcome. With 32 items, one item is 3 percentage points, which is part of why none of the
B1/B2/B3 differences is significant.

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
makes no new LLM calls.
