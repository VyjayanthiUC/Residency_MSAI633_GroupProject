# FanBot architecture

Current system as of `main` (`f069c90`) — offline ingestion/indexing, the FastAPI serving layer, the live chat request
flow, and the evaluation harness. See `README.md` for the repository layout and `reports/` for the measured numbers
behind each stage.

```mermaid
flowchart TD
    %% ===== Offline: ingestion & indexing (no live traffic) =====
    subgraph OFFLINE["Offline pipeline — no live traffic"]
        DUMP["Fandom XML dump<br/>(offline page selection)"] --> SELECT["select_pages.py"]
        SELECT --> CRAWL["crawl.py<br/>≤1 req/s · robots.txt · MediaWiki API"]
        CRAWL --> RAW[("raw/ + manifest.jsonl<br/>337 pages, SHA-256 verified")]
        RAW --> EXTRACT["extract.py<br/>strip boilerplate · tables→grids · dedupe"]
        EXTRACT --> DOCS[("docs.jsonl + normalized/md<br/>337 docs, 2.5M chars")]
        DOCS --> CHUNKA["Chunking A<br/>fixed 512/64 tokens"]
        DOCS --> CHUNKB["Chunking B<br/>structure-aware, heading path"]
        CHUNKA --> EMBED["bge-m3 embeddings<br/>1024-d, L2-normalized"]
        CHUNKB --> EMBED
        EMBED --> CHROMA[("Chroma vector store<br/>3,563 chunks · cosine")]
    end

    %% ===== Serving layer =====
    subgraph SERVE["Serving — one FastAPI origin (web/server.py)"]
        SITE["/ — browsable wiki site<br/>web/wiki.py, built from normalized/md"]
        CHATUI["/chat — Chainlit app<br/>chat/app.py, mounted as iframe"]
    end

    %% ===== Live chat request flow =====
    subgraph FLOW["Chat request flow"]
        USERQ["User question"] --> CC{"Greeting /<br/>small talk?"}
        CC -->|yes| WELCOME["Welcome message<br/>EN / 中文 — no retrieval"]
        CC -->|no| REWRITE["Query rewrite (LLM)<br/>resolves follow-ups, history-aware"]
        REWRITE --> BM25["BM25"]
        REWRITE --> DENSE["Dense (bge-m3 / Chroma)"]
        BM25 --> RRF["Hybrid fusion (RRF)<br/>pool = 20"]
        DENSE --> RRF
        RRF --> RERANK["Cross-encoder reranker<br/>bge-reranker-v2-m3 → top 5"]
        RERANK --> GATE{"Top score<br/>below 0.52?"}
        GATE -->|yes| REFUSE["Refuse — no LLM call<br/>language-aware refusal text"]
        GATE -->|no| GEN["Generation LLM<br/>context-only · numbered [Sn] citations"]
        GEN --> GUARD["Safeguards:<br/>citation parse · number check ·<br/>quote-limit · referral · spend-advice"]
        GUARD --> ANSWER["Answer: citations + retrieval<br/>trace + safeguard notes"]
        REFUSE --> ANSWER
    end

    CHROMA --> DENSE
    CHATUI --> USERQ

    %% ===== Evaluation harness (offline) =====
    subgraph EVALH["Evaluation (offline)"]
        GOLDEN[("golden.jsonl<br/>53 human-verified items")] --> HARNESS["evaluation.run<br/>retrieval / generation / threshold"]
        HARNESS --> REPORTS["reports/01–07<br/>bootstrap CIs · McNemar · failure analysis"]
    end
    RRF -.-> HARNESS
    GEN -.-> HARNESS
```

## Notes

- **Two chunking strategies** are both indexed and compared (report 02, 04); **B is used in the live pipeline** because
  it preserves heading paths and table headers that cited answers need.
- **The refusal gate runs before any LLM call** — if the top reranked score is below `REFUSE_BELOW` (0.52, tuned on
  dev), the bot refuses without spending a generation call.
- **Chitchat bypass**: greetings/thanks/"who are you" skip retrieval entirely and get a canned welcome message (EN or
  中文, detected from the question).
- **Safeguards run on every generated answer**, not just a special-cased subset: citation parsing/validity, a
  verbatim-number check against the cited sources, a 25-word quote-length cap, a human-referral detector (payments,
  refunds, account issues), and a spend-advice guard (facts only, never a pull/spend recommendation).
- The retrieval pool and the generation LLM both feed the **evaluation harness**, which is how reports 04–06 get their
  Recall@k/MRR/nDCG numbers and answer-correctness/refusal metrics with bootstrap CIs and McNemar tests.
