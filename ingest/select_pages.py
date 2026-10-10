"""Select the pages to crawl, offline, from the dump index (ns0.sqlite).

Scope: Nod-Krai + Snezhnaya. Writes selection.tsv (title, page_type, reason); the crawler
fetches only this list through the API and does no discovery on the live site.
"""
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "genshin" / "selection.tsv"

REGIONS = {"Nod-Krai", "Snezhnaya"}
V6_START = "2025-09-10"  # the date field of Version/Luna I

db = sqlite3.connect(sys.argv[1])
pages = {t: x for t, x in db.execute("select title, text from pages where redirect is null")}


def infobox(text):
    m = re.search(r"\{\{\s*([A-Za-z ]+?Infobox)\s*\n", text)
    return m.group(1) if m else None


def field(text, name):
    # take the value from this line only ([ \t], not \s, or an empty field swallows the next line); drop placeholder comments
    m = re.search(r"^\|[ \t]*" + re.escape(name) + r"[ \t]*=[ \t]*(.*)$", text, re.M)
    return re.sub(r"<!--.*?-->", "", m.group(1)).strip() if m else ""


sel = {}


def add(title, ptype, reason):
    if title in pages and title not in sel:
        sel[title] = (ptype, reason)


# 1. Playable characters: region / region2 / region3 is one of the two regions
chars = set()
for t, x in pages.items():
    # newer character pages (e.g. Sandrone) have no `type` field; fall back to weapon + element to decide playability
    playable = field(x, "type") == "Playable" or (field(x, "weapon") and field(x, "element"))
    if infobox(x) == "Character Infobox" and playable:
        regs = {field(x, k) for k in ("region", "region2", "region3")}
        if regs & REGIONS:
            chars.add(t)
            add(t, "character", "region=" + ",".join(sorted(regs & REGIONS)))
    elif infobox(x) == "Character Infobox" and field(x, "type") == "Upcoming":
        # announced but unreleased: the page is mostly placeholders; keep as unanswerable-question material, not in chars
        if {field(x, k) for k in ("region", "region2")} & REGIONS:
            add(t, "character_upcoming", "upcoming")

# 2/3. These characters' talent and constellation pages; 4. their banner (wish series) pages
for t, x in pages.items():
    ib = infobox(x)
    if ib == "Talent Infobox" and field(x, "character") in chars:
        add(t, "talent", field(x, "character"))
    elif ib == "Constellation Infobox" and field(x, "character") in chars:
        add(t, "constellation", field(x, "character"))
    elif ib == "Wish Series Infobox" and field(x, "character") in chars:
        add(t, "event_wish", field(x, "character"))

# 5. Weapons released from 6.0 on
for t, x in pages.items():
    if infobox(x) == "Weapon Infobox" and field(x, "releaseDate")[:10] >= V6_START:
        add(t, "weapon", field(x, "releaseDate")[:10])

# 5b. Artifact sets from 6.0 on: the set infobox has no date, ids increase, and the first Luna I set is 056
for t, x in pages.items():
    if infobox(x) == "Artifact Set Infobox" and field(x, "id").isdigit() and int(field(x, "id")) >= 56:
        add(t, "artifact", "set id " + field(x, "id"))

# 6. Version pages from 6.0 (Luna I) on
for t in pages:
    if re.fullmatch(r"Version/(Luna [IVX]+|7\.\d+)", t):
        add(t, "version", "6.0+")

# 7. Mechanic pages: hand-picked
MECHANICS = ["Wish", "Elemental Reaction", "Bloom", "Lunar Reaction", "Lunar-Charged",
             "Lunar-Bloom", "Lunar-Crystallize", "Moonsign: Ascendant Gleam",
             "Team Bonus", "Nod-Krai", "Snezhnaya",
             # Snezhnaya's Stellar reaction family (added 2026-10-09: only Nod-Krai's Lunar reactions were picked at first; a question about a Snezhnaya character exposed undefined terms)
             "Stellar Glimmer Reaction", "Stellar Swirl", "Stellar-Conduct", "Stellar Jubilee Passive"]
for t in MECHANICS:
    add(t, "mechanic", "hand-picked")

# Extended tier: locations / factions / terminology of the two regions (counted, tagged tier=ext)
ext = Counter()
for t, x in pages.items():
    ib = infobox(x)
    if ib in ("Location Infobox", "Faction Infobox", "Terminology Infobox") and field(x, "region") in REGIONS:
        ext[ib] += 1
        add(t, "lore_" + ib.split()[0].lower(), "ext:" + field(x, "region"))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("title\tpage_type\treason\tbytes\n")
    for t, (p, r) in sorted(sel.items(), key=lambda kv: (kv[1][0], kv[0])):
        f.write(f"{t}\t{p}\t{r}\t{len(pages[t])}\n")

print("characters:", sorted(chars))
print(Counter(p for p, _ in sel.values()))
print("total:", len(sel), "| missing mechanics:", [m for m in MECHANICS if m not in pages])
