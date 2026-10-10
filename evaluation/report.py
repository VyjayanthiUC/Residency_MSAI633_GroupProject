"""Turn saved evaluation results into Markdown tables for the reports (with 95% bootstrap CIs and McNemar).

Usage: uv run python -m evaluation.run report --split dev     -> evaluation/results/summary_<split>.md
"""
from __future__ import annotations

import json
from pathlib import Path

from evaluation import golden
from evaluation.run import RESULTS, bootstrap_ci, mcnemar, mean, pct


def _load(name: str, split: str) -> dict | None:
    p = RESULTS / f"{name}_{split}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def _ci(xs) -> str:
    xs = [float(x) for x in xs if x is not None]
    if not xs:
        return "—"
    lo, hi = bootstrap_ci(xs)
    return f"{mean(xs):.3f} [{lo:.2f}, {hi:.2f}]"


def retrieval_table(res: dict) -> str:
    lines = ["| Config | n | Recall@5 | Recall@20 | MRR | nDCG@10 | p50 / p95 latency (s) |", "|---|---|---|---|---|---|---|"]
    for name, rows in res["data"].items():
        lat = [r["latency_s"] for r in rows]
        lines.append(f"| {name} | {len(rows)} | {_ci(r['recall@5'] for r in rows)} | {_ci(r['recall@20'] for r in rows)} | "
                     f"{_ci(r['mrr'] for r in rows)} | {_ci(r['ndcg@10'] for r in rows)} | {pct(lat, 50):.2f} / {pct(lat, 95):.2f} |")
    rr = res["data"].get("B3 hybrid/B+rerank")
    if rr:
        lines += ["", f"Reranker lift (B3, Recall@5 post vs pre-rerank on the same pool): "
                      f"{mean(r['recall@5'] for r in rr):.3f} vs {mean(r['recall@5_pre_rerank'] for r in rr):.3f}; "
                      f"Recall@20 ceiling {mean(r['recall@20'] for r in rr):.3f}."]
    return "\n".join(lines)


# One change at a time from B1 to B3, then the end-to-end baseline comparisons
ABLATION_STEPS = [("B1 bm25/A", "B2 dense/A"), ("B2 dense/A", "+struct dense/B"), ("+struct dense/B", "+hybrid hybrid/B"),
                  ("+hybrid hybrid/B", "B3 hybrid/B+rerank"), ("B2 dense/A", "B3 hybrid/B+rerank"), ("B1 bm25/A", "B3 hybrid/B+rerank")]


def ablation_table(res: dict) -> str:
    """Paired differences per step (95% bootstrap CI over per-item deltas) and McNemar on 'all evidence in the top 5'."""
    data = res["data"]
    lines = ["| Step | n | ΔRecall@5 | ΔMRR | ΔRecall@20 | McNemar: all evidence in top 5 (gained / lost, p) |",
             "|---|---|---|---|---|---|"]
    for a, b in ABLATION_STEPS:
        if not (data.get(a) and data.get(b)):
            continue
        ra, rb = {r["id"]: r for r in data[a]}, {r["id"]: r for r in data[b]}
        ids = sorted(set(ra) & set(rb))
        cells = []
        for k in ("recall@5", "mrr", "recall@20"):
            d = [rb[i][k] - ra[i][k] for i in ids]
            lo, hi = bootstrap_ci(d)
            cells.append(f"{mean(d):+.3f} [{lo:+.2f}, {hi:+.2f}]")
        t = mcnemar([{"id": i, "passed": ra[i]["recall@5"] == 1} for i in ids],
                    [{"id": i, "passed": rb[i]["recall@5"] == 1} for i in ids])
        lines.append(f"| {a} → {b} | {len(ids)} | " + " | ".join(cells)
                     + f" | +{t['a_fail_b_pass']} / −{t['a_pass_b_fail']}, p = {t['p_value']:.2f} |")
    return "\n".join(lines)


