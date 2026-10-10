import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest_html import page_sections

HTML = """<div class="mw-parser-output">
<aside class="portable-infobox">
<h2 class="pi-title">Twine</h2>
<div class="pi-item pi-data" data-source="level"><h3 class="pi-data-label">Level</h3><div class="pi-data-value">2</div></div>
<div class="pi-item pi-data" data-source="description"><div class="pi-data-value">Burst is
 enhanced.</div></div>
</aside>
<p>"Twine" is
<a href="/wiki/Lauma">Lauma</a>'s Level 2 Constellation.</p>
<h2><span class="mw-headline" id="Attribute_Scaling">Attribute Scaling</span></h2>
<table><tr><th></th><th>1</th><th>10</th></tr>
<tr><th>Press DMG (%)</th><td>121.6</td><td>218.88</td></tr>
<tr><th>CD</th><td>12s</td><td>12s</td></tr></table>
<h2><span class="mw-headline" id="Other_Languages">Other Languages</span></h2>
<p>skip me</p>
</div>"""


def sections():
    return {"/".join(p): (a, t) for p, a, t in page_sections(HTML)}


def test_infobox_unlabeled_item_kept():
    intro = sections()["Intro"][1]
    assert "Level: 2" in intro
    assert "Description: Burst is enhanced." in intro


def test_inline_links_stay_in_sentence():
    assert "\"Twine\" is Lauma's Level 2 Constellation." in sections()["Intro"][1]


def test_table_rows_on_separate_lines_with_level_headers():
    anchor, text = sections()["Attribute Scaling"]
    assert anchor == "Attribute_Scaling"
    lines = text.splitlines()
    assert "Press DMG (%) — Lv1: 121.6; Lv10: 218.88" in lines
    assert "CD — Lv1: 12s; Lv10: 12s" in lines


def test_nested_table_keeps_rows():
    html = """<div class="mw-parser-output"><table><tr><td>
    <table><tr><th>Name</th><th>Gauge</th></tr><tr><td>Press DMG</td><td>1U</td></tr>
    <tr><td>Hold DMG</td><td>0U</td></tr></table></td></tr></table></div>"""
    text = page_sections(html)[0][2]
    assert "Press DMG — Gauge: 1U" in text.splitlines()
    assert "Hold DMG — Gauge: 0U" in text.splitlines()


def test_skipped_sections_dropped():
    assert "Other Languages" not in sections()
