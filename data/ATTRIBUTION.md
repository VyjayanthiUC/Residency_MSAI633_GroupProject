# Attribution

The corpus in `data/genshin/` is derived from the **Genshin Impact Wiki** on Fandom
(<https://genshin-impact.fandom.com/>), whose community content is licensed under
**[CC BY-SA](https://www.fandom.com/licensing)** (see Fandom's licensing page for the applicable version).

- **Authors:** the contributors to each page; the full authorship history of a page is at
  `https://genshin-impact.fandom.com/wiki/<Page_Title>?action=history`.
- **Source of each document:** the `source_url` field in `data/genshin/manifest.jsonl` and
  `data/genshin/normalized/docs.jsonl`; the page revision is recorded as `revid`.
- **Retrieved:** 2026-10-10 00:24–01:22 UTC via the MediaWiki API (`action=parse`). The page list was selected offline from
  the wiki's official XML dump generated 2026-09-30.
- **Changes made:** navigation boxes, tooltips, images, and relative timestamps were removed; tables were
  flattened into row/column grids; text was normalized and split into blocks by heading. See `ingest/extract.py`.
- **License of derived files:** the derived text in `data/genshin/` is shared under the same
  CC BY-SA license.

Genshin Impact and all related names and assets are trademarks of HoYoverse.
This project is non-commercial coursework and is not affiliated with or endorsed by HoYoverse or Fandom.
