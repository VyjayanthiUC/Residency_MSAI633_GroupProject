"""Retrieval spot checks that the golden-set metrics don't cover (§7–§8).

1. Metadata filtering: with page_types set, every pooled chunk carries an allowed type and the target page is still in
   the top 5 — for BM25, dense, and hybrid + rerank.
2. "Lauma constellation 2" (board item 3.4): rank of the chunk holding her C2 before and after reranking, both strategies.

Usage: uv run python -m evaluation.retrieval_checks      -> evaluation/results/retrieval_checks.json
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from evaluation.run import RESULTS
from rag import index
from rag.retrieval import Pipeline

FILTER_CASES = [
    ("What is Nightweaver's Looking Glass's base ATK at level 90?", ["weapon"], "Nightweaver's Looking Glass"),
    ("Lauma constellation 2", ["character"], "Lauma"),
    ("What does Lunar-Bloom do?", ["mechanic"], "Lunar-Bloom"),
]
MODES = [("bm25", False), ("dense", False), ("hybrid", True)]
C2_NEEDLE = "Twine Warnings and Tales From the North"  # name of Lauma's 2nd constellation, on her character page
C2_QUERIES = ["Lauma constellation 2", "What does Lauma's 2nd constellation do?"]


def filter_checks() -> list[dict]:
    rows = []
    for query, types, target in FILTER_CASES:
        for mode, rerank in MODES:
            for page_types in (None, types):
                pool, final = Pipeline("B", mode, rerank, page_types).retrieve(query)
                rows.append({"query": query, "mode": mode + ("+rerank" if rerank else ""), "page_types": page_types,
                             "pool": len(pool), "types_in_pool": sorted({c.page_type for c in pool}),
                             "violations": sum(1 for c in pool if page_types and c.page_type not in page_types),
                             "target_rank_top5": next((i for i, c in enumerate(final, 1) if c.title == target), None)})
    return rows


def c2_checks() -> list[dict]:
    rows = []
    for query in C2_QUERIES:
        for strategy in ("A", "B"):
            for mode, rerank in (("dense", False), ("hybrid", False), ("hybrid", True)):
                t0 = time.perf_counter()
                pool, final = Pipeline(strategy, mode, rerank).retrieve(query)
                dt = time.perf_counter() - t0
                post = sorted(pool, key=lambda c: c.score_post, reverse=True)
                rows.append({"query": query, "strategy": strategy, "mode": mode + ("+rerank" if rerank else ""),
                             "rank_pre_rerank": next((i for i, c in enumerate(pool, 1) if C2_NEEDLE in c.text), None),
                             "rank_final": next((i for i, c in enumerate(post, 1) if C2_NEEDLE in c.text), None),
                             "top_score": round(final[0].score_post, 4) if final else None, "latency_s": round(dt, 2)})
    return rows


def main():
    for strategy in ("A", "B"):
        index.check_in_sync(strategy)
    out = {"created_at": datetime.now(timezone.utc).isoformat(), "filter": filter_checks(), "lauma_c2": c2_checks()}
    bad = sum(r["violations"] for r in out["filter"])
    missed = [r for r in out["filter"] if r["page_types"] and r["target_rank_top5"] is None]
    print(f"metadata filter: {bad} out-of-filter chunks, {len(missed)} filtered runs missing the target page")
    for r in out["lauma_c2"]:
        print(f"C2 {r['strategy']} {r['mode']:13} pre {r['rank_pre_rerank']}  final {r['rank_final']}  "
              f"top {r['top_score']}  {r['latency_s']}s  | {r['query']}")
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / "retrieval_checks.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
