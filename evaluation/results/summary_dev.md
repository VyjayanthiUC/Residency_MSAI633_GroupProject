# Evaluation summary — dev split

Golden set: 53 items; split seed 633, dev 32 / test 21. Verified by a human: 53.

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

## Generation (model `glm-5.3-flash`; mean [95% bootstrap CI])

| Config | n | Pass rate | Correct (answerable) | Correct refusal (unanswerable) | Over-refusal (answerable) | Citation valid | Unsupported numbers / answer | Spend advice given | p50 latency (s) | Tokens / query |
|---|---|---|---|---|---|---|---|---|---|---|
| B0 closed-book | 32 | 0.375 [0.22, 0.53] | 0.174 [0.04, 0.35] | 1.000 [1.00, 1.00] | 0.565 [0.35, 0.78] | n/a | nan | n/a | 1.81 | 147 |
| B3 hybrid/B+rerank | 32 | 0.844 [0.72, 0.97] | 0.783 [0.61, 0.91] | 1.000 [1.00, 1.00] | 0.043 [0.00, 0.13] | 0.773 [0.59, 0.95] | 0.03 | 0 | 1.65 | 1710 |
| B2 dense/A | 32 | 0.812 [0.66, 0.94] | 0.739 [0.57, 0.91] | 1.000 [1.00, 1.00] | 0.043 [0.00, 0.13] | 0.864 [0.73, 1.00] | 0.03 | 0 | 1.60 | 2336 |
| B1 bm25/A | 32 | 0.750 [0.59, 0.88] | 0.739 [0.57, 0.91] | 0.667 [0.33, 1.00] | 0.043 [0.00, 0.13] | 0.727 [0.55, 0.91] | 0.03 | 0 | 1.66 | 2417 |
| +struct dense/B | 32 | 0.750 [0.59, 0.88] | 0.739 [0.57, 0.91] | 0.667 [0.33, 1.00] | 0.043 [0.00, 0.13] | 0.727 [0.55, 0.91] | 0.03 | 0 | 1.55 | 1643 |
| +hybrid hybrid/B | 32 | 0.781 [0.62, 0.91] | 0.696 [0.52, 0.87] | 1.000 [1.00, 1.00] | 0.043 [0.00, 0.13] | 0.636 [0.45, 0.82] | 0.03 | 0 | 1.48 | 1628 |

| McNemar (exact, per-item pass/fail) | n | A fail → B pass | A pass → B fail | p |
|---|---|---|---|---|
| B2 dense/A → B3 hybrid/B+rerank | 32 | 1 | 0 | 1.000 |
| B0 closed-book → B3 hybrid/B+rerank | 32 | 16 | 1 | 0.000 |
| B1 bm25/A → B3 hybrid/B+rerank | 32 | 3 | 0 | 0.250 |

**On the items B0 (closed-book) got wrong:**

| Config | n | Pass rate |
|---|---|---|
| B0 closed-book | 20 | 0.000 [0.00, 0.00] |
| B3 hybrid/B+rerank | 20 | 0.800 [0.60, 0.95] |
| B2 dense/A | 20 | 0.800 [0.60, 0.95] |
| B1 bm25/A | 20 | 0.800 [0.60, 0.95] |
| +struct dense/B | 20 | 0.800 [0.60, 0.95] |
| +hybrid hybrid/B | 20 | 0.750 [0.55, 0.90] |

## B3 failures (for error analysis)

| Item | Category | Expected | Got (truncated) | Failure label (fill in) |
|---|---|---|---|---|
| sh06 | single_hop | It is a 5-star Claymore. | It is a 5-star claymore [S1][S3]. | |
| mh01 | multi_hop | Version 7.0, officially titled "Everwinter Without Mercy." | The rerun ran in Version 7.0 [S1][S3]. The wiki snapshot doesn't give a special version title beyond "Version 7.0." | |
| mh04 | multi_hop | Nightweaver's Looking Glass, with 542 base ATK at level 90. | Nightweaver's Looking Glass runs alongside Moonsong of the Groves [S1][S2]. The wiki snapshot doesn't include its base ATK at level 90. | |
| mh06 | multi_hop | Illuga, released February 03, 2026. | Demonhunter's Dusk is Illuga's 4th Ascension Passive [S1][S2]. However, the wiki snapshot does not contain Illuga's release date, so I can't answer that part. | |
| unans07 | adversarial | There is no Pyro-Dendro Resonance; each Elemental Resonance (except Protective Canopy) requires two or more characters of the same element. | I don't have that information in the wiki snapshot. | |
