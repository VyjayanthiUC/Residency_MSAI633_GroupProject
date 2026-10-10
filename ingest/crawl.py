"""Stage 1 — Scrape.

Fetch the rendered pages listed in the offline selection (selection.tsv) through the MediaWiki API.

- robots.txt is parsed and obeyed in code: try the live file first; Fandom's Cloudflare returns 403 to
  non-browser requests, in which case fall back to a browser-saved copy (data/robots.snapshot.txt) and record the source.
- Rate limit <=1 request/second; the User-Agent carries the project name and a contact email.
- Raw bytes are written to disk first (URL, fetch time, sha256); all parsing later reads from disk, never the live site.
- Resumable: titles already in the manifest are skipped.

Usage: python ingest/crawl.py [--tiers core|all] [--limit N]
"""
import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "genshin"
SELECTION = DATA / "selection.tsv"
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.jsonl"
ROBOTS_SNAPSHOT = DATA / "robots.snapshot.txt"

SITE = "https://genshin-impact.fandom.com"
API = SITE + "/api.php"
USER_AGENT = "msai633-genshin-rag/0.1 (University of the Cumberlands coursework; saweisra@gmail.com)"
MIN_INTERVAL = 1.0  # seconds
LORE_TYPES = {"lore_location", "lore_terminology", "lore_faction"}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_robots():
    rp = urllib.robotparser.RobotFileParser()
    try:
        req = urllib.request.Request(SITE + "/robots.txt", headers={"User-Agent": USER_AGENT})
        text = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
        source = "live"
    except urllib.error.HTTPError as e:
        text = ROBOTS_SNAPSHOT.read_text(encoding="utf-8")
        source = f"snapshot (live fetch returned HTTP {e.code})"
    except (urllib.error.URLError, TimeoutError) as e:  # offline: DNS failure, refused connection, timeout
        text = ROBOTS_SNAPSHOT.read_text(encoding="utf-8")
        source = f"snapshot (live fetch failed: {getattr(e, 'reason', e)})"
    rp.parse(text.splitlines())
    log(f"robots.txt loaded from {source}")
    return rp, source


def api_url(title):
    q = {"action": "parse", "page": title, "format": "json", "formatversion": "2",
         "prop": "text|sections|revid|displaytitle|categories", "redirects": "1"}
    return API + "?" + urllib.parse.urlencode(q)


def page_url(title):
    return SITE + "/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiers", choices=["core", "all"], default="core")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    # QUOTE_NONE: some constellation titles contain literal double quotes ("I Must See…"); the default dialect would strip them as CSV quoting
    rows = list(csv.DictReader(SELECTION.open(encoding="utf-8", newline=""), delimiter="\t", quoting=csv.QUOTE_NONE))
    if args.tiers == "core":
        rows = [r for r in rows if r["page_type"] not in LORE_TYPES]
    done = set()
    if MANIFEST.exists():
        done = {json.loads(l)["title"] for l in MANIFEST.open(encoding="utf-8") if l.strip()}
    todo = [r for r in rows if r["title"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    log(f"selection={len(rows)} already={len(done & {r['title'] for r in rows})} todo={len(todo)}")

    rp, robots_source = load_robots()
    last = 0.0
    ok = fail = 0
    with MANIFEST.open("a", encoding="utf-8") as mf:
        for i, r in enumerate(todo, 1):
            url = api_url(r["title"])
            if not rp.can_fetch(USER_AGENT, url):
                log(f"({i}/{len(todo)}) SKIP robots disallow: {r['title']}")
                continue
            wait = MIN_INTERVAL - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            fetched_at = datetime.now(timezone.utc).isoformat()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                resp = urllib.request.urlopen(req, timeout=30)
                body, status = resp.read(), resp.status
            except urllib.error.HTTPError as e:
                body, status = e.read(), e.code
            except Exception as e:  # network error: log it; the next resumed run retries
                fail += 1
                log(f"({i}/{len(todo)}) ERROR {r['title']}: {e}")
                continue
            sha = hashlib.sha256(body).hexdigest()
            api_error = None
            if status == 200:
                try:
                    api_error = json.loads(body).get("error", {}).get("code")
                except ValueError:
                    api_error = "non-json"
            rec = {"title": r["title"], "page_type": r["page_type"], "source_url": page_url(r["title"]),
                   "fetch_url": url, "fetched_at": fetched_at, "http_status": status,
                   "api_error": api_error, "sha256": sha, "bytes": len(body),
                   "robots_source": robots_source}
            if status != 200 or api_error:
                fail += 1
                log(f"({i}/{len(todo)}) FAIL {status} {api_error} {r['title']}")
                continue  # failures are not written to the manifest or raw/, so a resumed run retries them
            (RAW / f"{sha}.json").write_bytes(body)  # only successful responses are stored
            mf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            mf.flush()
            ok += 1
            log(f"({i}/{len(todo)}) ok {r['page_type']:<18} {len(body)//1024:>4}KB {r['title']}")
    log(f"done ok={ok} fail={fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
