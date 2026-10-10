# Report 02 — Chunking, Indexing and Re-chunking

**MSAI 633 Residency · Day 2 · October 10, 2026** · stages 3–6 · code in `rag/chunking.py`, `rag/index.py` ·
verification evidence in `reports/evidence/indexing/`

## 1. Two strategies

Both read only the saved `data/genshin/normalized/docs.jsonl` (no network), drop the same low-value sections (translations, galleries,
voice-overs, patch logs, "See Also"…) and render tables the same way, one row per line as `label — column: value; …`.
So the comparison isolates **where the boundaries fall**. Token counts use the embedding model's own tokenizer (bge-m3).

| | **A — fixed-size** | **B — structure-aware** |
|---|---|---|
| Unit | 512-token sliding windows over the page text, 64-token overlap (step 448) | one section (heading path) at a time; small sibling sections under the same H2 are merged up to 512 tokens |
| Headings | ignored; a window can start mid-sentence or mid-table | the heading path (`Title > H2 > H3`) is the first line of every chunk |
| Tables | cut wherever the window ends | split by row groups, **with the header row repeated** in every piece |
| Chunk ID | `{doc_id}#A#{seq:04d}` | `{doc_id}#B#{seq:04d}` |

`doc_id` is the page-title slug plus a hash, so IDs are deterministic: the same `docs.jsonl` always produces the same IDs.

## 2. What they produce

| Statistic (`reports/evidence/indexing/chunk_stats.json`) | A | B |
|---|---:|---:|
| Chunks (337 documents) | 1,345 | 2,218 |
| Tokens: min · p25 · median · p75 · p95 · max | 65 · 511 · 512 · 512 · 513 · 513 | 14 · 86 · 226 · 454 · 505 · 512 |
| Total tokens | 597,632 | 567,509 |

- A is uniform by construction; its 513-token maximum comes from re-tokenising the sliced text (windows are 512).
- B is smaller and varied: 1.65× as many chunks, median 226 tokens. Its total is lower because A's 64-token overlaps count twice.
- **Structure checks on B:** 0 of 2,218 chunks fail to start with their heading path; 257 tables span more than one chunk, and
  0 of their row lines lack a header above them.
- **Overlap check on A:** all 1,008 consecutive window pairs overlap by exactly 64 tokens; the windows cover each document with
  nothing dropped at the end.

## 3. Comparison with real metrics

Retrieval on the human-verified golden set (dev split, 23 scored items), from report 04, with 95% bootstrap CIs:

| Retriever | Chunks | Recall@5 | Recall@20 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| dense | A | 0.707 [0.54, 0.85] | 0.739 [0.57, 0.89] | 0.750 [0.58, 0.90] | 0.684 [0.52, 0.84] |
| dense | B | 0.652 [0.48, 0.83] | 0.804 [0.65, 0.93] | 0.632 [0.46, 0.80] | 0.637 [0.49, 0.78] |
| BM25 | A | 0.663 [0.48, 0.83] | 0.739 [0.57, 0.89] | 0.534 [0.37, 0.70] | 0.539 [0.39, 0.68] |
| BM25 | B | 0.620 [0.43, 0.79] | 0.674 [0.50, 0.85] | 0.487 [0.32, 0.65] | 0.504 [0.35, 0.65] |

Paired dense A → dense B: ΔRecall@5 −0.054 [−0.16, +0.02], ΔMRR −0.118 [−0.27, +0.02], ΔRecall@20 +0.065 [−0.07, +0.22];
McNemar on "all evidence in the top 5": +1 / −1, p = 1.00. **No significant difference** at n = 23.

**What the direction says.**

- **B raises the ceiling and lowers the ranking.** More, smaller chunks put the right section in the 20-chunk pool more often
  (Recall@20 0.739 → 0.804), but each page now contributes several near-duplicate chunks that compete for the top ranks (MRR falls).
  In the full pipeline this is what we want: hybrid fusion lifts the pool to 0.826, and the cross-encoder reranker turns the pool back
  into a good top 5 (Recall@5 0.761, the best of all configurations — report 04).
