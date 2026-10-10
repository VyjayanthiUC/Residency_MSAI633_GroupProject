"""Stage 2 — Extraction.

Input: data/genshin/manifest.jsonl + data/genshin/raw/<sha>.json (raw API responses saved by the crawler; reads disk only, no network)
Output:
  data/genshin/normalized/docs.jsonl   one document per line (metadata + ordered blocks)
  data/genshin/normalized/md/<doc_id>.md   Markdown version for humans and for the chunker
  data/genshin/normalized/extract_report.json   statistics + dedupe log

Cleaning: strip navboxes / TOC / edit links / footnotes / tooltip pop-ups / images; remove soft hyphens and zero-width characters.
Tables stay tables: rowspan / colspan are expanded into a regular grid, stored as headers + rows, and rendered as Markdown tables.
Infoboxes become key-value blocks. effective_date is the page's Release Date; talent / constellation pages inherit their character's date.
Dedupe: by sha256 of the normalized text; only the first copy is kept.
"""
import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "genshin"
OUT = DATA / "normalized"

# h2 sections dropped entirely
DROP_SECTIONS = {"Navigation", "References", "Gallery", "Video Guides", "Media"}
# elements removed outright
DROP_SELECTORS = [
    "script", "style", "noscript", ".navbox", "table.navbox-border", ".toc", "#toc",
    ".mw-editsection", "sup.reference", ".mw-references-wrap",
    # the [Expand] button of collapsible tables; a tooltip's visible label carries the same class, so exclude it
    ".mw-collapsible-toggle:not(.toggle-tooltip)", "img", "figure figcaption:empty", ".mobile-only",
]
INVISIBLE = dict.fromkeys(map(ord, "­​‌‍⁠﻿"), None)
HEADINGS = {"h2": 1, "h3": 2, "h4": 3, "h5": 4}


# relative times ("(11 months ago)" / "Ran 4 months, 21 days ago") are computed at crawl time and go stale within days -> always removed
RELATIVE_TIME = re.compile(
    r"\(?\s*(?:Ran\s+|in\s+)?(?:about\s+)?(?:\d+\s+(?:years?|months?|weeks?|days?|hours?|minutes?)[,\s]*)+(?:ago)?\s*\)?(?=\W|$)")
EDIT_CRUFT = re.compile(r"\[\s*Create New History\s*\]")


def clean(text):
    text = unicodedata.normalize("NFKC", text).translate(INVISIBLE)
    text = EDIT_CRUFT.sub("", RELATIVE_TIME.sub(lambda m: "" if "ago" in m.group(0) or m.group(0).startswith("Ran") else m.group(0), text))
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\s*\n\s*", "\n", text)).strip()


def cell_text(cell):
    return clean(cell.get_text(" ", strip=True)).replace("\n", " ")


def table_grid(table):
    """Expand an HTML table into a regular 2-D grid (handles rowspan / colspan). Only this table's own rows are read."""
    rows = table.select(":scope > tr, :scope > tbody > tr, :scope > thead > tr, :scope > tfoot > tr")
    grid, carry = [], {}  # carry: col -> (rows remaining, text, is_header)
    for tr in rows:
        out, col = [], 0
        cells = tr.find_all(["th", "td"], recursive=False)
        it = iter(cells)
        while True:
            if col in carry:
                n, txt, is_h = carry[col]
                out.append((txt, is_h))
                carry[col] = (n - 1, txt, is_h) if n > 1 else None
                if carry[col] is None:
                    del carry[col]
                col += 1
                continue
            c = next(it, None)
            if c is None:
                break
            txt, is_h = cell_text(c), c.name == "th"
            span = int(re.sub(r"\D", "", c.get("colspan", "1")) or 1)
            rspan = int(re.sub(r"\D", "", c.get("rowspan", "1")) or 1)
            # colspan: a row with a single cell (a banner row such as "Ascension Cost …") -> text in the first cell only, or it repeats N times;
            # a labeled row whose value spans several columns (e.g. "Duration 15s" identical at every level) -> every column needs the value, so copy it.
            # rowspan continuing downward is semantic, so it is still copied.
            full_width = len(cells) == 1 and not carry
            for k in range(span):
                cell = txt if (k == 0 or not full_width) else ""
                out.append((cell, is_h))
                if rspan > 1:
                    carry[col] = (rspan - 1, cell, is_h)
                col += 1
        if any(t for t, _ in out):
            grid.append(out)
    if not grid:
        return None
    width = max(len(r) for r in grid)
    grid = [r + [("", False)] * (width - len(r)) for r in grid]
    # if every non-empty cell of the first row is a th, treat it as the header (ascension tables end with an empty td)
    if any(t for t, _ in grid[0]) and all(h for t, h in grid[0] if t):
        headers, body = [t for t, _ in grid[0]], grid[1:]
    else:
        headers, body = [], grid
    return {"headers": headers, "rows": [[t for t, _ in r] for r in body]}


