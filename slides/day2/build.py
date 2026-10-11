#!/usr/bin/env python3
"""Assemble index.html from template.html and sections/*.html (sorted by file name).

    python3 slides/day2/build.py
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
parts = [f"<!-- ===== {p.name} ===== -->\n{p.read_text()}" for p in sorted((HERE / "sections").glob("*.html"))]
page = (HERE / "template.html").read_text().replace("<!-- SECTIONS -->", "\n".join(parts))
# optional click-to-comment review layer (local tool, not in the repo)
review = (HERE / "review" / "comments.js").exists()
page = page.replace("<!-- REVIEW_CSS -->", '<link rel="stylesheet" href="review/comments.css">' if review else "")
page = page.replace("<!-- REVIEW_JS -->", '<script src="review/comments.js"></script>' if review else "")
missing = sorted({m for m in re.findall(r'src="(img/[^"]+)"', page) if not (HERE / m).exists()})
if missing:
    print(f"warning: {len(missing)} image(s) missing, run: python3 fetch_images.py  ({', '.join(missing)})")
(HERE / "index.html").write_text(page)
print(f"index.html: {len(parts)} section files, {page.count('class=\"slide')} slides")
