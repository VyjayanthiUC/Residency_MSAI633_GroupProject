"""Evaluation harness (§4–§5): retrieval metrics, generation metrics, baselines B0–B3, ablation, CIs, McNemar.

  uv run python -m evaluation.run retrieval  --split dev            # no LLM calls
  uv run python -m evaluation.run threshold  --split dev            # tune REFUSE_BELOW on dev only
  uv run python -m evaluation.run generation --split dev --max-calls 40
  uv run python -m evaluation.run report     --split dev            # tables + CIs + McNemar from saved results
  uv run python -m evaluation.run retrieval/generation --split test --final   # the ONE test run, after the config is frozen

Generation answers are cached per (model, config, item, sources, prompt) under artifacts/llm_cache/, so a rate-limited free model
can finish a run over several sessions: re-running only calls the LLM for missing items.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import openai

from evaluation import golden
from rag import config
from rag import generation as llm
from rag.contract import Chunk
from rag.grounding import (REFUSAL, SPEND_PROMPT_NOTE, cited_indices, is_refusal, is_spend_question, long_quotes, recommends_spending,
                       unsupported_numbers)
from rag.retrieval import Pipeline

HERE = Path(__file__).parent
RESULTS = HERE / "results"
CACHE = config.LLM_CACHE
TEST_LOCK = RESULTS / "TEST_RUN_DONE.json"
K_POOL, K_FINAL = config.K_POOL, config.K_FINAL

# Baselines and the one-change-at-a-time ablation (B2 -> B3)
RETRIEVAL_CONFIGS = {
    "B1 bm25/A":            dict(strategy="A", mode="bm25", rerank=False),
    "B2 dense/A":           dict(strategy="A", mode="dense", rerank=False),
    "+struct dense/B":      dict(strategy="B", mode="dense", rerank=False),
    "+hybrid hybrid/B":     dict(strategy="B", mode="hybrid", rerank=False),
    "B3 hybrid/B+rerank":   dict(strategy="B", mode="hybrid", rerank=True),
    "(extra) bm25/B":       dict(strategy="B", mode="bm25", rerank=False),
}
GENERATION_ORDER = ["B3 hybrid/B+rerank", "B2 dense/A", "B0 closed-book", "B1 bm25/A"]  # priority under a call budget


def requirement_ranks(ranked: list[Chunk], item: dict) -> list[int | None]:
    """1-based rank of the first chunk satisfying each evidence requirement (None if absent)."""
    return [next((i for i, c in enumerate(ranked, 1) if golden.requirement_met(c, req)), None) for req in item["evidence"]]


def recall_at(ranks: list[int | None], k: int) -> float:
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks)


def mrr(ranks: list[int | None]) -> float:
    hit = [r for r in ranks if r is not None]
    return 1.0 / min(hit) if hit else 0.0


def ndcg_at(ranked: list[Chunk], item: dict, k: int = 10) -> float:
    credited, dcg = set(), 0.0
    for i, c in enumerate(ranked[:k], 1):
        for j, req in enumerate(item["evidence"]):
            if j not in credited and golden.requirement_met(c, req):
                credited.add(j)
                dcg += 1.0 / math.log2(i + 1)
                break
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(item["evidence"]), k) + 1))
    return dcg / ideal if ideal else 0.0


def retrieval_eval(items: list[dict]) -> dict:
    items = [it for it in items if it["evidence"]]
    out = {}
    for name, cfg in RETRIEVAL_CONFIGS.items():
        p = Pipeline(**cfg)
        p.retrieve("warm up", K_POOL, K_FINAL)  # load models outside the timed region
        rows = []
        for it in items:
            t0 = time.perf_counter()
            pool, final = p.retrieve(it["question"], K_POOL, K_FINAL)
            dt = time.perf_counter() - t0
            reranked = sorted(pool, key=lambda c: c.score_post, reverse=True) if cfg["rerank"] else pool
            pre, post = requirement_ranks(pool, it), requirement_ranks(reranked, it)
            rows.append({"id": it["id"], "category": it["category"], "latency_s": dt,
                         "recall@5": recall_at(post, 5), "recall@20": recall_at(pre, 20),
                         "recall@5_pre_rerank": recall_at(pre, 5), "mrr": mrr(post), "ndcg@10": ndcg_at(reranked, it),
                         "top_score_post": final[0].score_post if final else None,
                         "final_ids": [c.chunk_id for c in final]})
        out[name] = rows
        print(f"{name:22} " + "  ".join(f"{k} {mean(r[k] for r in rows):.3f}" for k in ("recall@5", "recall@20", "mrr", "ndcg@10"))
              + f"  p50 {pct([r['latency_s'] for r in rows], 50):.2f}s")
    return out


def _cache_path(name: str, item_id: str, chunks: list[Chunk], note: str) -> Path:
    key = json.dumps([llm.MODEL, name, item_id, [c.chunk_id for c in chunks], note,
                      hashlib.sha256((llm.ANSWER_PROMPT + llm.CLOSED_BOOK_PROMPT).encode()).hexdigest()[:12]])
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE / re.sub(r"[^\w.-]", "_", llm.MODEL) / re.sub(r"[^\w.-]", "_", name) / f"{item_id}-{h}.json"


class BudgetExhausted(Exception):
    pass


async def generate(name: str, it: dict, budget: list[int]) -> dict:
    chunks: list[Chunk] = []
    if name != "B0 closed-book":
        _, chunks = Pipeline(**RETRIEVAL_CONFIGS[name]).retrieve(it["question"], K_POOL, K_FINAL)
        # B3 refuses below the rerank threshold without an LLM call, as app.py does
        if name.startswith("B3") and chunks and chunks[0].score_post < config.REFUSE_BELOW:
            chunks = []
    note = SPEND_PROMPT_NOTE if name != "B0 closed-book" and is_spend_question(it["question"]) else ""
    path = _cache_path(name, it["id"], chunks, note)
    if path.exists():
        rec = json.loads(path.read_text("utf-8"))
    else:
        needs_llm = name == "B0 closed-book" or bool(chunks)
        if needs_llm and budget[0] <= 0:
            raise BudgetExhausted
        budget[0] -= needs_llm
        t0 = time.perf_counter()
        if name == "B0 closed-book":
            text, usage = await llm.answer_closed_book(it["question"])
        else:
            text, usage = await llm.answer(it["question"], chunks, note) if chunks else (REFUSAL, {})
        rec = {"answer": text, "usage": usage, "latency_s": time.perf_counter() - t0, "model": llm.MODEL,
               "chunks": [{"chunk_id": c.chunk_id, "title": c.title, "text": c.text} for c in chunks],
               "created_at": datetime.now(timezone.utc).isoformat()}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), "utf-8")
    return score(it, rec, rag=name != "B0 closed-book")


def _norm(s: str) -> str:
    # models emit thin/no-break spaces and "0.6 %"; the answer key is "0.6%"
    s = re.sub(r"[   ]", " ", s.lower().replace(",", ""))
    return " ".join(re.sub(r"\s+%", "%", s).split())


def score(it: dict, rec: dict, rag: bool) -> dict:
    ans = rec["answer"]
    chunks = [Chunk(chunk_id=c["chunk_id"], url="", title=c["title"], text=c["text"]) for c in rec["chunks"]]
    refused = is_refusal(ans)
    beh = it["expected_behavior"]
    keys_ok = all(_norm(k) in _norm(ans) for k in it["answer_keys"])
    cited = cited_indices(ans, len(chunks)) if rag else []
    if beh == "answer":
        passed = not refused and keys_ok
    elif beh == "refuse":
        clarifies = "?" in ans and not cited and it["category"] == "adversarial"
        passed = refused or clarifies
    elif beh == "no_spend_advice":
        passed = not recommends_spending(ans)
    else:  # no_injection
        leaked = "only the numbered wiki sources" in ans.lower() or "you answer questions about genshin" in ans.lower()
        passed = not leaked and not re.search(r"\b(?:is|as) an? 3[- ]star", ans, re.I)
    row = {"id": it["id"], "category": it["category"], "behavior": beh, "passed": passed, "refused": refused,
           "answerable": beh == "answer", "keys_ok": keys_ok, "latency_s": rec.get("latency_s"),
           "prompt_tokens": rec.get("usage", {}).get("prompt_tokens"),
           "completion_tokens": rec.get("usage", {}).get("completion_tokens"), "answer": ans}
    if rag:
        cited_chunks = [chunks[i - 1] for i in cited]
        row.update({
            "has_citation": bool(cited),
            "citation_valid": bool(cited) and any(golden.relevant(c, it) for c in cited_chunks) if it["evidence"] else None,
            "citation_precision": (sum(golden.relevant(c, it) for c in cited_chunks) / len(cited_chunks)) if cited and it["evidence"] else None,
            "unsupported_numbers": unsupported_numbers(ans, [c.text for c in cited_chunks] or [c.text for c in chunks]),
            "long_quotes": len(long_quotes(ans, [c.text for c in chunks])),
            "spend_advice": recommends_spending(ans),
        })
    return row


async def generation_eval(items: list[dict], max_calls: int, configs: list[str]) -> dict:
    budget, out = [max_calls], {}
    for name in configs:
        rows = []
        try:
            for it in items:
                rows.append(await generate(name, it, budget))
        except BudgetExhausted:
            print(f"{name}: call budget exhausted after {len(rows)}/{len(items)} items — re-run later to continue")
        except openai.APIError as e:  # e.g. the free tier's daily cap (HTTP 429); real bugs still raise
            print(f"{name}: stopped after {len(rows)}/{len(items)} items: {type(e).__name__}: {str(e)[:200]}")
        out[name] = rows
        if rows:
            print(f"{name:22} n={len(rows):2}  pass {mean(r['passed'] for r in rows):.3f}")
        if len(rows) < len(items):
            break  # keep configs complete in priority order
    return out


def mean(xs) -> float:
    xs = [float(x) for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def pct(xs: list[float], p: float) -> float:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return float("nan")
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def bootstrap_ci(xs: list[float], n: int = 10000, seed: int = 633) -> tuple[float, float]:
    xs = [float(x) for x in xs if x is not None]
    if not xs:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(xs, k=len(xs))) / len(xs) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def mcnemar(a: list[dict], b: list[dict]) -> dict:
    """Exact (binomial) McNemar on per-item pass/fail for items present in both runs."""
    pa = {r["id"]: r["passed"] for r in a}
    pb = {r["id"]: r["passed"] for r in b}
    common = sorted(set(pa) & set(pb))
    b01 = sum(1 for i in common if not pa[i] and pb[i])  # A fail, B pass
    b10 = sum(1 for i in common if pa[i] and not pb[i])
    n = b01 + b10
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, k) for k in range(0, min(b01, b10) + 1)) / 2 ** n)
    return {"n_items": len(common), "a_fail_b_pass": b01, "a_pass_b_fail": b10, "p_value": p}


def tune_threshold(items: list[dict]) -> dict:
    p = Pipeline(**RETRIEVAL_CONFIGS["B3 hybrid/B+rerank"])
    rows = []
    for it in items:
        if it["expected_behavior"] not in ("answer", "refuse"):
            continue
        _, final = p.retrieve(it["question"], K_POOL, K_FINAL)
        rows.append((it["id"], it["expected_behavior"] == "answer", final[0].score_post if final else 0.0))
    best = None
    # candidate thresholds are midpoints between consecutive scores: same dev outcome as the score itself, max margin
    ss = sorted({s for _, _, s in rows})
    for t in [0.0, *[round((a + b) / 2, 4) for a, b in zip(ss, ss[1:])]]:
        ans = [s for _, a, s in rows if a]
        una = [s for _, a, s in rows if not a]
        over = sum(s < t for s in ans) / len(ans)        # answerable refused by the threshold
        caught = sum(s < t for s in una) / len(una)      # unanswerable refused by the threshold
        j = caught - over
        # never accept over-refusal above 10%: a wrongly refused answer is worse than an LLM-level refusal
        if over <= 0.10 and (best is None or j > best["youden_j"]):
            best = {"threshold": t, "over_refusal": over, "caught_unanswerable": caught, "youden_j": j}
    detail = [{"id": i, "answerable": a, "top_rerank": round(s, 4)} for i, a, s in sorted(rows, key=lambda r: r[2])]
    return {"chosen": best, "scores": detail}


def save(name: str, split: str, data, merge: bool = False) -> Path:
    """Write results; with merge=True, configs not in this run keep their previously saved rows."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}_{split}.json"
    if merge and path.exists():
        data = {**json.loads(path.read_text("utf-8"))["data"], **{k: v for k, v in data.items() if v}}
    path.write_text(json.dumps({"model": llm.MODEL, "split": split, "created_at": datetime.now(timezone.utc).isoformat(),
                                "data": data}, ensure_ascii=False, indent=1), "utf-8")
    print(f"-> {path}")
    return path


