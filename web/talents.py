"""Talent and constellation tables on character pages, rebuilt from the snapshot's raw crawl.

On the wiki these are nested: a row per talent (icon, name, type), then a full-width row holding tabs (Description,
Advanced Properties, Attribute Scaling, ...) with tables inside. The extractor flattens that inner row into one long
cell, so the Markdown page shows a wall of text and numbers. The raw parse HTML in data/genshin/raw still has the
structure: this module reads it back for display only. Nothing here feeds retrieval, and the page still shows the
flattened text the chatbot answers from (web/wiki.py puts it under "As the chatbot sees it").

Only a whitelist of tags survives (tables, paragraphs, bold, lists); links, images, videos, tooltips, scripts and
attributes other than colspan/rowspan are dropped, so the page shows the wiki's text, never its markup or scripts.
"""
from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from functools import lru_cache

from bs4 import BeautifulSoup, NavigableString, Tag

from rag import config
from web.images import _html

KEEP = {"table", "thead", "tbody", "tr", "th", "td", "p", "b", "strong", "i", "em", "br", "ul", "ol", "li", "sup", "sub"}
DROP = {"script", "style", "img", "video", "audio", "figure", "noscript", "svg"}
SKIP_TABS = {"Preview"}                       # the wiki's gameplay videos: not part of the snapshot text


@dataclass
class Row:
    name: str
    kind: str                                 # talent type ("Normal Attack") or constellation level ("1")
    tabs: list[tuple[str, str]] = field(default_factory=list)   # (label, sanitized HTML)


def clean(node: Tag) -> str:
    """The node's children as whitelisted HTML: text escaped, kept tags without attributes except colspan/rowspan."""
    out = []
    for child in node.children:
        if isinstance(child, NavigableString):
            if type(child) is NavigableString:            # skip comments, CDATA and the like
                out.append(html.escape(str(child)))
            continue
        if not isinstance(child, Tag) or child.name in DROP:
            continue
        style = (child.get("style") or "").replace(" ", "")
        if "display:none" in style or "mw-editsection" in (child.get("class") or []):
            continue
        inner = clean(child)
        if child.name in KEEP:
            attrs = "".join(f' {a}="{html.escape(str(child[a]))}"' for a in ("colspan", "rowspan")
                            if child.name in ("th", "td") and str(child.get(a, "")).isdigit())
            out.append(f"<{child.name}{attrs}>" if child.name == "br" else f"<{child.name}{attrs}>{inner}</{child.name}>")
        else:                                              # div, span, a, ...: keep the text, drop the tag
            out.append(inner)
    return "".join(out)


def _rows(table: Tag) -> list[Row]:
    body = table.tbody or table
    trs = body.find_all("tr", recursive=False)
    rows: list[Row] = []
    for tr in trs[1:]:
        cells = tr.find_all(["td", "th"], recursive=False)
        if len(cells) >= 3:                                # icon | name | type or level
            rows.append(Row(name=cells[1].get_text(" ", strip=True), kind=cells[2].get_text(" ", strip=True)))
        elif len(cells) == 1 and rows:                     # the full-width row under it
            cell = cells[0]
            tabber = cell.find("div", class_="wds-tabber")
            if tabber:
                labels = [li.get_text(" ", strip=True) for li in tabber.select(":scope > ul .wds-tabs__tab-label")]
                panels = tabber.find_all("div", class_="wds-tab__content", recursive=False)
                rows[-1].tabs = [(lab, clean(p)) for lab, p in zip(labels, panels) if lab not in SKIP_TABS]
            else:
                rows[-1].tabs = [("Description", clean(cell))]
    return [r for r in rows if r.name]


def _tables(raw_html: str) -> dict[str, list[Row]]:
    """{"Type": talent rows, "Level": constellation rows}: tables whose header is Icon | Name | Type/Level."""
    soup = BeautifulSoup(raw_html, "lxml")
    found: dict[str, list[Row]] = {}
    for table in soup.find_all("table"):
        first = (table.tbody or table).find("tr", recursive=False)
        head = [th.get_text(" ", strip=True) for th in first.find_all("th", recursive=False)] if first else []
        if len(head) == 3 and head[:2] == ["Icon", "Name"] and head[2] in ("Type", "Level") and head[2] not in found:
            if rows := _rows(table):
                found[head[2]] = rows
    return found


@lru_cache(maxsize=1)
def _raw_shas() -> dict[str, str]:
    with open(config.DOCS_PATH, encoding="utf-8") as f:
        return {d["doc_id"]: d["raw_sha256"] for d in map(json.loads, f)
                if d["page_type"] in ("character", "character_upcoming")}


@lru_cache(maxsize=64)
def tables_for(doc_id: str) -> dict[str, list[Row]]:
    sha = _raw_shas().get(doc_id)
    return _tables(_html(sha)) if sha else {}
