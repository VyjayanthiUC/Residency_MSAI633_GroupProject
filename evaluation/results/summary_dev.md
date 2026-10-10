# Evaluation summary — dev split

Golden set: 51 items; split seed 633, dev 31 / test 20. Verified by a human: 51.

## Retrieval (mean [95% bootstrap CI])

| Config | n | Recall@5 | Recall@20 | MRR | nDCG@10 | p50 / p95 latency (s) |
|---|---|---|---|---|---|---|
| B1 bm25/A | 23 | 0.663 [0.48, 0.83] | 0.739 [0.57, 0.89] | 0.534 [0.37, 0.70] | 0.539 [0.39, 0.68] | 0.00 / 0.00 |
| B2 dense/A | 23 | 0.707 [0.54, 0.85] | 0.739 [0.57, 0.89] | 0.750 [0.58, 0.90] | 0.684 [0.52, 0.84] | 0.14 / 0.20 |
| +struct dense/B | 23 | 0.652 [0.48, 0.83] | 0.804 [0.65, 0.93] | 0.632 [0.46, 0.80] | 0.637 [0.49, 0.78] | 0.13 / 0.16 |
| +hybrid hybrid/B | 23 | 0.717 [0.54, 0.87] | 0.826 [0.70, 0.93] | 0.583 [0.41, 0.75] | 0.583 [0.43, 0.73] | 0.14 / 0.20 |
| B3 hybrid/B+rerank | 23 | 0.761 [0.59, 0.91] | 0.826 [0.70, 0.93] | 0.699 [0.53, 0.85] | 0.693 [0.53, 0.84] | 15.14 / 18.70 |
| (extra) bm25/B | 23 | 0.620 [0.43, 0.79] | 0.674 [0.50, 0.85] | 0.487 [0.32, 0.65] | 0.504 [0.35, 0.65] | 0.00 / 0.01 |

Reranker lift (B3, Recall@5 post vs pre-rerank on the same pool): 0.761 vs 0.717; Recall@20 ceiling 0.826.

## Retrieval ablation (paired, one change per step)

| Step | n | ΔRecall@5 | ΔMRR | ΔRecall@20 | McNemar: all evidence in top 5 (gained / lost, p) |
|---|---|---|---|---|---|
| B1 bm25/A → B2 dense/A | 23 | +0.043 [-0.09, +0.17] | +0.216 [+0.04, +0.39] | +0.000 [-0.17, +0.15] | +1 / −1, p = 1.00 |
| B2 dense/A → +struct dense/B | 23 | -0.054 [-0.16, +0.02] | -0.118 [-0.27, +0.02] | +0.065 [-0.07, +0.22] | +1 / −1, p = 1.00 |
| +struct dense/B → +hybrid hybrid/B | 23 | +0.065 [-0.04, +0.22] | -0.049 [-0.14, +0.02] | +0.022 [-0.07, +0.13] | +2 / −0, p = 0.50 |
| +hybrid hybrid/B → B3 hybrid/B+rerank | 23 | +0.043 [-0.09, +0.17] | +0.116 [-0.01, +0.26] | +0.000 [+0.00, +0.00] | +2 / −1, p = 1.00 |
| B2 dense/A → B3 hybrid/B+rerank | 23 | +0.054 [-0.07, +0.21] | -0.051 [-0.18, +0.06] | +0.087 [-0.07, +0.26] | +3 / −0, p = 0.25 |
| B1 bm25/A → B3 hybrid/B+rerank | 23 | +0.098 [-0.08, +0.27] | +0.165 [-0.01, +0.34] | +0.087 [+0.00, +0.22] | +4 / −1, p = 0.38 |

## Refusal threshold (tuned on dev)

Top rerank score threshold 0.5396: catches 100% of unanswerable dev items before generation, refuses 4% of answerable dev items.
