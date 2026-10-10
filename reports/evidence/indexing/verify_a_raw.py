"""Recompute A windows exactly as chunk_fixed does, before .strip(): step and overlap in token indices."""
import collections
from rag import chunking
tok = chunking.tokenizer()
ov, ws_start = collections.Counter(), 0
for d in chunking.load_docs():
    text = "\n\n".join(chunking.render_block(b) for b in chunking.kept_blocks(d))
    if not text: continue
    offs = tok(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    wins, start = [], 0
    while start < len(offs):
        end = min(start + 512, len(offs)); wins.append((start, end))
        raw = text[offs[start][0]:offs[end-1][1]]
        if start and raw != raw.lstrip(): ws_start += 1
        if end == len(offs): break
        start += 448
    for (s1, e1), (s2, _) in zip(wins, wins[1:]): ov[e1 - s2] += 1
print("overlap of consecutive raw windows:", dict(ov), "| windows starting with whitespace (stripped):", ws_start)
