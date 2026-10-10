"""Load the main namespace (ns0) of the Fandom XML dump into sqlite for offline page selection."""
import sqlite3, sys, xml.etree.ElementTree as ET
src, dst = sys.argv[1], sys.argv[2]
NS = "{http://www.mediawiki.org/xml/export-0.11/}"
db = sqlite3.connect(dst)
db.execute("DROP TABLE IF EXISTS pages")
db.execute("CREATE TABLE pages(title TEXT PRIMARY KEY, redirect TEXT, ts TEXT, len INT, text TEXT)")
n = 0
for _, el in ET.iterparse(src, events=("end",)):
    if el.tag != NS + "page":
        continue
    if el.findtext(NS + "ns") == "0":
        rev = el.find(NS + "revision")
        text = rev.findtext(NS + "text") or ""
        r = el.find(NS + "redirect")
        db.execute("INSERT OR REPLACE INTO pages VALUES(?,?,?,?,?)",
                   (el.findtext(NS + "title"), r.get("title") if r is not None else None,
                    rev.findtext(NS + "timestamp"), len(text), text))
        n += 1
    el.clear()
db.commit()
print("ns0 pages:", n)