def table_md(tbl):
    def esc(s):
        return s.replace("|", "\\|")
    headers = tbl["headers"] or [""] * len(tbl["rows"][0]) if tbl["rows"] else tbl["headers"]
    lines = ["| " + " | ".join(esc(h) for h in headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(esc(c) for c in r) + " |" for r in tbl["rows"]]
    return "\n".join(lines)


def infobox_pairs(aside):
    pairs = []
    title = aside.select_one(".pi-title")
    if title:
        pairs.append(("Name", cell_text(title)))
    # talent / constellation effect text (data-source="info") has no label and must not be skipped: it is the core content of those pages
    NAMES = {"info": "Description", "description": "Description", "effect": "Effect"}
    for item in aside.select(".pi-data"):
        label, value = item.select_one(".pi-data-label"), item.select_one(".pi-data-value")
        if not value:
            continue
        key = cell_text(label) if label else NAMES.get(item.get("data-source"), item.get("data-source") or "Value")
        v = clean(value.get_text(" ", strip=True)).replace("\n", " ")
        if v:
            pairs.append((key, v))
    # "smart" horizontal groups: one row of labels, one row of values, paired in order (a weapon's Base ATK / Secondary Attribute)
    for grp in aside.select(".pi-smart-group"):
        labels = [cell_text(x) for x in grp.select(".pi-smart-data-label")]
        values = [clean(x.get_text(" ", strip=True)) for x in grp.select(".pi-smart-data-value")]
        pairs += [(k, v) for k, v in zip(labels, values) if k and v]
    for grp in aside.select("table.pi-horizontal-group"):
        t = table_grid(grp)
        if t and t["headers"] and t["rows"]:
            pairs += [(h, v) for h, v in zip(t["headers"], t["rows"][0]) if v]
    return pairs


class Walker:
    def __init__(self, title):
        self.path, self.blocks, self.buf, self.skip = [], [], [], False
        self.title = title

    def flush(self):
        text = clean(" ".join(self.buf))
        self.buf = []
        if text and not self.skip:
            self.blocks.append({"heading_path": [self.title] + self.path, "kind": "text", "text": text})

    def heading(self, el):
        self.flush()
        level = HEADINGS[el.name]
        name = cell_text(el.select_one(".mw-headline") or el)
        self.path = self.path[: level - 1] + [name]
        if level == 1:
            self.skip = name in DROP_SECTIONS

    def walk(self, node):
        for ch in node.children:
            if isinstance(ch, NavigableString):
                if ch.strip():
                    self.buf.append(str(ch))
                continue
            if not isinstance(ch, Tag):
                continue
            if ch.name in HEADINGS:
                self.heading(ch)
            elif ch.name == "aside" and "portable-infobox" in ch.get("class", []):
                self.flush()
                pairs = infobox_pairs(ch)
                if pairs and not self.skip:
                    self.blocks.append({"heading_path": [self.title] + self.path + ["Infobox"],
                                        "kind": "infobox", "pairs": pairs,
                                        "text": "\n".join(f"{k}: {v}" for k, v in pairs)})
            elif ch.name == "table":
                self.flush()
                tbl = table_grid(ch)
                if tbl and tbl["rows"] and not self.skip:
                    self.blocks.append({"heading_path": [self.title] + self.path, "kind": "table",
                                        "table": tbl, "text": table_md(tbl)})
            elif ch.name in ("div", "section", "center", "blockquote"):
                self.flush()
                self.walk(ch)
                self.flush()
            elif ch.name in ("p", "ul", "ol", "dl"):
                self.flush()
                if ch.name == "p":
                    self.buf.append(ch.get_text(" ", strip=True))
                else:
                    items = []
                    for li in ch.find_all(["li", "dt", "dd"]):
                        t = clean(li.get_text(" ", strip=True))
                        items.append(t + ":" if li.name == "dt" else "- " + t)
                    self.buf.append("\n".join(items))
                self.flush()
            else:
                self.buf.append(ch.get_text(" ", strip=True))
        return self


def harvest_tooltips(soup):
    """A tooltip = visible label + a display:none hidden explanation. Remove only the hidden part and keep the label.

    Glossary-style tooltips (giw-extra-effect: term -> definition) go into a page-level glossary, each term once;
    otherwise the definition is pasted into the middle of the sentence and repeated many times on the page.
    """
    glossary = {}
    for wrap in soup.select(".custom-tt-wrapper"):
        hidden = wrap.select_one(":scope > .mw-collapsible-content")
        if hidden is None:
            continue
        if "giw-extra-effect" in hidden.get("class", []):
            head = hidden.select_one(".giw-extra-effect-header")
            body = hidden.select_one(".giw-extra-effect-content")
            if head and body:
                glossary.setdefault(cell_text(head), clean(body.get_text(" ", strip=True)).replace("\n", " "))
        hidden.decompose()
    return glossary


def keep_icon_text(soup):
    """Some fields are icon-only (rarity "4 Stars"); keep the alt text before images are removed.

    Scope: rarity icons are kept site-wide, and so is any infobox value that is only an image. Other alts (splash art etc.) are noise and dropped.
    """
    for img in soup.select("img[alt]"):
        alt = img.get("alt", "").strip()
        value = img.find_parent(class_="pi-data-value")
        if re.fullmatch(r"\d Stars?", alt) or (value is not None and not value.get_text(strip=True)):
            img.replace_with(NavigableString(alt))


def flatten_cards(soup):
    """Icon cards (materials, characters, weapons) carry their name only in <a title> / <img alt>; turn them into text before images are removed: "Mora ×20,000"."""
    for card in soup.select(".card-container"):
        link, img = card.select_one("a[title]"), card.select_one("img[alt]")
        name = (link and link.get("title")) or (img and img.get("alt")) or ""
        caption = card.select_one(".card-caption")
        qty = card.select_one(".card-text")
        cap = cell_text(caption) if caption else ""
        subtotal = cap if re.fullmatch(r"\[.*\]", cap) else ""  # talent upgrade tables: the caption is the running total "[12,500]"
        name = name or ("" if subtotal else cap)
        qty = cell_text(qty) if qty else ""
        text = f"{name} ×{qty}" if name and qty and qty != name else (name or qty)
        if subtotal:
            text += f" (total {subtotal.strip('[]')})"
        card.replace_with(NavigableString(f" {text}; " if text else " "))


def parse_date(s):
    for fmt in ("%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    m = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", s)
    return parse_date(m.group(1)) if m else None


def find_date(blocks):
    for b in blocks:
        if b["kind"] == "infobox":
            for k, v in b["pairs"]:
                if k.lower() in ("release date", "date", "released"):
                    d = parse_date(v.split(";")[0].strip())
                    if d:
                        return d
    return None


def doc_id(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    return f"gi-{slug}-{hashlib.sha1(title.encode()).hexdigest()[:8]}"


def main():
    (OUT / "md").mkdir(parents=True, exist_ok=True)
    manifest = [json.loads(l) for l in (DATA / "manifest.jsonl").open() if l.strip()]
    docs, seen, dups = [], {}, []
    for rec in manifest:
        payload = json.loads((DATA / "raw" / f"{rec['sha256']}.json").read_bytes())["parse"]
        soup = BeautifulSoup(payload["text"], "lxml")
        glossary = harvest_tooltips(soup)
        flatten_cards(soup)
        keep_icon_text(soup)
        for sel in DROP_SELECTORS:
            for el in soup.select(sel):
                el.decompose()
        root = soup.select_one(".mw-parser-output") or soup.body
        w = Walker(rec["title"]).walk(root)
        w.flush()
        blocks = w.blocks
        if glossary:
            blocks.append({"heading_path": [rec["title"], "Glossary"], "kind": "text",
                           "text": "\n".join(f"{k}: {v}" for k, v in glossary.items())})
        body = "\n\n".join(b["text"] for b in blocks)
        chash = hashlib.sha256(body.encode()).hexdigest()
        if chash in seen:
            dups.append({"title": rec["title"], "duplicate_of": seen[chash]})
            continue
        seen[chash] = rec["title"]
        infobox = next((dict(b["pairs"]) for b in blocks if b["kind"] == "infobox"), {})
        docs.append({
            "doc_id": doc_id(rec["title"]), "title": rec["title"], "page_type": rec["page_type"],
            "source_url": rec["source_url"], "crawled_at": rec["fetched_at"], "revid": payload.get("revid"),
            "raw_sha256": rec["sha256"], "content_hash": chash,
            "effective_date": find_date(blocks), "effective_date_source": "page" if find_date(blocks) else None,
            "character": infobox.get("Character"),
            "blocks": blocks,
        })

    # talent / constellation pages have no date -> inherit from their character
    char_dates = {d["title"]: d["effective_date"] for d in docs if d["page_type"] == "character"}
    for d in docs:
        if not d["effective_date"] and d.get("character") in char_dates and char_dates[d["character"]]:
            d["effective_date"], d["effective_date_source"] = char_dates[d["character"]], "inherited:character"

    # pages without a date: 'Released in Version "X"' in Change History -> look up that version page's Release Date
    version_dates = {}
    for d in docs:
        if d["page_type"] == "version":
            name = next((b for b in d["blocks"] if b["kind"] == "infobox"), {"pairs": []})
            label = dict(name["pairs"]).get("Name", "")
            m = re.search(r'Version "?([^"]+)"?', label)
            if m and d["effective_date"]:
                version_dates[m.group(1).strip()] = d["effective_date"]
    for d in docs:
        if d["effective_date"]:
            continue
        hist = " ".join(b["text"] for b in d["blocks"] if "Change History" in b["heading_path"])
        m = re.search(r'Released in\s+Version\s+(?:"([^"]+)"|(\S+))', hist)
        ver = m and (m.group(1) or m.group(2)).strip()
        if ver in version_dates:
            d["effective_date"] = version_dates[ver]
            d["effective_date_source"] = f"inherited:version {ver}"

    with (OUT / "docs.jsonl").open("w") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
            md = [f"# {d['title']}", f"<!-- {d['source_url']} | type={d['page_type']} | effective={d['effective_date']} -->"]
            last = None
            for b in d["blocks"]:
                hp = " › ".join(b["heading_path"][1:])
                if hp and hp != last:
                    md.append(f"\n## {hp}")
                    last = hp
                md.append(b["text"])
            (OUT / "md" / f"{d['doc_id']}.md").write_text("\n\n".join(md) + "\n")

    kinds = {}
    for d in docs:
        for b in d["blocks"]:
            kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    report = {
        "docs": len(docs), "duplicates_dropped": dups, "blocks_by_kind": kinds,
        "docs_with_table": sum(any(b["kind"] == "table" for b in d["blocks"]) for d in docs),
        "effective_date": {
            "page": sum(d["effective_date_source"] == "page" for d in docs),
            "inherited": sum((d["effective_date_source"] or "").startswith("inherited") for d in docs),
            "missing": [d["title"] for d in docs if not d["effective_date"]],
        },
        "total_chars": sum(len("\n\n".join(b["text"] for b in d["blocks"])) for d in docs),
    }
    (OUT / "extract_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: (v if k != "effective_date" else {**v, "missing": len(v["missing"])}) for k, v in report.items()
                      if k != "duplicates_dropped"}, ensure_ascii=False), "| dups:", len(dups))


if __name__ == "__main__":
    main()
