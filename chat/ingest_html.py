"""Convert the crawled, rendered wiki HTML into chunks.jsonl for the chat UI.

Input (read-only): data/genshin/manifest.jsonl + data/genshin/raw/<sha256>.json (api.php?action=parse responses)
Output: chat/data/chunks.jsonl (one contract.Chunk per line)

Interim chunking for the UI: split on h2/h3 sections, then at ~1500 chars; not the formal chunking experiment.
Usage: uv run python ingest_html.py [--all]   # default: core tier only (no lore_*)
"""
from __future__ import annotations

import argparse
import os
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from contract import Chunk

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("CORPUS_DIR", ROOT / "data" / "genshin"))
OUT = Path(__file__).parent / "data" / "chunks.jsonl"

SKIP_SECTIONS = {"Other Languages", "Navigation", "References", "Gallery", "Voice-Overs", "Preview", "Talent Demo"}
DROP = ["script", "style", "noscript", "figure", "img", ".mw-editsection", "sup.reference", ".reference",
        ".navbox", "table.navbox", ".toc", ".wikia-gallery", ".mw-references-wrap"]
MAX_CHARS = 1500


BLOCK = ["p", "li", "div", "dt", "dd", "tr", "h4", "h5", "blockquote"]


def clean(s: str) -> str:
    return s.replace("‍", "").replace("\xad", "").replace("\xa0", " ")


def cell_text(el: Tag, keep_newlines: bool = False) -> str:
    s = clean(" ".join(el.stripped_strings))
    if keep_newlines:  # cell contains an already-rendered nested table: keep its rows
        return "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in s.splitlines() if ln.strip())
    return re.sub(r"\s+", " ", s).strip()


def level_header(h: str) -> str:
    return f"Lv{h}" if h.isdigit() else h


def render_table(table: Tag) -> str:
    rows = [[cell_text(c, keep_newlines=True) for c in tr.find_all(["th", "td"], recursive=False)]
            for tr in table.find_all("tr")]
    rows = [r for r in rows if any(r)]
    if not rows:
        return ""
    first = table.find("tr")
    header_is_th = first is not None and all(c.name == "th" for c in first.find_all(["th", "td"], recursive=False))
    lines = []
    if header_is_th and len(rows) > 1:
        head = [level_header(h) for h in rows[0]]
        for r in rows[1:]:
            if len(r) == len(head) and len(r) > 1:
                pairs = "; ".join(f"{h}: {v}" for h, v in zip(head[1:], r[1:]) if v)
                lines.append(f"{r[0]} — {pairs}" if r[0] else pairs)
            else:
                lines.append(" | ".join(r))
        return "\n".join([" | ".join(head)] + lines)
    return "\n".join(" | ".join(r) for r in rows)


def render_infobox(aside: Tag) -> str:
    lines = []
    title = aside.select_one(".pi-title")
    if title:
        lines.append(cell_text(title))
    for item in aside.select("div.pi-data"):
        label, value = item.select_one(".pi-data-label"), item.select_one(".pi-data-value")
        if not value:
            continue
        # some items have no label (e.g. constellation effect text); fall back to data-source
        name = cell_text(label) if label else item.get("data-source", "").replace("_", " ").title()
        lines.append(f"{name}: {cell_text(value)}")
    return "\n".join(lines)


def page_sections(html: str) -> list[tuple[list[str], str, str]]:
    """Return [(section path, anchor id, text)]."""
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(".mw-parser-output") or soup
    for sel in DROP:
        for el in root.select(sel):
            el.decompose()
    infobox = "\n".join(render_infobox(a) for a in root.select("aside.portable-infobox"))
    for a in root.select("aside.portable-infobox"):
        a.decompose()
    # Source newlines carry no meaning; collapse them first (must happen before rendering tables, or table rows get flattened)
    for s in root.find_all(string=True):
        if "\n" in s:
            s.replace_with(NavigableString(s.replace("\n", " ")))
    for t in reversed(root.find_all("table")):  # innermost first
        t.replace_with(NavigableString("\n" + render_table(t) + "\n"))
    # newline only after block elements; inline links stay inside their sentence
    for br in root.find_all("br"):
        br.replace_with(NavigableString("\n"))
    for blk in root.find_all(BLOCK):
        blk.append(NavigableString("\n"))

    sections, path, anchor, buf = [], ["Intro"], "", [infobox] if infobox else []

    def flush():
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(b for b in buf if b.strip())).strip()
        if text and path[0] not in SKIP_SECTIONS:
            sections.append((list(path), anchor, text))

    for el in root.children:
        if isinstance(el, Tag) and el.name in ("h2", "h3"):
            flush()
            buf = []
            head = el.select_one(".mw-headline")
            name = cell_text(head or el)
            anchor = (head.get("id") if head else None) or name.replace(" ", "_")
            path = [name] if el.name == "h2" else [path[0], name]
            continue
        if isinstance(el, Tag) and el.name in ("ul", "ol"):
            text = "\n".join("- " + cell_text(li) for li in el.find_all("li", recursive=False))
        else:
            text = clean(el.get_text("") if isinstance(el, Tag) else str(el))
        text = "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines())
        buf.append(text)
    flush()
    return sections


def split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    out, cur = [], ""
    lines = []
    for line in text.splitlines():  # hard-split a single overlong line
        lines += [line[i:i + MAX_CHARS] for i in range(0, len(line), MAX_CHARS)] or [""]
    for line in lines:
        if cur and len(cur) + len(line) > MAX_CHARS:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        out.append(cur)
    return [c.strip() for c in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include lore_* pages")
    args = ap.parse_args()

    seen, chunks = set(), []
    for line in open(DATA / "manifest.jsonl", encoding="utf-8"):
        m = json.loads(line)
        if m.get("http_status") != 200 or m.get("api_error") or m["sha256"] in seen:
            continue
        if m["page_type"].startswith("lore_") and not args.all:
            continue
        seen.add(m["sha256"])
        parse = json.load(open(DATA / "raw" / f"{m['sha256']}.json", encoding="utf-8"))["parse"]
        title = parse.get("title") or m["title"]
        for path, anchor, text in page_sections(parse["text"]):
            for n, part in enumerate(split_long(text)):
                chunks.append(Chunk(
                    chunk_id=f"{title}#{'/'.join(path)}#{n}",
                    url=m["source_url"] + (f"#{anchor}" if anchor else ""),
                    title=title, heading_path=path, page_type=m["page_type"],
                    text=part, crawled_at=m["fetched_at"],
                ))

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_json(), ensure_ascii=False) + "\n")
    print(f"{len(seen)} pages → {len(chunks)} chunks → {OUT}")


if __name__ == "__main__":
    main()
