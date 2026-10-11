"""Landing site (#64/#66): a browsable guide built ONLY from the wiki snapshot's Markdown pages
(data/genshin/normalized/md/*.md, one per crawled page). Nothing on the site is typed in by hand: titles, infoboxes,
text and tables all come from those files, so the site shows exactly the content the chat answers from.

Each file looks like:
    # <title>
    <!-- <source url> | type=<page_type> | effective=<YYYY-MM-DD> -->
    ## <section heading>
    Key: Value lines (infobox), paragraphs, and Markdown tables
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from rag import config
from web.images import clips, images
from web.talents import tables_for

MD_DIR = config.DOCS_PATH.parent / "md"
_HEADER = re.compile(r"<!--\s*(\S+)\s*\|\s*type=(\S+)\s*\|\s*effective=(\S*)\s*-->")
_MACHINE_KEY = re.compile(r"^[a-z_]+\d*$")  # wiki template fields like eff_att1, title2: not for display

# Home-page order and labels for each page type found in the snapshot
SECTIONS = [
    ("character", "Characters"), ("character_upcoming", "Upcoming characters"), ("version", "Versions"),
    ("event_wish", "Event wishes"), ("weapon", "Weapons"), ("artifact", "Artifact sets"),
    ("mechanic", "Regions and mechanics"), ("talent", "Talents"), ("constellation", "Constellations"),
]
FEATURED = ("Nod-Krai", "Snezhnaya")
COLLAPSED = ("Other Languages", "Change History", "Gallery", "Navigation")
e = html.escape


@dataclass
class Page:
    slug: str
    title: str
    url: str
    type: str
    effective: str
    sections: list[tuple[str, str]] = field(default_factory=list)  # (heading, raw body)
    info: dict[str, str] = field(default_factory=dict)

    @property
    def intro(self) -> str:
        """First prose paragraph of the page (the wiki's lead sentence), or ''."""
        for heading, body in self.sections:
            for para in re.split(r"\n\s*\n", body):
                para = para.strip()
                if (len(para) > 60 and not para.startswith("|") and not _is_kv_block(para)
                        and not para.startswith("This article is about")):  # skip the wiki's disambiguation note
                    return para
        return ""


def _is_kv_block(text: str) -> bool:
    lines = [l for l in text.splitlines() if l.strip()]
    return bool(lines) and all(_kv(l) for l in lines)


def _kv(line: str) -> tuple[str, str] | None:
    key, sep, value = line.partition(": ")
    if sep and 0 < len(key) <= 40 and not key.startswith("|"):
        return key.strip(), value.strip()
    return None


def parse(path: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    first, _, rest = text.partition("\n")
    m = _HEADER.search(rest)
    page = Page(slug=path.stem, title=first.lstrip("# ").strip(), url=m.group(1) if m else "",
                type=m.group(2) if m else "other", effective=m.group(3) if m else "")
    body = rest[m.end():] if m else rest
    lead, *chunks = re.split(r"\n## ", "\n" + body)
    if lead.strip():
        page.sections.append(("", lead.strip()))
    for chunk in chunks:
        heading, _, sec = chunk.partition("\n")
        page.sections.append((heading.strip(), sec.strip()))
        if heading.strip() == "Infobox":
            for line in sec.splitlines():
                if (kv := _kv(line)) and kv[0] not in page.info:
                    page.info[kv[0]] = kv[1]
    return page


@lru_cache(maxsize=1)
def pages() -> dict[str, Page]:
    return {p.slug: p for p in (parse(f) for f in sorted(MD_DIR.glob("*.md")))}


# ---------- rendering ----------

def section_id(path: list[str] | tuple[str, ...]) -> str:
    """Element id of a page section, from its heading path (a chunk's heading_path, or a Markdown "## A › B" heading
    split on " › "). The chat links each citation to /wiki/<doc_id>#<section_id>, so it opens the cited section here."""
    slug = re.sub(r"[^a-z0-9]+", "-", " ".join(path).lower()).strip("-")
    return "sec-" + slug if slug else ""


def page_href(doc_id: str, path: list[str] | tuple[str, ...]) -> str:
    sid = section_id(path)
    return f"/wiki/{doc_id}" + (f"#{sid}" if sid else "")


def render_block(heading: str, body: str) -> str:
    """Markdown subset used by the snapshot: Key: Value lines, pipe tables, paragraphs."""
    out, lines, i = [], body.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                head, *data = rows
                out.append('<div class="tablewrap"><table><thead><tr>' + "".join(f"<th>{e(c)}</th>" for c in head)
                           + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>"
                                                              for r in data) + "</tbody></table></div>")
            continue
        if heading == "Infobox" and _kv(line):
            pairs = []
            while i < len(lines) and _kv(lines[i]):
                k, v = _kv(lines[i])
                if not _MACHINE_KEY.match(k):
                    pairs.append(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>")
                i += 1
            out.append(f'<dl class="infobox">{"".join(pairs)}</dl>')
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("|"):
            para.append(lines[i].strip())
            i += 1
        if para:
            out.append(f"<p>{e(' '.join(para))}</p>")
        i += 1 if i < len(lines) and not lines[i].strip() else 0
    return "".join(out)


def stars(info: dict) -> str:
    q = info.get("Quality", "")
    n = int(q.split()[0]) if q[:1].isdigit() else 0
    return f'<span class="stars"><span aria-hidden="true">{"★" * n}</span><span class="sr">{n}-star</span></span>' if n else ""


def ask_name(p: Page) -> str:
    """What the Ask buttons call a page: "Version 7.0" rather than "7.0", so retrieval can match it (review on #90)."""
    return f"Version {p.title.removeprefix('Version/')}" if p.type == "version" else p.title


def img(p: Page, size: str, cls: str, lazy: bool = True) -> str:
    """Decorative picture from the wiki's image server (alt="" because the title next to it names the same thing).
    No referrer is sent, and site.js hides the picture if it fails to load."""
    url, load = images().get(p.slug, {}).get(size), "lazy" if lazy else "eager"
    return (f'<img class="{cls}" src="{e(url)}" alt="" loading="{load}" decoding="async" referrerpolicy="no-referrer">'
            if url else "")


def card(p: Page, version_titles: dict[str, str]) -> str:
    i, el = p.info, p.info.get("Element", "")
    meta = {
        "character": [el, i.get("Weapon", ""), i.get("Region", "")],
        "character_upcoming": [el, i.get("Region", ""), "Upcoming"],
        "version": [i.get("Release Date", ""), version_titles.get(p.title.removeprefix("Version/"), "")],
        "event_wish": [i.get("Character", ""), i.get("Type", "")],
        "weapon": [i.get("Weapon Type", ""), i.get("Base ATK (Lv. 1 - 90)", "")],
        "artifact": [i.get("2pcBonus", "").removeprefix("2-Piece Bonus ").strip()],
        "mechanic": [i.get("Type", "") or i.get("Group", "")],
        "talent": [i.get("Character", ""), i.get("Talent Type", "")],
        "constellation": [i.get("Character", ""), f"Constellation level {i['Level']}" if i.get("Level") else ""],
    }.get(p.type, [])
    meta_html = " · ".join(e(m) for m in meta if m)
    title = p.title.removeprefix("Version/")
    style = f' style="--el: var(--{e(el)})"' if el else ""
    q = i.get("Quality", "")
    rarity = f' data-q="{q[0]}"' if q[:1] in ("4", "5") else ""   # the picture's backdrop follows rarity, as in the game
    return (f'<li class="card" data-search="{e((p.title + " " + " ".join(meta)).lower())}"{style}{rarity}>'
            f'{img(p, "thumb", "thumb")}{stars(i)}<h3><a href="/wiki/{e(p.slug)}">{e(title)}</a></h3>'
            f'<span class="meta">{meta_html}</span>'
            f'<button type="button" class="ask" data-q="Tell me about {e(ask_name(p))}.">Ask about {e(title)}</button></li>')


# --- compact formats (team feedback: too many flat cards) ---
ABILITY_TYPES = ("talent", "constellation")      # 231 pages, all belonging to the 18 characters: grouped per character
TABLE_TYPES = ("weapon", "version")              # compared by numbers and dates, so shown as sortable tables
PAGE_SIZE = {"weapon": 12}                       # rows per page (team feedback); without JavaScript every row shows
_TALENT_ORDER = ("Normal Attack", "Elemental Skill", "Elemental Burst", "1st Ascension Passive", "4th Ascension Passive")


def _num(text: str) -> str:
    """Last number in a value ("48 - 674" -> "674"), used as the sort key of a table cell."""
    found = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
    return found[-1] if found else ""


def _date(text: str) -> str:
    from datetime import datetime
    try:
        return datetime.strptime(text.strip(), "%B %d, %Y").date().isoformat()
    except ValueError:
        return text


def abilities_of(name: str) -> tuple[list[Page], list[Page]]:
    mine = [p for p in pages().values() if p.type in ABILITY_TYPES and p.info.get("Character") == name]
    talents = sorted((p for p in mine if p.type == "talent"), key=lambda p: (
        _TALENT_ORDER.index(p.info.get("Talent Type")) if p.info.get("Talent Type") in _TALENT_ORDER else 9, p.title))
    cons = sorted((p for p in mine if p.type == "constellation"), key=lambda p: p.info.get("Level", ""))
    return talents, cons


def rating(n: int, out_of: int = 5) -> str:
    """Five star slots, n of them filled; screen readers hear "4-star" instead of the symbols."""
    return (f'<span class="rating" style="--el: var(--{"Geo" if n >= 5 else "Electro"})"><span aria-hidden="true">'
            f'{"★" * n}<span class="off">{"★" * (out_of - n)}</span></span><span class="sr">{n}-star</span></span>')


def ability_list(items: list[Page], label: str, with_search: bool) -> str:
    rows = []
    for p in items:
        tag = p.info.get("Talent Type") or (f"C{p.info['Level']}" if p.info.get("Level") else "")
        attr = f' data-search="{e((p.title + " " + tag + " " + label).lower())}"' if with_search else ""
        rows.append(f'<li{attr}><span class="tag">{e(tag)}</span><a href="/wiki/{e(p.slug)}">{e(p.title)}</a></li>')
    return f'<div><h3>{e(label)} <span class="count">{len(items)}</span></h3><ul class="list">{"".join(rows)}</ul></div>' if items else ""


def abilities_section(chars: list[Page]) -> str:
    rows = []
    for c in chars:
        talents, cons = abilities_of(c.title)
        if not talents and not cons:
            continue
        el = c.info.get("Element", "")
        style = f' style="--el: var(--{e(el)})"' if el else ""
        rows.append(f'<details class="who" data-search="{e(c.title.lower())}"{style}><summary>{img(c, "thumb", "mini")}'
                    f'<span class="whoname">{e(c.title)}</span><span class="meta">{len(talents)} talents · {len(cons)} constellations</span></summary>'
                    f'<div class="cols">{ability_list(talents, "Talents", True)}{ability_list(cons, "Constellations", True)}</div></details>')
    total = sum(1 for p in pages().values() if p.type in ABILITY_TYPES)
    return (f'<section class="block" id="abilities"><h2>Talents and constellations <span class="count">{total}</span></h2>'
            f'<div class="whos">{"".join(rows)}</div></section>')


def table_section(t: str, label: str, group: list[Page], titles: dict[str, str]) -> str:
    if t == "weapon":
        head = [("Weapon", "text"), ("Type", "text"), ("Rarity", "num"), ("Base ATK (Lv. 90)", "num"), ("Secondary stat", "text")]
        def cells(p):
            i = p.info
            return [(p.title, p.title.lower()), (i.get("Weapon Type", ""), i.get("Weapon Type", "")),
                    (i.get("Quality", "").replace(" Stars", "★"), _num(i.get("Quality", ""))),
                    (_num(i.get("Base ATK (Lv. 1 - 90)", "")), _num(i.get("Base ATK (Lv. 1 - 90)", ""))),
                    (" ".join(x for x in (i.get("Secondary Attribute Type", ""), i.get("Secondary Attribute (Lv. 1 - 90)", "").split(" - ")[-1]) if x), "")]
    else:
        head = [("Version", "text"), ("Title", "text"), ("Release date", "text")]
        def cells(p):
            v = p.title.removeprefix("Version/")
            return [(v, _date(p.info.get("Release Date", "")) or v), (titles.get(v, ""), titles.get(v, "").lower()), (p.info.get("Release Date", ""), _date(p.info.get("Release Date", "")))]
    ths = "".join(f'<th scope="col" aria-sort="none"><button type="button" data-kind="{k}">{e(h)}</button></th>' for h, k in head)
    trs = []
    for p in group:
        cs = cells(p)
        name = cs[0][0]
        first = f'<th scope="row" data-sort="{e(cs[0][1])}"><a href="/wiki/{e(p.slug)}">{e(name)}</a></th>'
        rest = "".join(f'<td data-sort="{e(k or v)}">{rating(int(k)) if h == "Rarity" and k else e(v)}</td>'
                       for (v, k), (h, _) in zip(cs[1:], head[1:]))
        trs.append(f'<tr data-search="{e(" ".join(v for v, _ in cs).lower())}">{first}{rest}'
                   f'<td><button type="button" class="ask" data-q="Tell me about {e(ask_name(p))}." '
                   f'aria-label="Ask about {e(name)}">Ask</button></td></tr>')
    page_attr = f' data-page-size="{PAGE_SIZE[t]}"' if t in PAGE_SIZE else ""   # site.js adds the page buttons
    return (f'<section class="block" id="{t}"><h2>{e(label)} <span class="count">{len(group)}</span></h2>'
            f'<div class="tablewrap"><table class="sortable"{page_attr}><caption class="sr">{e(label)}, sortable by column</caption>'
            f'<thead><tr>{ths}<th scope="col"><span class="sr">Ask</span></th></tr></thead><tbody>{"".join(trs)}</tbody></table></div></section>')



def background_clips(chars: list[Page], n: int = 4) -> list[dict[str, str]]:
    """Home banner background: the first talent demo of the n most recently released characters, played in turn."""
    def released(p: Page) -> str:
        return _date(p.info.get("Release Date", ""))
    picks = [p for p in sorted(chars, key=released, reverse=True) if clips().get(p.slug)][:n]
    return [{"src": clips()[p.slug][0]["src"], "name": p.title, "href": f"/wiki/{p.slug}"} for p in picks]


def version_titles() -> dict[str, str]:
    """Version subtitles appear in each version page's Previous/Next fields ("Luna II - An Elegy for Faded Moonlight")."""
    titles = {}
    for p in pages().values():
        if p.type == "version":
            for k in ("Previous", "Next"):
                key, _, sub = p.info.get(k, "").partition(" - ")
                if sub:
                    titles[key.strip()] = sub.strip()
    return titles


def _sort_key(p: Page):
    if p.type == "version":
        return (p.effective,)
    if p.type in ("talent", "constellation"):
        return (p.info.get("Character", ""), p.info.get("Level", ""), p.title)
    return (p.title.lower(),)


def home_body() -> str:
    all_pages, titles = pages(), version_titles()
    by_type: dict[str, list[Page]] = {}
    for p in all_pages.values():
        by_type.setdefault(p.type, []).append(p)

    featured = [p for p in all_pages.values() if p.title in FEATURED]
    def region(p: Page) -> str:
        facts = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in p.info.items()
                        if not _MACHINE_KEY.match(k) and k not in ("Name", "World Map") and len(v) <= 60)
        return (f'<article class="region">{img(p, "hero", "regionimg")}<h2><a href="/wiki/{e(p.slug)}">{e(p.title)}</a></h2><p>{e(p.intro)}</p>'
                f'<dl class="infobox">{facts}</dl>'
                f'<button type="button" class="ask" data-q="Tell me about {e(p.title)}.">Ask about {e(p.title)}</button></article>')
    hero_regions = "".join(region(p) for p in featured)

    counts = " · ".join(f"{len(by_type.get(t, []))} {label.lower()}" for t, label in SECTIONS if by_type.get(t))
    nav = "".join(f'<a href="#{t}">{e(label)}</a>' for t, label in SECTIONS if by_type.get(t) and t not in ABILITY_TYPES)
    nav += '<a href="#abilities">Talents and constellations</a>'
    sections = []
    for t, label in SECTIONS:
        group = sorted(by_type.get(t, []), key=_sort_key, reverse=(t == "version"))
        if not group or t in ABILITY_TYPES:
            continue
        if t in TABLE_TYPES:
            sections.append(table_section(t, label, group, titles))
            continue
        sections.append(f'<section class="block" id="{t}"><h2>{e(label)} <span class="count">{len(group)}</span></h2>'
                        f'<ul class="grid">{"".join(card(p, titles) for p in group)}</ul></section>')
    chars = sorted(by_type.get("character", []) + by_type.get("character_upcoming", []), key=lambda p: p.title)
    sections.append(abilities_section(chars))
    latest = max(by_type.get("version", []), key=lambda p: p.effective, default=None)
    art = img(latest, "banner", "bannerimg", lazy=False) if latest else ""
    credit = (f'<a class="bannercredit" href="/wiki/{e(latest.slug)}">Key art: {e(latest.title.removeprefix("Version/"))}'
              f'{" · " + e(titles[latest.title.removeprefix("Version/")]) if latest.title.removeprefix("Version/") in titles else ""}</a>'
              if art else "")
    reel = background_clips(by_type.get("character", []))
    # Background video: muted, no controls, started by site.js only (never for prefers-reduced-motion), with a pause
    # button (WCAG 2.2.2). Decorative, so hidden from screen readers; the key art image stays underneath as fallback.
    video = (f'<video class="bannervideo" muted playsinline preload="none" aria-hidden="true" tabindex="-1" '
             f'data-reel="{e(json.dumps(reel))}"></video>'
             f'<button type="button" class="bgtoggle" aria-pressed="false" hidden>Pause background</button>' if reel else "")
    return (f'<section class="hero"><div class="banner">{art}{video}<div class="bannertext">'
            f'<h1>Genshin Impact: Nod-Krai and Snezhnaya</h1><p class="counts">{e(counts)}</p>'
            f'<label class="search"><span class="sr">Search pages</span><input type="search" id="q" placeholder="Search {len(all_pages)} pages: characters, weapons, versions…" autocomplete="off" enterkeyhint="go"></label>'
            f'<p class="resultcount" id="results" role="status" aria-live="polite"></p>'
            f'</div>{credit}</div>'
            f'<nav class="jump" aria-label="Sections">{nav}</nav><div class="regions">{hero_regions}</div></section>'
            + "".join(sections) + '<p class="empty" id="empty" hidden>No pages match your search.</p>')


# Character-page sections whose wiki table nests tabs inside rows (flattened by the extractor): shown from the raw crawl
NESTED = {"Gameplay Info › Talents": "Type", "Gameplay Info › Constellation": "Level"}


def nested_table(p: Page, heading: str, flat: str) -> str:
    """The talent / constellation table rebuilt from the raw crawl (web/talents.py), one card per row with the wiki's
    tabs, followed by the flattened text the chatbot retrieves from, so a citation still finds its words here."""
    rows = tables_for(p.slug).get(NESTED.get(heading, ""), []) if p.type in ("character", "character_upcoming") else []
    if not rows:
        return flat
    slugs = {q.title: q.slug for q in pages().values()}
    base = section_id(heading.split(" › "))
    cards = []
    for i, r in enumerate(rows):
        name = (f'<a href="/wiki/{e(slugs[r.name])}">{e(r.name)}</a>' if r.name in slugs else e(r.name))
        kind = f"C{r.kind}" if r.kind.isdigit() else r.kind
        tabs, panels = [], []
        for j, (label, body) in enumerate(r.tabs):
            tid, pid = f"tab-{base}-{i}-{j}", f"panel-{base}-{i}-{j}"
            tabs.append(f'<button type="button" role="tab" id="{tid}" aria-controls="{pid}" '
                        f'aria-selected="{"true" if j == 0 else "false"}"{"" if j == 0 else " tabindex=\"-1\""}>{e(label)}</button>')
            panels.append(f'<div class="tabpanel" role="tabpanel" id="{pid}" aria-labelledby="{tid}"{"" if j == 0 else " hidden"}>'
                          f'{body}</div>')
        tablist = f'<div class="tabs" role="tablist" aria-label="{e(r.name)}">{"".join(tabs)}</div>' if len(tabs) > 1 else ""
        cards.append(f'<div class="tt"><div class="tthead"><h3>{name}</h3><span class="ttkind">{e(kind)}</span></div>'
                     f'{tablist}{"".join(panels)}</div>')
    return (f'<div class="tts">{"".join(cards)}</div>'
            f'<details class="asbot"><summary>As the chatbot sees it</summary>'
            f'<p class="meta">The extractor flattened this table into the text below; it is what retrieval searches '
            f'and what a citation of this section quotes.</p>{flat}</details>')


def page_body(p: Page) -> str:
    parts = []
    for heading, body in p.sections:
        content = render_block(heading, body)
        if heading in NESTED and content:
            content = nested_table(p, heading, content)
        if not content:
            continue
        if not heading:
            if "." not in body and "\n" not in body.strip():  # the wiki's tab menu ("Overview Profile Gallery")
                continue
            parts.append(f'<div class="lead">{content}</div>')
        else:
            open_attr = "" if heading.split(" › ")[0] in COLLAPSED else " open"
            sid = section_id(heading.split(" › "))
            parts.append(f'<details id="{sid}"{open_attr}><summary><h2>{e(heading)}</h2></summary>{content}</details>')
    if p.type in ("character", "character_upcoming"):
        talents, cons = abilities_of(p.title)
        if talents or cons:
            parts.insert(1 if parts and parts[0].startswith('<div class="lead">') else 0,
                         f'<details open><summary><h2>Talents and constellations</h2></summary>'
                         f'<div class="cols">{ability_list(talents, "Talents", False)}{ability_list(cons, "Constellations", False)}</div></details>')
    title = p.title.removeprefix("Version/")
    source = (f'<a href="{e(p.url)}" target="_blank" rel="noopener">View on the Genshin Impact Wiki</a>'
              if p.url else "")
    head = (f'<p class="crumbs"><a href="/">Home</a> › {e(dict(SECTIONS).get(p.type, p.type))}</p>'
            f'<h1>{e(title)}</h1><div class="pageactions">'
            f'<button type="button" class="ask btn" data-q="Tell me about {e(ask_name(p))}.">Ask about {e(title)}</button>{source}</div>')
    banner = img(p, "banner", "bannerimg", lazy=False)
    if banner:   # characters (wish art) and versions (splash screen) get a full-width banner header
        top = f'<div class="banner pagebanner">{banner}<div class="bannertext">{head}</div></div>'
    else:
        top = img(p, "hero", "pageimg") + head
    el = p.info.get("Element", "") if p.type in ("character", "character_upcoming") else ""
    data_el = f' data-el="{e(el)}"' if el else ""   # tints the page's night sky with the character's element
    return f"<article class=\"page\"{data_el}>{top}{''.join(parts)}</article>"


TEMPLATE = Path(__file__).parent / "templates" / "base.html"


def _bust(page: str) -> str:
    """Add ?v=<file time> to the stylesheet and script so browsers fetch them again after an edit."""
    static = Path(__file__).parent / "static"
    for name in ("site.css", "site.js"):
        page = page.replace(f"/static/{name}\"", f"/static/{name}?v={int((static / name).stat().st_mtime)}\"")
    return page


def render(title: str, body: str, chat_path: str = "/chat") -> str:
    return (_bust(TEMPLATE.read_text(encoding="utf-8")).replace("__TITLE__", e(title))
            .replace("__CHAT_PATH__", chat_path).replace("<!--__BODY__-->", body))
