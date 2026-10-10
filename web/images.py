"""Page images (#64): picked from the snapshot's raw crawl (data/genshin/raw/<sha256>.json, the MediaWiki parse HTML
saved when the pages were fetched), so no new crawling happens. The images stay on the Genshin Impact Wiki's image
server and are shown from there.

Copyright: the wiki's TEXT is CC BY-SA; its IMAGES are HoYoverse game art that the wiki shows under fair use. The site
credits them in the footer, and the ethics report records that visitors' browsers load them from Fandom's servers.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from urllib.parse import unquote

from rag import config

CORPUS = config.DOCS_PATH.parent.parent            # data/genshin
IMAGE_HOST = "https://static.wikia.nocookie.net/"
_IMG = re.compile(r"https://static\.wikia\.nocookie\.net/gensin-impact/images/[0-9a-f]/[0-9a-f]{2}/[^/\"\s?]+?\.(?:png|jpe?g|webp)")
_INFOBOX = re.compile(r"<aside[^>]*portable-infobox.*?</aside>", re.S)


def _sized(url: str, width: int) -> str:
    return f"{url}/revision/latest/scale-to-width-down/{width}"


def _html(raw_sha256: str) -> str:
    path = CORPUS / "raw" / f"{raw_sha256}.json"
    try:
        text = json.loads(path.read_text(encoding="utf-8"))["parse"]["text"]
    except (OSError, KeyError, ValueError):
        return ""
    return text.get("*", "") if isinstance(text, dict) else text or ""


def pick(title: str, page_type: str, html: str) -> dict[str, str]:
    """{"thumb": small image for cards, "hero": larger image for the page view}, or {} when the page has none."""
    urls = list(dict.fromkeys(_IMG.findall(html)))
    if page_type in ("character", "character_upcoming"):
        by_file = {unquote(u.rsplit("/", 1)[-1]): u for u in urls}
        name = title.replace(" ", "_")
        icon, card = by_file.get(f"{name}_Icon.png"), by_file.get(f"{name}_Card.png")
        wish = by_file.get(f"Character_{name}_Full_Wish.png")
        return {k: v for k, v in (("thumb", icon and _sized(icon, 160)), ("hero", (card or icon) and _sized(card or icon, 420)),
                                  ("banner", wish and _sized(wish, 1600))) if v}
    box = _INFOBOX.search(html)
    first = next(iter(_IMG.findall(box.group(0))), None) if box else None
    if not first:
        return {}
    got = {"thumb": _sized(first, 160), "hero": _sized(first, 420)}
    if page_type == "version":                      # the version's splash screen: wide key art, used as a banner
        got["banner"] = _sized(first, 1600)
    return got


@lru_cache(maxsize=1)
def images() -> dict[str, dict[str, str]]:
    """slug (the Markdown file's name = docs.jsonl doc_id) -> picked images."""
    out = {}
    with open(config.DOCS_PATH, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if got := pick(d["title"], d["page_type"], _html(d["raw_sha256"])):
                out[d["doc_id"]] = got
    return out


# --- gameplay clips (#64): the wiki's short, silent ability videos (Talent Demo / Preview .mp4), same source as images ---
_VIDEO = re.compile(r"https://static\.wikia\.nocookie\.net/gensin-impact/images/[0-9a-f]/[0-9a-f]{2}/[^/\"\s?]+?\.(?:mp4|webm)")
MAX_CLIPS = 4


def _label(url: str) -> str:
    name = unquote(url.rsplit("/", 1)[-1]).rsplit(".", 1)[0].replace("_", " ")
    return re.sub(r"\s*Preview$", "", name).strip()


def pick_clips(title: str, page_type: str, html: str) -> list[dict[str, str]]:
    urls = list(dict.fromkeys(_VIDEO.findall(html)))
    if page_type in ("character", "character_upcoming"):
        prefix = f"{title.replace(' ', '_')}_Talent_Demo_"
        urls = sorted(u for u in urls if unquote(u.rsplit("/", 1)[-1]).startswith(prefix))
    urls.sort(key=_label)
    return [{"src": f"{u}/revision/latest", "label": _label(u)} for u in urls[:MAX_CLIPS]]


@lru_cache(maxsize=1)
def clips() -> dict[str, list[dict[str, str]]]:
    """slug -> up to four gameplay clips {"src", "label"}."""
    out = {}
    with open(config.DOCS_PATH, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if got := pick_clips(d["title"], d["page_type"], _html(d["raw_sha256"])):
                out[d["doc_id"]] = got
    return out