def generation_table(res: dict) -> str:
    lines = ["| Config | n | Pass rate | Correct (answerable) | Correct refusal (unanswerable) | Over-refusal (answerable) | "
             "Citation valid | Unsupported numbers / answer | Spend advice given | p50 latency (s) | Tokens / query |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, rows in res["data"].items():
        if not rows:
            continue
        ans = [r for r in rows if r["behavior"] == "answer"]
        una = [r for r in rows if r["behavior"] == "refuse"]
        rag = "has_citation" in rows[0]
        toks = [(r["prompt_tokens"] or 0) + (r["completion_tokens"] or 0) for r in rows if r.get("prompt_tokens")]
        lines.append(
            f"| {name} | {len(rows)} | {_ci(r['passed'] for r in rows)} | {_ci(r['passed'] for r in ans)} | "
            f"{_ci(r['refused'] for r in una)} | {_ci(r['refused'] for r in ans)} | "
            f"{_ci(r['citation_valid'] for r in ans if not r['refused']) if rag else 'n/a'} | "
            f"{mean(len(r['unsupported_numbers']) for r in rows) if rag else float('nan'):.2f} | "
            f"{sum(r.get('spend_advice', False) for r in rows) if rag else 'n/a'} | "
            f"{pct([r['latency_s'] for r in rows if r['latency_s']], 50):.2f} | {mean(toks):.0f} |")
    data = res["data"]
    pairs = [("B2 dense/A", "B3 hybrid/B+rerank"), ("B0 closed-book", "B3 hybrid/B+rerank"), ("B1 bm25/A", "B3 hybrid/B+rerank")]
    tests = [(a, b, mcnemar(data[a], data[b])) for a, b in pairs if data.get(a) and data.get(b)]
    if tests:
        lines += ["", "| McNemar (exact, per-item pass/fail) | n | A fail → B pass | A pass → B fail | p |", "|---|---|---|---|---|"]
        lines += [f"| {a} → {b} | {t['n_items']} | {t['a_fail_b_pass']} | {t['a_pass_b_fail']} | {t['p_value']:.3f} |"
                  for a, b, t in tests]
    b0 = {r["id"]: r["passed"] for r in data.get("B0 closed-book", [])}
    if b0:
        lines += ["", "**On the items B0 (closed-book) got wrong:**", "", "| Config | n | Pass rate |", "|---|---|---|"]
        for name, rows in data.items():
            sub = [r for r in rows if r["id"] in b0 and not b0[r["id"]]]
            if sub:
                lines.append(f"| {name} | {len(sub)} | {_ci(r['passed'] for r in sub)} |")
    return "\n".join(lines)


def failures(res: dict, config: str = "B3 hybrid/B+rerank") -> str:
    items = {i["id"]: i for i in golden.load()}
    rows = [r for r in res["data"].get(config, []) if not r["passed"]]
    if not rows:
        return "_No failures recorded for this configuration yet._"
    out = ["| Item | Category | Expected | Got (truncated) | Failure label (fill in) |", "|---|---|---|---|---|"]
    for r in rows:
        got = r["answer"].replace("\n", " ").replace("|", "/")[:160]
        out.append(f"| {r['id']} | {r['category']} | {items[r['id']]['gold_answer'] or r['behavior']} | {got} | |")
    return "\n".join(out)


def write_report(split: str) -> Path:
    parts = [f"# Evaluation summary — {split} split", ""]
    sp = json.loads(golden.SPLIT.read_text("utf-8"))
    parts += [f"Golden set: {len(golden.load())} items; split seed {sp['seed']}, dev {len(sp['dev'])} / test {len(sp['test'])}. "
              f"Verified by a human: {sum(1 for i in golden.load() if i['verified_by'])}.", ""]
    ret, gen, thr = _load("retrieval", split), _load("generation", split), _load("threshold", "dev")
    if ret:
        parts += ["## Retrieval (mean [95% bootstrap CI])", "", retrieval_table(ret), "",
                  "## Retrieval ablation (paired, one change per step)", "", ablation_table(ret), ""]
    if thr:
        c = thr["data"]["chosen"]
        parts += ["## Refusal threshold (tuned on dev)", "",
                  f"Top rerank score threshold {c['threshold']}: catches {c['caught_unanswerable']:.0%} of unanswerable dev items "
                  f"before generation, refuses {c['over_refusal']:.0%} of answerable dev items.", ""]
    if gen:
        parts += [f"## Generation (model `{gen['model']}`; mean [95% bootstrap CI])", "", generation_table(gen), "",
                  "## B3 failures (for error analysis)", "", failures(gen), ""]
    path = RESULTS / f"summary_{split}.md"
    path.write_text("\n".join(parts), "utf-8")
    print(f"-> {path}")
    return path
