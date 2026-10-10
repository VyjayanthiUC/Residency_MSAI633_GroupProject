"""#21 on a copy of the real store: rebuild twice -> identical IDs, page_type filter, delete by ID / doc_id."""
import sys, json, hashlib; sys.stdout.reconfigure(encoding="utf-8")
from rag import index, config
# this script deletes chunks: refuse to touch the evaluated index, run it on a copy via CHROMA_DIR
if index.CHROMA_DIR == (config.ARTIFACTS / "chroma").resolve():
    raise SystemExit("set CHROMA_DIR to a copy of artifacts/chroma (see README) — this script deletes chunks")
col = index.collection
h = lambda ids: hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()[:16]
before = index.stored_ids("B")
index.cmd_build("B"); run1 = index.stored_ids("B")
index.cmd_build("B"); run2 = index.stored_ids("B")
out = {"store": str(index.CHROMA_DIR), "B_ids_before": len(before), "after_build_1": len(run1), "after_build_2": len(run2),
       "ids_identical_1_vs_2": run1 == run2, "ids_identical_to_before": run1 == before, "ids_sha256": h(run2),
       "total_in_store_(A+B)": col().count()}
q = index.embed(["What is the CRIT DMG of A Teaspoon of Transcendence at level 90?"])
r = col().query(query_embeddings=q, n_results=5, where={"$and": [{"strategy": "B"}, {"page_type": "weapon"}]}, include=["metadatas"])
out["filter_page_type=weapon_top5"] = [(i, m["page_type"]) for i, m in zip(r["ids"][0], r["metadatas"][0])]
out["count_page_type_talent_B"] = index.count({"$and": [{"strategy": "B"}, {"page_type": "talent"}]})
victim = sorted(run2)[0]
col().delete(ids=[victim])
out["delete_by_id"] = {"id": victim, "still_present": bool(col().get(ids=[victim])["ids"]), "B_count_after": index.count({"strategy": "B"})}
doc = "gi-a-teaspoon-of-transcendence-c14b8fc3"
out["delete_by_doc_id"] = {"doc_id": doc, "deleted": index.delete_doc(doc), "remaining": index.count({"doc_id": doc})}
print(json.dumps(out, indent=2))
