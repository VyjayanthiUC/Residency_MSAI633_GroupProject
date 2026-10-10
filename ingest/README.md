# ingest/ — stages 1–2 (scrape → extraction)

The crawler and extractor that produced `data/genshin/` live here. Everything downstream reads only their output
files, so the format below is the contract: keep it, or update `rag/chunking.py` in the same PR.

## Reproduce the corpus

| Step | Command | Reads → writes | Network |
|---|---|---|---|
| 0. Get the dump | Fandom's official current-pages XML dump of the wiki, `gensinimpact_pages_current.xml.7z` (generated 2026-09-30; 61 MB, 565 MB unpacked), then `7z x` | — | yes (once) |
| 1. Index the dump | `python ingest/dump_to_sqlite.py <dump.xml> ns0.sqlite` | dump → `ns0.sqlite` (not committed, ~220 MB) | no |
| 2. Select pages | `python ingest/select_pages.py ns0.sqlite` | `ns0.sqlite` → `data/genshin/selection.tsv` | no |
| 3. Crawl | `uv run python ingest/crawl.py` (core tier; `--tiers all` adds lore pages) | `selection.tsv` → `raw/<sha256>.json` + `manifest.jsonl` | yes, ≤1 req/s |
| 4. Extract | `uv run python ingest/extract.py` | `raw/` + `manifest.jsonl` → `normalized/` | no |

- **Step 4 is deterministic**: re-running it on the committed `raw/` reproduces `normalized/` byte for byte
  (verified 2026-10-10 — `git diff` is empty afterwards).
- **Step 3 is resumable**: titles already in `manifest.jsonl` are skipped, so re-running it on the committed snapshot
  makes no page requests (it still fetches `robots.txt` once). It parses `robots.txt` in code (`urllib.robotparser`), falls back to
  `data/genshin/robots.snapshot.txt` when the live file is blocked, and records which one was used per page.
- The exact download URL of the dump was not recorded at the time; the file name and generation date identify it.
- `selection.tsv` lists all 603 candidate pages; the committed snapshot is the **core tier (337 pages)**.
- Snapshot statistics (from `normalized/extract_report.json`): 337 documents, 854 table blocks, 3,891 text blocks,
  ~2.5M characters, 0 duplicates; `effective_date` from the page itself 68, inherited 260, missing 9.

## Outputs (committed snapshot in `data/genshin/`)

`manifest.jsonl` — one line per fetched page:

| Field | Meaning |
|---|---|
| `title`, `page_type`, `source_url` | page identity; `page_type` drives metadata filtering |
| `fetch_url`, `fetched_at`, `http_status`, `api_error` | what was requested, when, and the outcome |
| `sha256`, `bytes` | raw response stored as `raw/<sha256>.json` |
| `robots_source` | `live` or `snapshot (…)` — which robots.txt was checked |

`normalized/docs.jsonl` — one line per page:

| Field | Meaning |
|---|---|
| `doc_id` | stable ID (title slug + hash); prefix of every chunk ID |
| `title`, `page_type`, `source_url`, `crawled_at`, `revid` | provenance |
| `raw_sha256`, `content_hash` | link to raw bytes; dedupe key |
| `effective_date`, `effective_date_source` | game-version date the content applies to (`null` = undated) |
| `blocks[]` | `{heading_path: [title, h2, h3…], kind: "infobox" \| "text" \| "table", text, pairs?, table?: {headers, rows}}` |

Tables must stay structured (`headers` + `rows`); chunking renders each row as `label — Lv1: …; Lv2: …`.

## Known issue to fix here

The *Talents* table on character pages is nested (a tabbed box of Description / Gameplay Notes / Advanced Properties /
Attribute Scaling / Preview inside one cell), and `extract.py` flattens it into a single run-on cell. Example: in
`docs.jsonl`, the block `Lauma > Gameplay Info > Talents` has a row whose first cell starts with
`Description Gameplay Notes Advanced Properties Attribute Scaling Preview Normal Attack …`.
The talent pages carry the same data as clean tables, so the planned fix is to skip that table on character pages.
Fixing it changes `normalized/` for the 18 character pages, so chunks, the index, and any evaluation numbers must be
rebuilt afterwards — do it before the golden set is frozen.

## PDF path

`uv run python -m ingest.pdfs` prints selected crawled pages to PDF with headless Edge/Chrome from the saved raw HTML,
extracts them with pdfplumber and compares against the HTML extraction (`artifacts/pdf/comparison.json`).
