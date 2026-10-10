"""#18 overlap check on the real corpus + #20 normalization/metric check on the stored vectors."""
import bisect, collections, json
import numpy as np
from rag import chunking, index, config
from rag.contract import load_chunks

docs = {d["doc_id"]: d for d in chunking.load_docs()}
chunks = load_chunks(chunking.out_path("A"))
by_doc = collections.defaultdict(list)
for c in chunks: by_doc[c.doc_id].append(c)
tok = chunking.tokenizer()
steps, overlaps, sizes, bad = collections.Counter(), collections.Counter(), collections.Counter(), []
for did, cs in by_doc.items():
    text = "\n\n".join(chunking.render_block(b) for b in chunking.kept_blocks(docs[did]))
    offs = tok(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    starts_char = [o[0] for o in offs]
    idx = []
    pos = 0
    for c in cs:
        ch = text.find(c.text, pos); pos = ch
        idx.append(bisect.bisect_left(starts_char, ch))
    n = len(offs)
    for k in range(len(cs)):
        end = min(idx[k] + 512, n); sizes[end - idx[k]] += 0  # placeholder
        if k + 1 < len(cs):
            st = idx[k + 1] - idx[k]; steps[st] += 1
            ov = min(idx[k] + 512, n) - idx[k + 1]; overlaps[ov] += 1
            if ov != 64: bad.append((c.chunk_id, ov))
multi = sum(1 for cs in by_doc.values() if len(cs) > 1)
print(json.dumps({"A_chunks": len(chunks), "docs": len(by_doc), "docs_with_>1_window": multi,
                  "consecutive_pairs": sum(overlaps.values()), "window_step_tokens": dict(steps),
                  "overlap_tokens": dict(overlaps), "pairs_not_64": bad[:5]}, indent=2))

col = index.collection()
got = col.get(include=["embeddings", "metadatas"], limit=100000)
E = np.asarray(got["embeddings"], dtype=np.float32)
norms = np.linalg.norm(E, axis=1)
print(json.dumps({"collection": col.name, "stored_vectors": len(E), "dim": int(E.shape[1]),
    "norm_min": float(norms.min()), "norm_max": float(norms.max()),
    "collection_space": col.configuration.get("hnsw", {}).get("space") if hasattr(col, "configuration") else None,
    "collection_metadata": col.metadata,
    "by_strategy": dict(collections.Counter(m["strategy"] for m in got["metadatas"]))}, indent=2, default=str))
# cosine distance from Chroma == 1 - dot on unit vectors
q = index.embed(["What is the cooldown of Lauma's Elemental Skill?"])
r = col.query(query_embeddings=q, n_results=3, include=["embeddings", "distances"])
for d, e in zip(r["distances"][0], r["embeddings"][0]):
    print(f"chroma distance {d:.6f}  vs 1 - dot {1 - float(np.dot(q[0], e)):.6f}")
