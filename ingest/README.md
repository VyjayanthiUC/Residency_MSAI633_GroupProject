# ingest/ — stages 1–2 (scrape → extraction)

**Owner: crawl / extraction (Yanwei Li).** The crawler and extractor that produced `data/genshin/` belong here
(e.g. `ingest/crawl.py`, `ingest/extract.py`) — they are not committed yet. Everything downstream reads only their
output files, so the format below is the contract: keep it, or update `rag/chunking.py` in the same PR.

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

The *Talents* table on character pages is nested; its cells are flattened into run-on text in `docs.jsonl`
(see `reports/01_ingestion.md` §3). Either expand nested tables or skip that table on character pages
(the talent pages carry the same data cleanly).

## PDF path

`uv run python -m ingest.pdfs` prints selected crawled pages to PDF with headless Edge/Chrome from the saved raw HTML,
extracts them with pdfplumber and compares against the HTML extraction (`artifacts/pdf/comparison.json`).
