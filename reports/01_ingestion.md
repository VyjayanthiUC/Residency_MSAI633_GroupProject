# Report 01 — Ingestion (Scrape and Extraction)

**MSAI 633 Residency · Day 2 · October 10, 2026** · stages 1–2 · code in `ingest/`, snapshot in `data/genshin/`

## 1. Source and scope

- **Site:** the [Genshin Impact Fandom wiki](https://genshin-impact.fandom.com/), content under CC BY-SA (attribution in
  `data/ATTRIBUTION.md` and `data/genshin/README.md`).
- **Scope:** the two newest regions, Nod-Krai and Snezhnaya (game versions 6.0–7.1): their characters, talents, constellations,
  weapons, artifacts, event wishes, version pages, and the game mechanics they introduce.
- **Excluded:** user, talk and file pages, anything behind a login, and any directory of people. Only main-namespace articles are
  fetched, so no personal data is collected.

## 2. Page selection — offline, from the official dump

We selected pages **without crawling the live site to discover them**. `ingest/dump_to_sqlite.py` indexes Fandom's official
current-pages XML dump (`gensinimpact_pages_current.xml.7z`, generated 2026-09-30), and `ingest/select_pages.py` picks pages by
infobox type, region and release date (on or after Version Luna I, 2025-09-10), plus 15 hand-picked mechanic and system pages.

| Tier | Pages | Contents |
|---|---:|---|
| core (crawled) | **337** | talent 123 · constellation 108 · weapon 40 · character 18 · mechanic 15 · event wish 13 · version 10 · artifact 8 · upcoming character 2 |
| lore (listed, not crawled) | 266 | locations 151 · terminology 95 · factions 20 |

`data/genshin/selection.tsv` lists all 603 candidates; the committed snapshot is the core tier.

## 3. Crawl (`ingest/crawl.py`)

| Requirement | How it is met | Evidence (from `manifest.jsonl`) |
|---|---|---|
| Honor robots.txt in code | `urllib.robotparser.can_fetch()` before every request; if the live robots.txt is blocked, the committed copy `robots.snapshot.txt` is used, and the source is recorded per page | robots source: live 313, snapshot 24 (live fetch returned HTTP 403) |
| ≤ 1 request / second | sleep between requests | 337 fetches over 58 min 48 s (00:24:07–01:22:55 UTC); **minimum gap 1.000 s**, median 2.76 s |
| Descriptive User-Agent with email | `msai633-genshin-rag/0.1 (University of the Cumberlands coursework; saweisra@gmail.com)` | `crawl.py` |
| Allowed path only | MediaWiki API `api.php?action=parse` (rendered HTML), allowed for `User-agent: *` | `fetch_url` per page |
| Raw bytes saved before parsing | each response stored as `raw/<sha256>.json`, with URL, timestamp and hash in the manifest | 337 raw files; **all 337 SHA-256 values match**; 0 unreferenced files; 30.5 MB |
| Outcome | — | **337 / 337 HTTP 200**, 0 API errors |

The crawl is resumable: titles already in the manifest are skipped, so re-running it on the snapshot sends no page requests.

## 4. Extraction (`ingest/extract.py`)

Reads only `raw/` and the manifest (no network) and writes `normalized/docs.jsonl`, one Markdown file per document, and
`extract_report.json`.

- **Cleaning:** strips navboxes, table of contents, edit links, footnotes, tooltip pop-ups and images; removes soft hyphens and
  zero-width characters.
- **Tables stay tables:** `rowspan` / `colspan` are expanded into a regular grid and stored as `headers` + `rows`
  (rendered as Markdown tables in `md/`). Chunking later renders each row as `label — column: value; …`.
- **Infoboxes** become key–value blocks.
- **Per-document metadata:** `doc_id` (title slug + hash, the prefix of every chunk ID), `source_url`, `title`, heading path per
  block, `page_type`, `effective_date` and its source, `crawled_at`, `revid`, `raw_sha256`, `content_hash`.
- **Effective date:** the page's own release date; talent and constellation pages inherit their character's date.
- **Dedupe:** by SHA-256 of the normalized text; only the first copy is kept.

| Statistic (`extract_report.json`) | Value |
|---|---:|
| Documents | 337 |
| Duplicates dropped | 0 |
| Blocks: infobox / text / **table** | 337 / 3,891 / **854** |
| Documents containing a table | 337 (requirement: ≥ 3) |
| Characters | 2,517,370 |
| `effective_date` from the page / inherited / missing | 68 / 260 / 9 |

