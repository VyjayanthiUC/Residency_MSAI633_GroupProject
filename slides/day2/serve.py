#!/usr/bin/env python3
"""Local server for the Day 2 deck: static files, plus a small comment API used by the optional local review layer (review/comments.js, not in the repo).

    python3 slides/day2/serve.py            # http://127.0.0.1:8820
    python3 slides/day2/serve.py --dump [outline] [--all]   # print open comments, grouped by screen
"""
import json
import re
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent


def store(doc="slides"):
    # one file per review document: comments.json (the deck) and comments-<doc>.json (e.g. the outline)
    return HERE / ("comments.json" if doc == "slides" else f"comments-{doc}.json")
PORT = 8820


def head():
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True, text=True)
    return r.stdout.strip() or None


def load(doc="slides"):
    f = store(doc)
    return json.loads(f.read_text()) if f.exists() else {"comments": []}


def doc_of(path):
    name = path.split("?")[0].rsplit("/", 1)[-1]
    return name if re.fullmatch(r"[a-z0-9-]{1,40}", name) else None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(HERE), **k)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def reply(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/comments/"):
            doc = doc_of(self.path)
            if not doc:
                return self.reply(404, {"error": "bad document name"})
            return self.reply(200, {**load(doc), "head": head()})
        super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/comments/"):
            return self.reply(404, {"error": "not found"})
        doc = doc_of(self.path)
        if not doc:
            return self.reply(404, {"error": "bad document name"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if not isinstance(body.get("comments"), list):
            return self.reply(400, {"error": "comments must be a list"})
        store(doc).write_text(json.dumps({"comments": body["comments"]}, ensure_ascii=False, indent=1))
        self.reply(200, {"ok": True, "n": len(body["comments"])})

    def log_message(self, *a):
        pass


def dump(doc="slides", show_all=False):
    tag = {"like": "like", "change": "change", "question": "question", "idea": "idea"}
    cs = [c for c in load(doc)["comments"] if show_all or not c.get("resolved")]
    by = {}
    for i, c in enumerate(cs, 1):
        by.setdefault(c.get("screen") or "?", []).append((i, c))
    for screen, items in by.items():
        print(f"\n## {screen} — {items[0][1].get('label', '')}")
        for i, c in items:
            t = c.get("target", {})
            where = t.get("text") or t.get("key") or t.get("kind", "")
            print(f"{i}. [{tag.get(c.get('tag'), c.get('tag'))}] ({c.get('id')}) 「{str(where)[:60]}」 {c.get('text', '')}")
    if not cs:
        print("no open comments")


if __name__ == "__main__":
    if "--dump" in sys.argv:
        names = [a for a in sys.argv[1:] if not a.startswith("--")]
        dump(names[0] if names else "slides", "--all" in sys.argv)
    else:
        print(f"deck: http://127.0.0.1:{PORT}/")
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
