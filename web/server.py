"""Front door (#64): the site at "/" (built from the snapshot's Markdown pages, web/wiki.py) and the Chainlit chat
mounted at "/chat", on one server and one origin. The site's chat pop-up shows /chat in an iframe, so login (header
auth), citations and history are the chat's own and need nothing extra.

Start with ./run.sh or run.ps1 (uvicorn web.server:app on 127.0.0.1:8800).
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Chainlit reads .chainlit/config.toml, chainlit.md and public/ from its app root: keep using chat/ (set before import)
os.environ.setdefault("CHAINLIT_APP_ROOT", str(ROOT / "chat"))

from chainlit.utils import mount_chainlit  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from web import wiki  # noqa: E402

CHAT_PATH = "/chat"

app = FastAPI(title="Nod-Krai & Snezhnaya", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "web" / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return wiki.render("Genshin Impact: Nod-Krai and Snezhnaya", wiki.home_body(), CHAT_PATH)


@app.get("/wiki/{slug}", response_class=HTMLResponse)
def page(slug: str) -> str:
    p = wiki.pages().get(slug)
    if p is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return wiki.render(f"{p.title.removeprefix('Version/')} · Nod-Krai and Snezhnaya", wiki.page_body(p), CHAT_PATH)


mount_chainlit(app=app, target=str(ROOT / "chat" / "app.py"), path=CHAT_PATH)
