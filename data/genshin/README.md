# Genshin Impact Wiki — corpus snapshot (2026-10-10)

A frozen crawl of selected pages from the [Genshin Impact Fandom wiki](https://genshin-impact.fandom.com/),
scoped to the two newest regions (Nod-Krai and Snezhnaya, game versions 6.0–7.1).
It is committed so every teammate works from the **same snapshot** — no one needs to re-crawl the live site,
and every reported number can be reproduced against identical input.

## License and attribution

Content is from the Genshin Impact Wiki on Fandom, written by its contributors, and is licensed under
**[CC BY-SA](https://www.fandom.com/licensing)**. It is redistributed here unmodified (`raw/`) and in
normalized form (`normalized/`) under the same license. Each document records its source URL and revision ID.
Genshin Impact is a trademark of HoYoverse; this project is not affiliated with HoYoverse or Fandom.

## Contents

| Path | What it is |
|---|---|
| `manifest.jsonl` | One line per page: `title`, `page_type`, `source_url`, `fetch_url`, `fetched_at`, `http_status`, `sha256`, `bytes`, `robots_source` |
| `raw/<sha256>.json` | Raw MediaWiki API response (`action=parse`, rendered HTML), stored as fetched; file name = SHA-256 of the bytes |
| `normalized/docs.jsonl` | Extracted documents: `doc_id`, `source_url`, `title`, `page_type`, heading-path sections, `effective_date`, `crawled_at`, `revid`, `raw_sha256`, `content_hash` |
| `normalized/md/<doc_id>.md` | Human-readable Markdown of each document (tables kept as tables) |
| `normalized/extract_report.json` | Extraction statistics |
| `robots.snapshot.txt` | Copy of the site's robots.txt, used as a fallback when the live file was blocked by Cloudflare |

## Snapshot facts

- **337 pages**, all HTTP 200; fetched 2026-10-10 00:24–01:22 UTC
- Every `raw/` file matches its manifest SHA-256; no unreferenced files
- 337 normalized documents, every one containing at least one table; ~2.5M characters

| page_type | pages |
|---|---:|
| talent | 123 |
| constellation | 108 |
| weapon | 40 |
| character | 18 |
| mechanic | 15 |
| event_wish | 13 |
| version | 10 |
| artifact | 8 |
| character_upcoming | 2 |

## How it was collected

- Page list selected **offline** from Fandom's official XML dump (generated 2026-09-30), so no discovery traffic hit the live site
- Fetched through the MediaWiki API (`api.php?action=parse`), which `robots.txt` explicitly allows for `User-agent: *`
- robots.txt parsed in code, ≤1 request/second, descriptive User-Agent with a contact email
- Main-namespace articles only — no user, talk, or file pages; no personal data is collected

The site's robots.txt disallows named AI crawlers (e.g. GPTBot, ClaudeBot, CCBot). Our crawler does not use those
user agents and stays within the allowed API path, but we treat the site's stance on AI use as an ethics consideration
and discuss it in `reports/07_ethics.md`.

## Known gaps

- **No native PDFs** on this wiki — the PDF extraction path is exercised by rendering selected pages to PDF (documented in the ingestion report)
- Upcoming characters (`character_upcoming`) are placeholder pages — useful as unanswerable evaluation items
- Character pages embed full talent-scaling tables that duplicate the talent pages, so the same number can be retrieved from two sources
