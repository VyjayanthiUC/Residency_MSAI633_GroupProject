"""PDF extraction path (§2). The wiki hosts no native PDFs, so — as disclosed in the proposal — we print crawled pages
to PDF with a headless Chromium browser (Edge/Chrome) and extract them with pdfplumber, then compare against the HTML
extraction of the same pages. These are rendered PDFs, not crawled PDFs.

Inputs: the saved raw API responses (data/genshin/raw/<sha256>.json) — no network.
Outputs (git-ignored): artifacts/pdf/<doc_id>.pdf, <doc_id>.pdf.txt, and artifacts/pdf/comparison.json

Usage: uv run python -m ingest.pdfs [--browser PATH]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

from rag import chunking, config

RAW = config.RAW_DIR
MANIFEST = config.MANIFEST_PATH
OUT = config.ARTIFACTS / "pdf"

# Table-heavy pages: version pages (event-wish and new-content tables) plus one talent and one weapon page
PAGES = ["Version/Luna I", "Version/Luna IV", "Version/7.0", "Wish", "Runo: Dawnless Rest of Karsikko", "Athame Artis"]

BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "google-chrome", "chromium", "chromium-browser", "microsoft-edge"]

CSS = """body{font-family:Arial,Helvetica,sans-serif;font-size:10pt;margin:18px}
table{border-collapse:collapse;margin:6px 0}td,th{border:1px solid #888;padding:2px 4px;vertical-align:top}
img,figure,.mw-editsection,.navbox,script,style{display:none}"""


def find_browser(explicit: str | None) -> str:
    for b in ([explicit] if explicit else []) + BROWSERS:
        if b and (Path(b).exists() or shutil.which(b)):
            return b
    raise SystemExit("No Chromium-based browser found; pass --browser PATH")


def render(browser: str, title: str, body_html: str, pdf: Path) -> None:
    src = pdf.with_suffix(".html")
    src.write_text(f"<!doctype html><meta charset='utf-8'><title>{html.escape(title)}</title><style>{CSS}</style>"
                   f"<h1>{html.escape(title)}</h1>{body_html}", "utf-8")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", src.resolve().as_uri()], check=True, capture_output=True, timeout=120)


def extract(pdf: Path) -> dict:
    import pdfplumber
    text, tables = [], 0
    with pdfplumber.open(pdf) as doc:
        for page in doc.pages:
            text.append(page.extract_text() or "")
            tables += len(page.extract_tables())
        n_pages = len(doc.pages)
    return {"text": "\n".join(text), "tables": tables, "pages": n_pages}


_TOK = re.compile(r"[\w.%★]+", re.U)
_NUM = re.compile(r"\d+(?:\.\d+)?")


def compare(html_text: str, pdf_text: str) -> dict:
    """Token recall of the HTML extraction inside the PDF extraction (overall and for numbers)."""
    norm = lambda s: s.lower().replace(",", "")
    h_tok, p_tok = _TOK.findall(norm(html_text)), set(_TOK.findall(norm(pdf_text)))
    h_num, p_num = _NUM.findall(norm(html_text)), set(_NUM.findall(norm(pdf_text)))
    return {"token_recall": round(sum(t in p_tok for t in h_tok) / max(1, len(h_tok)), 4),
            "number_recall": round(sum(n in p_num for n in h_num) / max(1, len(h_num)), 4),
            "html_tokens": len(h_tok), "pdf_tokens": len(_TOK.findall(norm(pdf_text)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser")
    a = ap.parse_args()
    browser = find_browser(a.browser)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {json.loads(l)["title"]: json.loads(l) for l in open(MANIFEST, encoding="utf-8")}
    docs = {d["title"]: d for d in chunking.load_docs()}
    rows = []
    for title in PAGES:
        m, d = manifest[title], docs[title]
        parse = json.loads((RAW / f"{m['sha256']}.json").read_text("utf-8"))["parse"]
        pdf = OUT / f"{d['doc_id']}.pdf"
        render(browser, title, parse["text"], pdf)
        ex = extract(pdf)
        (pdf.with_suffix(".pdf.txt")).write_text(ex["text"], "utf-8")
        # compare against the HTML extraction of the same page (all blocks, as normalized in docs.jsonl)
        html_text = "\n".join(b["text"] for b in d["blocks"])
        html_tables = sum(1 for b in d["blocks"] if b["kind"] == "table")
        row = {"title": title, "doc_id": d["doc_id"], "pdf": pdf.name, "pdf_bytes": pdf.stat().st_size,
               "pages": ex["pages"], "html_tables": html_tables, "pdf_tables": ex["tables"], **compare(html_text, ex["text"])}
        rows.append(row)
        print(row)
    (OUT / "comparison.json").write_text(json.dumps({"browser": Path(browser).name, "pages": rows}, indent=2), "utf-8")
    print(f"{len(rows)} PDFs -> {OUT}")


if __name__ == "__main__":
    main()
