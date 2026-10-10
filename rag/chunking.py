"""Stage 3 — chunking. Reads ONLY the saved normalized documents (never the network) and writes one chunk file per strategy.

Strategy A — fixed-size: 512-token windows with 64-token overlap over the page text, ignoring structure.
Strategy B — structure-aware: one section (heading path) at a time; the heading path is the first line of every chunk;
             small sibling sections under the same H2 are merged; tables are split by row groups with the header repeated.

Both strategies see the same text (same section filter, same table rendering), so the comparison isolates chunk boundaries.
Token counts use the embedding model's own tokenizer (config.EMBED_MODEL).

Chunk IDs are deterministic: "{doc_id}#{strategy}#{seq:04d}". Same docs.jsonl in -> same IDs out.

Usage: uv run python -m rag.chunking [--strategy A|B|both]
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from functools import lru_cache
from pathlib import Path

from rag import config
from rag.contract import Chunk

OUT_DIR = config.ARTIFACTS
A_SIZE, A_OVERLAP, B_MAX = config.A_SIZE, config.A_OVERLAP, config.B_MAX

# Sections with no question-answering value (translations, patch logs, media) — dropped for BOTH strategies
SKIP_SECTIONS = {"Other Languages", "Navigation", "References", "Gallery", "Voice-Overs", "Preview", "Talent Demo",
                 "Change History", "New Content", "Bug Fixes", "Adjustments & Optimizations",
                 "Post-patch Optimization & Fixes", "See Also", "Known Issues"}


@lru_cache(maxsize=1)
def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(config.EMBED_MODEL)


def n_tokens(text: str) -> int:
    return len(tokenizer()(text, add_special_tokens=False)["input_ids"])


def load_docs(path: Path = config.DOCS_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _level(h: str) -> str:
    return f"Lv{h}" if h.isdigit() else h


def table_header(table: dict) -> str:
    return " | ".join(_level(h) for h in table["headers"])


# Wiki table labels players don't type ("cooldown" never matches "CD"); expanded in place, original kept
LABEL_EXPANSIONS = {"CD": "CD (Cooldown)"}


def table_rows(table: dict) -> list[str]:
    """One self-describing line per row: "Skill DMG (%) — Lv1: 108.08; Lv2: 116.19; ..." when the row matches the header."""
    head = [_level(h) for h in table["headers"]]
    out = []
    for r in table["rows"]:
        if len(r) == len(head) and len(r) > 1:
            pairs = "; ".join(f"{h}: {v}" for h, v in zip(head[1:], r[1:]) if v)
            label = LABEL_EXPANSIONS.get(r[0], r[0]) or head[0]
            out.append(f"{label} — {pairs}" if label else pairs)
        else:
            out.append(" | ".join(c for c in r if c))
    return [ln for ln in out if ln.strip()]


def render_block(b: dict) -> str:
    if b["kind"] == "table" and b.get("table"):
        return "\n".join([table_header(b["table"]), *table_rows(b["table"])])
    return b["text"].strip()


def kept_blocks(doc: dict) -> list[dict]:
    return [b for b in doc["blocks"] if not SKIP_SECTIONS.intersection(b["heading_path"][1:]) and render_block(b)]


def anchor(path: list[str]) -> str:
    """MediaWiki section anchor for the deepest heading (path excludes the page title)."""
    real = [p for p in path if p != "Infobox"]
    return "#" + real[-1].replace(" ", "_") if real else ""


def make_chunk(doc: dict, strategy: str, seq: int, path: list[str], text: str) -> Chunk:
    return Chunk(
        chunk_id=f"{doc['doc_id']}#{strategy}#{seq:04d}",
        url=doc["source_url"] + anchor(path), title=doc["title"], heading_path=path,
        page_type=doc["page_type"], text=text, crawled_at=doc["crawled_at"],
        doc_id=doc["doc_id"], strategy=strategy, effective_date=doc.get("effective_date") or "",
    )


def chunk_fixed(doc: dict, size: int = A_SIZE, overlap: int = A_OVERLAP) -> list[Chunk]:
    text = "\n\n".join(render_block(b) for b in kept_blocks(doc))
    if not text:
        return []
    enc = tokenizer()(text, add_special_tokens=False, return_offsets_mapping=True)
    offs = enc["offset_mapping"]
    chunks, start, step = [], 0, size - overlap
    while start < len(offs):
        end = min(start + size, len(offs))
        piece = text[offs[start][0]:offs[end - 1][1]].strip()
        if piece:
            chunks.append(make_chunk(doc, "A", len(chunks), [], piece))
        if end == len(offs):
            break
        start += step
    return chunks


def _split_long(text: str, budget: int) -> list[str]:
    """Split one oversized paragraph on sentence ends, then hard-split by tokens as a last resort."""
    parts, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        cand = f"{cur} {sent}".strip()
        if cur and n_tokens(cand) > budget:
            parts.append(cur)
            cur = sent
        else:
            cur = cand
    if cur:
        parts.append(cur)
    out = []
    for p in parts:
        if n_tokens(p) <= budget:
            out.append(p)
            continue
        enc = tokenizer()(p, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
        for i in range(0, len(enc), budget):
            seg = enc[i:i + budget]
            out.append(p[seg[0][0]:seg[-1][1]])
    return out


def _section_units(blocks: list[dict], budget: int) -> list[str]:
    """Pack a section's blocks into text units of <= budget tokens. Tables split by row groups, header repeated."""
    units, cur = [], []

    def flush():
        if cur:
            units.append("\n".join(cur))
            cur.clear()

    for b in blocks:
        if b["kind"] == "table" and b.get("table"):
            head, rows = table_header(b["table"]), table_rows(b["table"])
            whole = "\n".join([head, *rows])
            if n_tokens("\n".join([*cur, whole])) <= budget:
                cur.append(whole)
                continue
            flush()
            # an overlong row is split into several rows, never truncated
            row_budget = budget - n_tokens(head) - 1
            pieces = (p for r in rows for p in ([r] if n_tokens(r) <= row_budget else _split_long(r, row_budget)))
            group = [head]
            for r in pieces:
                if len(group) > 1 and n_tokens("\n".join([*group, r])) > budget:
                    units.append("\n".join(group))
                    group = [head]
                group.append(r)
            if len(group) > 1:
                units.append("\n".join(group))
        else:
            for para in [p for p in render_block(b).split("\n") if p.strip()]:
                if n_tokens("\n".join([*cur, para])) <= budget:
                    cur.append(para)
                    continue
                flush()
                if n_tokens(para) <= budget:
                    cur.append(para)
                else:
                    units.extend(_split_long(para, budget))
    flush()
    return units


