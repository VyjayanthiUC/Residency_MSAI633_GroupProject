import sqlite3

from chat.persistence import history_from_thread, init_db


def test_init_db_idempotent(tmp_path):
    db = tmp_path / "t.sqlite"
    url = init_db(db)
    init_db(db)
    assert url == f"sqlite+aiosqlite:///{db}"
    tables = {r[0] for r in sqlite3.connect(db).execute("select name from sqlite_master where type='table'")}
    assert {"users", "threads", "steps", "elements", "feedbacks"} <= tables


def test_init_db_migrates_old_steps_table(tmp_path):
    db = tmp_path / "old.sqlite"
    with sqlite3.connect(db) as c:  # database created from the older documented schema: no autoCollapse / icon
        c.execute('CREATE TABLE steps ("id" TEXT PRIMARY KEY, "name" TEXT NOT NULL)')
    init_db(db)
    cols = {r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(steps)")}
    assert {"autoCollapse", "icon"} <= cols


def test_history_from_thread_skips_welcome_and_strips_footer():
    thread = {"steps": [
        {"type": "assistant_message", "output": "Ask me about...", "createdAt": "1"},
        {"type": "user_message", "output": "Lauma skill lv10?", "createdAt": "2"},
        {"type": "retrieval", "output": "| # | ...", "createdAt": "3"},
        {"type": "assistant_message", "output": "218.88% S1\n\n---\n**Sources:** S1 Lauma", "createdAt": "4"},
        {"type": "user_message", "output": "and C2?", "createdAt": "5"},
    ]}
    assert history_from_thread(thread) == [
        {"role": "user", "content": "Lauma skill lv10?"},
        {"role": "assistant", "content": "218.88%"},  # old-turn S1 badge dropped
        {"role": "user", "content": "and C2?"},
    ]