- **BM25 does worse on B** on every metric: short structured chunks give exact-term matching fewer words to work with.
- **We keep B for the final system (B3)**: it preserves table headers and section context, which every cited answer needs, and its
  higher pool recall is what the reranker depends on. The retrieval cost of B shows up as a ranking problem, which the reranker solves.
- **A weakness common to both:** infobox chunks (a long list of `Field: value` lines) rank poorly, so infobox facts such as element or
  release date are hard to retrieve (report 04, section 6). A planned fix is to emit each infobox as its own short "key facts" chunk.

## 4. Embedding and vector store

| Item | Value |
|---|---|
| Model | `BAAI/bge-m3`, revision `5617a9f61b028005a4858fdac845db406aefb181`, 1024-d, vectors L2-normalised |
| Store | Chroma (persistent, local), cosine space; one collection per embedding model; both strategies in it, tagged `strategy` |
| Metadata | `strategy`, `doc_id`, `title`, `page_type`, `heading_path`, `url`, `crawled_at`, `effective_date` — `page_type` drives filtering, `url` the citations |
| Determinism | building B twice gives the identical 2,218-ID set (SHA-256 prefix `88b46b8272075e79`) and an unchanged store total of 3,563 |
| Filtering | `strategy=B, page_type=weapon` → top 5 all weapons; through the full pipeline, 0 out-of-filter chunks (report 04 §5) |
| Delete path | by chunk ID and by `doc_id`, each confirmed absent afterwards |

## 5. Re-chunk migration A → B, without re-crawling

`uv run python -m rag.index rechunk --old A --new B`:

1. Re-chunks from the saved `docs.jsonl` — **no network, no re-crawl**.
2. Embeds and upserts the B chunks, and removes any stale B IDs that are no longer produced.
3. **Deletes every A chunk** from the store.
4. Runs an orphan check: no chunk whose `doc_id` is not in the corpus, and no chunk ID that the current chunker would not produce.
5. Exits with an error if any A chunk remains, any B chunk is missing, or any orphan exists.

| Result (`reports/evidence/indexing/rechunk_A_to_B_2026-10-10.json`) | Value |
|---|---:|
| A chunks before → deleted → after | 1,345 → 1,345 → **0** |
| B chunks produced / indexed | 2,218 / 2,218 |
| Store total after | 2,218 (all B) |
| Orphan chunk IDs / orphan doc IDs | **0 / 0** |

The migration ran on a **copy** of the store (`CHROMA_DIR`), so the evaluated index, which keeps both strategies for the A/B
comparison (3,563 chunks, 0 orphans), was not modified.

**Independently reproduced.** The author ran it on a CUDA machine; a second teammate re-ran every check in this report from a clean
checkout of `main` on a CPU-only machine and got identical counts, token statistics, ID hash and re-chunk result (comment on #7).
Embedding time differs by hardware, not code: on CPU, embedding took about 34 min for A and 21 min for B (comment on #7); on CUDA,
the whole re-chunk run embedded B in 50.8 s (`rechunk_A_to_B_2026-10-10.json`).

## 6. Limitations

- n = 23 scored dev items: the A/B differences are within noise; the test split (report 06) is the confirmatory run.
- B's small chunks (minimum 14 tokens) can be a heading plus a single line, which helps pool recall but adds ranking noise.
- Character pages repeat talent tables that also exist on talent pages, so the same fact can appear in two chunks.
- The flattened *Talents* table on 16 character pages (report 01, section 7) is chunked as one run-on row in both strategies.
- `cmd_build` / `cmd_rechunk` write `artifacts/index_manifest.json` even when `CHROMA_DIR` points at a copy (noted in the evidence
  README); the content stayed correct here because the chunks were identical.

## 7. Reproduce

```bash
uv run python -m rag.chunking --strategy both                           # -> artifacts/chunks_A.jsonl, chunks_B.jsonl
uv run python -m rag.index build --strategy A && uv run python -m rag.index build --strategy B
uv run python -m rag.index status                                       # totals per strategy, orphan check
cp -r artifacts/chroma artifacts/chroma_rechunk
CHROMA_DIR=artifacts/chroma_rechunk uv run python -m rag.index rechunk --old A --new B
uv run python reports/evidence/indexing/verify_b.py                     # and the other scripts listed there
```