def chunk_structured(doc: dict, max_tokens: int = B_MAX) -> list[Chunk]:
    sections: list[tuple[list[str], list[dict]]] = []
    for b in kept_blocks(doc):
        path = b["heading_path"][1:]
        if sections and sections[-1][0] == path:
            sections[-1][1].append(b)
        else:
            sections.append((path, [b]))

    chunks: list[Chunk] = []
    buf: list[tuple[list[str], str]] = []  # (section path, text unit) waiting to be emitted as one chunk

    def render(entries: list[tuple[list[str], str]]) -> tuple[list[str], str]:
        """Chunk header = title > common heading prefix; deeper headings become "## sub" lines inside the chunk."""
        prefix = entries[0][0]
        for p, _ in entries[1:]:
            k = 0
            while k < min(len(prefix), len(p)) and prefix[k] == p[k]:
                k += 1
            prefix = prefix[:k]
        lines, last = [" > ".join([doc["title"], *prefix])], prefix
        for p, unit in entries:
            if p != last and len(p) > len(prefix):
                lines.append("## " + " > ".join(p[len(prefix):]))
            last = p
            lines.append(unit)
        return prefix, "\n".join(lines)

    def flush():
        if buf:
            path, text = render(buf)
            chunks.append(make_chunk(doc, "B", len(chunks), path, text))
            buf.clear()

    for path, blocks in sections:
        budget = max_tokens - n_tokens(" > ".join([doc["title"], *path])) - 2
        for unit in _section_units(blocks, budget):
            # merge small units into the open chunk while they stay under the same H2 and fit
            if buf and buf[-1][0][:1] == path[:1] and n_tokens(render([*buf, (path, unit)])[1]) <= max_tokens:
                buf.append((path, unit))
                continue
            flush()
            buf.append((path, unit))
    flush()
    return chunks


STRATEGIES = {"A": chunk_fixed, "B": chunk_structured}


def build(strategy: str, docs: list[dict] | None = None) -> list[Chunk]:
    docs = docs if docs is not None else load_docs()
    return [c for d in docs for c in STRATEGIES[strategy](d)]


def out_path(strategy: str) -> Path:
    return OUT_DIR / f"chunks_{strategy}.jsonl"


def write(chunks: list[Chunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_json(), ensure_ascii=False) + "\n")


def stats(chunks: list[Chunk]) -> dict:
    toks = sorted(n_tokens(c.text) for c in chunks)
    q = lambda p: toks[min(len(toks) - 1, int(p * len(toks)))]
    return {"chunks": len(chunks), "docs": len({c.doc_id for c in chunks}), "tokens_min": toks[0],
            "tokens_p25": q(.25), "tokens_median": int(statistics.median(toks)), "tokens_p75": q(.75),
            "tokens_p95": q(.95), "tokens_max": toks[-1], "tokens_total": sum(toks)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", choices=["A", "B", "both"], default="both")
    args = ap.parse_args()
    docs = load_docs()
    report = {}
    for s in (["A", "B"] if args.strategy == "both" else [args.strategy]):
        chunks = build(s, docs)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "duplicate chunk IDs"
        write(chunks, out_path(s))
        report[s] = stats(chunks)
        print(f"strategy {s}: {report[s]} -> {out_path(s)}")
    with open(OUT_DIR / "chunk_stats.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
