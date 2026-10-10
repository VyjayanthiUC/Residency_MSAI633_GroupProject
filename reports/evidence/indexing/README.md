# Indexing verification (Epic 2, issues 2.1–2.5) — 2026-10-10

Run on the current code (after `6ceed39`) against the 337 saved docs in `data/genshin/normalized/docs.jsonl`.
Store checks ran on **copies** of `artifacts/chroma` (via `CHROMA_DIR`) so the evaluated index was not modified.
Run each script from the repo root: `uv run python reports/evidence/indexing/<script>.py`.
`verify_store.py` deletes chunks, so it refuses to run on the evaluated index; point it at a copy:

```bash
cp -r artifacts/chroma artifacts/chroma_verify
CHROMA_DIR=artifacts/chroma_verify uv run python reports/evidence/indexing/verify_store.py
```

The re-chunk run used a copy the same way: `CHROMA_DIR=<copy> uv run python -m rag.index rechunk --old A --new B`.

| Issue | Check | Result | Script / file |
|---|---|---|---|
| 2.1 Chunking A | chunk count, token lengths | 1,345 chunks; min 65 · p25 511 · median 512 · p75 512 · p95 513 · max 513 | `chunk_stats.json` |
| 2.1 | overlap of consecutive windows (recomputed exactly as `chunk_fixed`) | all 1,008 pairs = 64 tokens (step 448) | `verify_a_raw.py` |
| 2.1 / 2.2 | re-run `rag.chunking` | `chunks_A.jsonl` and `chunks_B.jsonl` byte-identical to the previous build | — |
| 2.2 Chunking B | first line = `title > heading_path` | 0 of 2,218 chunks differ | `verify_b.py` |
| 2.2 | split tables repeat header | 257 tables span >1 chunk; 0 row lines without their header above them | `verify_b.py` |
| 2.3 Embedding | model / revision / dim | `BAAI/bge-m3` @ `5617a9f61b028005a4858fdac845db406aefb181`, 1024-d, fp16 CUDA | `artifacts/index_manifest.json` |
| 2.3 | L2 norms of stored vectors | 3,563 vectors, norm 0.99976–1.00050 | `verify_a_and_embed.py` |
| 2.3 | metric | collection `hnsw.space = cosine`; Chroma distance = 1 − dot within 2e-4 | `verify_a_and_embed.py` |
| 2.4 Vector store | build B twice | identical 2,218-ID sets (sha256 prefix `88b46b8272075e79`), store total unchanged at 3,563 | `verify_store.py` |
| 2.4 | filter | `strategy=B, page_type=weapon` → top 5 all weapon; `page_type=talent` → 728 | `verify_store.py` |
| 2.4 | delete | by ID: 1 removed, absent afterwards; by `doc_id`: 17 removed, 0 remain | `verify_store.py` |
| 2.5 Re-chunk | `rag.index rechunk --old A --new B` | A 1,345 → 0; store 2,218 (all B); 0 orphan chunk IDs; 0 orphan doc IDs | `rechunk_A_to_B_2026-10-10.json` |

Notes:
- Max 513 tokens for A comes from re-tokenizing the sliced text; windows are 512 tokens.
- `cmd_build`/`cmd_rechunk` write `artifacts/index_manifest.json` regardless of `CHROMA_DIR`, so runs on a copy update the
  main manifest (content stayed correct here because the chunks are identical).
- A→B evaluation delta (2.5): see report 04 §2, measured on the human-verified 53-item golden set (23 scored dev items).
  Dense A → dense B: ΔRecall@5 −0.054 [−0.16, +0.02], ΔMRR −0.118 [−0.27, +0.02], ΔRecall@20 +0.065 [−0.07, +0.22];
  McNemar +1 / −1, p = 1.00 — no significant difference. B raises pool recall but lowers ranking; the reranker (B3)
  recovers the top 5.