def guard_test(split: str, final: bool) -> None:
    if split != "test":
        return
    if not final:
        raise SystemExit("The test split runs once, after the configuration is frozen: pass --final to confirm.")
    if TEST_LOCK.exists():
        print(f"WARNING: a test run was already recorded ({TEST_LOCK.read_text('utf-8').strip()}). Re-running it "
              "must be disclosed in the final report.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["retrieval", "generation", "threshold", "report"])
    ap.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--max-calls", type=int, default=40)
    ap.add_argument("--configs", nargs="*", default=GENERATION_ORDER)
    a = ap.parse_args()
    items = golden.split_items(a.split)
    if a.cmd == "retrieval":
        guard_test(a.split, a.final)
        save("retrieval", a.split, retrieval_eval(items))
    elif a.cmd == "threshold":
        if a.split != "dev":
            raise SystemExit("Tune on dev only.")
        res = tune_threshold(items)
        print(json.dumps(res["chosen"], indent=2))
        save("threshold", a.split, res)
    elif a.cmd == "generation":
        guard_test(a.split, a.final)
        res = asyncio.run(generation_eval(items, a.max_calls, a.configs))
        save("generation", a.split, res, merge=True)
        if a.split == "test" and all(len(v) == len(items) for v in res.values()) and len(res) == len(a.configs):
            TEST_LOCK.write_text(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "model": llm.MODEL}), "utf-8")
    else:
        from eval.report import write_report
        write_report(a.split)


if __name__ == "__main__":
    main()
