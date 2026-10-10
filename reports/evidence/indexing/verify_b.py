"""#19: heading path is line 1 of every B chunk; split tables repeat their header row."""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import collections, json
from rag import chunking
from rag.contract import load_chunks
docs = {d["doc_id"]: d for d in chunking.load_docs()}
B = load_chunks(chunking.out_path("B"))
# 1. every chunk's first line == title > heading_path
bad_first = [c.chunk_id for c in B if c.text.split("\n")[0] != " > ".join([c.title, *c.heading_path])]
# 2. every table split across chunks: each piece starts its group with the same header line
headers = {}
for d in docs.values():
    for b in d["blocks"]:
        if b["kind"] == "table" and b.get("table"):
            headers.setdefault(d["doc_id"], set()).add(chunking.table_header(b["table"]))
split = collections.defaultdict(list)   # (doc, header) -> chunks containing it
for c in B:
    for h in headers.get(c.doc_id, ()):
        if h in c.text.split("\n"): split[(c.doc_id, h)].append(c.chunk_id)
multi = {k: v for k, v in split.items() if len(v) > 1}
# a data row ("X — Lv1: ..") must never appear in a chunk without its header above it
orphan_rows = 0
print(json.dumps({"B_chunks": len(B), "first_line_not_heading_path": len(bad_first), "examples": bad_first[:3],
                  "tables_split_across_chunks": len(multi),
                  "page_types": dict(collections.Counter(c.page_type for c in B))}, indent=2))
# show examples: one character talent table split, and one non-character table
def show(key):
    for cid in multi[key][:2]:
        c = next(x for x in B if x.chunk_id == cid)
        lines = c.text.split("\n"); i = lines.index(key[1])
        print(f"\n--- {cid}  page_type={c.page_type}  url={c.url}")
        print("\n".join(l[:150] for l in lines[:2] + ["..."] + lines[i:i+2]))
talent = next(k for k in multi if next(x for x in B if x.chunk_id == multi[k][0]).page_type == "talent" and "Lv1" in k[1])
other = next(k for k in multi if next(x for x in B if x.chunk_id == multi[k][0]).page_type == "weapon")
show(talent); show(other)
# every table row line in a B chunk must have a table header line above it in the same chunk
all_headers = {h for hs in headers.values() for h in hs}
rows_without_header = 0
for c in B:
    seen = False
    hs = headers.get(c.doc_id, set())
    rows = set()
    for b in docs[c.doc_id]["blocks"]:
        if b["kind"] == "table" and b.get("table"): rows.update(chunking.table_rows(b["table"]))
    for ln in c.text.split("\n"):
        if ln in hs: seen = True
        elif ln in rows and not seen: rows_without_header += 1
print("\nrow lines with no header above them in their chunk:", rows_without_header)
