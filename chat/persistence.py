"""Conversation persistence: Chainlit's SQLAlchemyDataLayer + local SQLite.

Chainlit's chat-history sidebar requires both persistence and authentication to be enabled (see the Chat History docs).
The schema is the Postgres version from the official docs, with types adapted for SQLite (UUID/JSONB/TEXT[] -> TEXT).
The database lives at data/threads.sqlite (git-ignored); delete it to clear all history.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    "id" TEXT PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "metadata" TEXT NOT NULL,
    "createdAt" TEXT
);
CREATE TABLE IF NOT EXISTS threads (
    "id" TEXT PRIMARY KEY,
    "createdAt" TEXT,
    "name" TEXT,
    "userId" TEXT,
    "userIdentifier" TEXT,
    "tags" TEXT,
    "metadata" TEXT,
    FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS steps (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "threadId" TEXT NOT NULL,
    "parentId" TEXT,
    "streaming" BOOLEAN NOT NULL,
    "waitForAnswer" BOOLEAN,
    "isError" BOOLEAN,
    "metadata" TEXT,
    "tags" TEXT,
    "input" TEXT,
    "output" TEXT,
    "createdAt" TEXT,
    "command" TEXT,
    "start" TEXT,
    "end" TEXT,
    "generation" TEXT,
    "showInput" TEXT,
    "language" TEXT,
    "indent" INT,
    "defaultOpen" BOOLEAN,
    "autoCollapse" BOOLEAN,
    "icon" TEXT,
    "modes" TEXT,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS elements (
    "id" TEXT PRIMARY KEY,
    "threadId" TEXT,
    "type" TEXT,
    "url" TEXT,
    "chainlitKey" TEXT,
    "name" TEXT NOT NULL,
    "display" TEXT,
    "objectKey" TEXT,
    "size" TEXT,
    "page" INT,
    "language" TEXT,
    "forId" TEXT,
    "mime" TEXT,
    "props" TEXT,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS feedbacks (
    "id" TEXT PRIMARY KEY,
    "forId" TEXT NOT NULL,
    "threadId" TEXT NOT NULL,
    "value" INT NOT NULL,
    "comment" TEXT,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);
"""


# The schema in the official docs is older than Chainlit 2.12 (missing autoCollapse / icon; writes fail without them).
# If a Chainlit upgrade raises "has no column named X", add X to SCHEMA above and to this list.
LATER_COLUMNS = {"steps": {"autoCollapse": "BOOLEAN", "icon": "TEXT"}}


def init_db(path: Path) -> str:
    """Create tables and add missing columns to older databases (both idempotent); return the SQLAlchemy URL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        for table, cols in LATER_COLUMNS.items():
            have = {r[1] for r in db.execute(f"PRAGMA table_info({table})")}
            for col, typ in cols.items():
                if col not in have:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN "{col}" {typ}')
    return f"sqlite+aiosqlite:///{path}"


def history_from_thread(thread: dict) -> list[dict]:
    """Rebuild LLM conversation history from a persisted thread, so follow-ups still work after resuming.

    Assistant messages are stored as displayed, with a sources footer after "\\n\\n---\\n"; strip it here.
    """
    history = []
    for s in sorted(thread.get("steps", []), key=lambda s: s.get("createdAt") or ""):
        if s.get("type") == "user_message":
            history.append({"role": "user", "content": s.get("output") or ""})
        elif s.get("type") == "assistant_message" and s.get("output") and history:  # skip the welcome message
            history.append({"role": "assistant", "content": s["output"].split("\n\n---\n")[0]})
    return history