The 9 undated documents are the two upcoming characters (Mitya, Valeriy) and seven system pages that have no release date
(Bloom, Elemental Reaction, Lunar Reaction, Lunar-Charged, Team Bonus, Wish, Stellar Jubilee Passive).

The table count in our Day 1 proposal (828) was measured on an earlier, smaller selection; 854 is the count for the committed snapshot.

## 5. Reproducibility (verified)

- **Extraction is deterministic.** Re-running `uv run python ingest/extract.py` on the committed `raw/` reproduces
  `normalized/` byte for byte (`git diff` empty). Checked by the author on 2026-10-10 and again for this report on main `7bcc416`
  (9.9 s). It also passes with strict encoding warnings (`-X warn_default_encoding -W error::EncodingWarning`), so the output does not
  depend on the platform's default encoding (an issue found in review of PR #5 and fixed there).
- **The snapshot is the raw crawl output.** Every manifest hash matches its raw file, and there are no extra files.
- Everyone downstream reads the committed snapshot, so every reported number is computed from identical input.

## 6. PDF path (`ingest/pdfs.py`)

The wiki hosts **no native PDFs** (checked by MIME type through the MediaWiki API, as stated in the proposal). To exercise PDF
extraction anyway, we **render** six crawled pages to PDF with a headless Chromium browser from the saved raw HTML (no network),
extract them with `pdfplumber`, and compare against the HTML extraction of the same page. These are rendered PDFs, not crawled ones.

| Page | PDF pages | Tables (HTML → PDF) | Token recall | Number recall |
|---|---:|---|---:|---:|
| Version/Luna I | 19 | 2 → 3 | 99.2% | 100% |
| Version/Luna IV | 16 | 2 → 3 | 99.2% | 100% |
| Version/7.0 | 17 | 1 → 2 | 99.6% | 100% |
| Wish | 11 | 12 → 13 | 99.6% | 100% |
| Runo: Dawnless Rest of Karsikko | 4 | 4 → 7 | 96.7% | 100% |
| Athame Artis | 8 | 4 → 11 | 96.3% | 100% |

Every number on the page survives the PDF round trip; the token losses are layout text. The higher PDF table counts are layout
boxes that `pdfplumber` detects as tables, which is why we keep HTML as the primary extraction path. Two independent runs
(Edge on Windows, Brave on Linux) gave the same page counts, table counts and number recall; token recall differed by at most
0.2 points on three pages (the table shows the Brave run; #17). The PDF text is a side-by-side extraction check and is **not** part
of the retrieval corpus.

## 7. Known issues and limitations

- **Flattened *Talents* table on character pages.** The table is a tabbed box (Description / Gameplay Notes / Advanced Properties /
  Attribute Scaling / Preview) nested inside one cell, and the extractor flattens it into a single run-on cell — 16 of the 18
  character pages contain such a block. The talent pages carry the same data as clean tables, so retrieval can still find it there
  (report 04). Planned fix: skip that table on character pages. We did not apply it on Day 2, because it changes `normalized/` and
  would require re-chunking, re-indexing and re-running every evaluation after the golden set was verified.
- **Duplicated numbers.** Character pages embed talent-scaling tables that duplicate the talent pages, so the same number can be
  retrieved from two sources.
- **Snapshot age.** The selection comes from a dump generated 2026-09-30 and the pages were fetched on 2026-10-10; edits after that
  are not reflected. The golden set was checked against the snapshot, with the live page only as a reference.
- **robots.txt fallback.** For 24 pages the live robots.txt returned HTTP 403 (Cloudflare), so the committed copy was used.
  The site's robots.txt disallows named AI crawlers; we do not use those user agents, and we discuss the site's stance in report 07.
- The exact download URL of the dump was not recorded; its file name and generation date identify it.

## 8. Reproduce

```bash
python ingest/dump_to_sqlite.py gensinimpact_pages_current.xml ns0.sqlite   # dump -> page index (not committed, ~220 MB)
python ingest/select_pages.py ns0.sqlite                                    # -> data/genshin/selection.tsv
uv run python ingest/crawl.py                                               # -> raw/ + manifest.jsonl (core tier, <=1 req/s)
uv run python ingest/extract.py                                             # -> normalized/ (byte-identical on the snapshot)
uv run python -m ingest.pdfs [--browser PATH]                               # -> artifacts/pdf/comparison.json
```

Steps 3–5 run against the committed snapshot without any page requests; step 4 can be checked with `git diff --stat data/genshin/normalized`.
