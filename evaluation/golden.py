"""Golden set: loading, validation against the corpus, and the frozen dev/test split.

Relevance is strategy-independent: a chunk satisfies an evidence requirement when it comes from the named page AND
contains every needle string. Chunk IDs differ between strategies A and B, so IDs can't be the gold label.

Usage:
  uv run python -m evaluation.golden validate      # every needle must exist on its page, and in some A and some B chunk
  uv run python -m evaluation.golden split   # write evaluation/split.json (60/40, stratified by category, seed 633) — once
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rag.contract import Chunk

HERE = Path(__file__).parent
GOLDEN = HERE / "golden.jsonl"
SPLIT = HERE / "split.json"
SEED = 633
DEV_FRACTION = 0.6


def load(path: Path = GOLDEN) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _norm(s: str) -> str:
    return " ".join(s.lower().replace(" ", " ").split())


def alt_matches(chunk: Chunk, alt: dict) -> bool:
    return chunk.title == alt["title"] and all(_norm(n) in _norm(chunk.text) for n in alt["needles"])


def requirement_met(chunk: Chunk, requirement: list[dict]) -> bool:
    return any(alt_matches(chunk, alt) for alt in requirement)


def relevant(chunk: Chunk, item: dict) -> bool:
    return any(requirement_met(chunk, r) for r in item["evidence"])


def make_split(items: list[dict]) -> dict:
    rng = random.Random(SEED)
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it["category"]].append(it["id"])
    dev, test = [], []
    for cat in sorted(by_cat):
        ids = sorted(by_cat[cat])
        rng.shuffle(ids)
        k = round(len(ids) * DEV_FRACTION)
        dev += ids[:k]
        test += ids[k:]
    return {"seed": SEED, "dev_fraction": DEV_FRACTION, "dev": sorted(dev), "test": sorted(test)}


def split_items(name: str, items: list[dict] | None = None) -> list[dict]:
    items = items if items is not None else load()
    if name == "all":
        return items
    ids = set(json.loads(SPLIT.read_text("utf-8"))[name])
    return [it for it in items if it["id"] in ids]


def validate() -> int:
    from rag import chunking, index
    docs = {d["title"]: d for d in chunking.load_docs()}
    page_text = {t: _norm("\n".join(chunking.render_block(b) for b in chunking.kept_blocks(d))) for t, d in docs.items()}
    chunks = {s: index.load_strategy(s) for s in ("A", "B") if chunking.out_path(s).exists()}
    problems = 0
    items = load()
    for it in items:
        if it["expected_behavior"] == "answer" and not it["answer_keys"]:
            print(f"{it['id']}: answerable item without answer_keys"); problems += 1
        for r_i, req in enumerate(it["evidence"]):
            ok_alts = [a for a in req if a["title"] in page_text and all(_norm(n) in page_text[a["title"]] for n in a["needles"])]
            if not ok_alts:
                print(f"{it['id']} req{r_i}: no alternative found on its page: {req}"); problems += 1
                continue
            for s, cs in chunks.items():
                if not any(requirement_met(c, req) for c in cs):
                    print(f"{it['id']} req{r_i}: needles split across chunk boundaries in strategy {s}: {req}"); problems += 1
    print(f"{len(items)} items, categories {dict(Counter(i['category'] for i in items))}; "
          f"verified {sum(1 for i in items if i['verified_by'])}/{len(items)}; problems: {problems}")
    return problems


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "validate":
        sys.exit(1 if validate() else 0)
    if cmd == "split":
        if SPLIT.exists() and "--force" not in sys.argv:
            sys.exit(f"{SPLIT} already exists; the split is frozen (use --force only before any tuning)")
        sp = make_split(load())
        SPLIT.write_text(json.dumps(sp, indent=2), "utf-8")
        print(f"dev {len(sp['dev'])} / test {len(sp['test'])} -> {SPLIT}")


if __name__ == "__main__":
    main()
