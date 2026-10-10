# Project Proposal — A Cited Q&A Assistant for Genshin Impact Players

**MSAI 633 Residency · Day 1 · October 9, 2026**
**Repository:** https://github.com/VyjayanthiUC/Residency_MSAI633_GroupProject

---

## 0. Hypothesis and Research Grounding

**Hypothesis.** On a scraped, table-heavy game-wiki corpus, a pipeline that combines *structure-aware chunking*, *hybrid (BM25 + dense) retrieval*, and *cross-encoder reranking* (B3) will achieve significantly higher answer correctness and correct-refusal rate than a dense-only retriever over naive fixed-size chunks (B2), measured on a human-verified golden set with a 95% bootstrap confidence interval or McNemar's test.

**Supporting sources.**

1. Lewis et al. (2020) introduced retrieval-augmented generation and showed that conditioning a generator on retrieved passages improves factual accuracy on knowledge-intensive tasks compared with parametric-only models. This motivates our B0 (closed-book) vs. retrieval comparison.
2. Karpukhin et al. (2020) showed that dense passage retrieval outperforms BM25 on open-domain QA — the basis for our dense retriever and for including dense retrieval in the hybrid.
3. Cormack, Clarke, and Buettcher (2009) showed that Reciprocal Rank Fusion of multiple rankers outperforms the individual rankers — the fusion method we use for hybrid retrieval.
4. Nogueira and Cho (2019) showed that a BERT cross-encoder reranking a BM25 candidate pool yields large ranking gains — the basis for our reranking stage and our Recall@20-as-ceiling analysis.
5. Es et al. (2024) proposed RAGAS, separating retrieval quality from answer faithfulness in RAG evaluation — the framing behind reporting retrieval metrics and grounded-answer metrics separately.

**Opposing sources.**

1. Thakur et al. (2021), the BEIR benchmark, found that BM25 remains a strong baseline and that dense retrievers often fail to beat it out of domain. Our corpus (game-specific names and terms) is exactly such a domain, so dense retrieval may *not* help — we test this directly with B1 (BM25 only) vs. B2.
2. Liu et al. (2024), "Lost in the Middle," found that LLMs use information at the start and end of long contexts far better than information in the middle. More retrieved context is not automatically better, which is why we cap generation context at the top 5 reranked chunks and measure over-refusal.

---

## 1. Team Composition and Roles

| Member | GitHub | Role | Owns |
|---|---|---|---|
| Gudla, Shyamala Keerthi | @ShyamalaKeerthi | Product Manager | Scope, schedule, issue board, presentation |
| Kamath, Vyjayanthi (VJ) | @VyjayanthiUC | Lead Analyst | Repository admin, golden set review, final performance report |
| Konkayala, Deep | _[handle]_ | AI Engineer / Architect | Embedding, retrieval, reranking |
| Daniel, Ibukun | @ibkcode | _[role]_ | _[stages]_ |
| Ban, Sohyun | _[handle]_ | _[role]_ | _[stages]_ |
| Akpe, Oyin | @oyinakpe2-firstgrandprince | _[role]_ | _[stages]_ |
| Li, Yanwei | @Saweisra | Data & Evaluation Engineer | Crawl, extraction, golden set, evaluation harness |

Every member commits under their own GitHub account across more than one pipeline stage; ownership is tracked in GitHub Issues.

---

## 2. Domain and Corpus Plan

**Domain (§1.1, "another industry": consumer gaming).** Genshin Impact is a free-to-play game monetized through gacha ("wishes"): players spend real money on randomized pulls from limited-time banners, and they make those decisions from fan-wiki information — pity rules, banner dates, and character kits. A wrong answer costs a player money, and a cited answer carries an authority an uncited forum post does not.

**Source site.** Genshin Impact Fandom wiki (`genshin-impact.fandom.com`), CC BY-SA, public and unauthenticated. Scope: the two newest regions, Nod-Krai and Snezhnaya (game versions 6.0–7.1, September 2025 onward). Most of this content post-dates the training cutoff of current LLMs, which makes the closed-book baseline (B0) informative.

**Page selection.** Pages are selected *offline* from the wiki's official XML dump (generated 2026-09-30) by infobox fields — so no discovery traffic hits the live site. The selection list is the crawler's only input.

| Page type | Pages |
|---|---|
| Playable characters / upcoming characters | 18 / 2 |
| Talents / constellations | 123 / 108 |
| Event wishes (banners) | 13 |
| Weapons / artifact sets | 40 / 8 |
| Version pages (6.0–7.1) | 10 |
| Game mechanics (wish rules, reactions) | 15 |
| **Core tier (crawled)** | **337** |
| Lore tier (optional expansion) | 266 |

**Status (Friday).** The core tier is already crawled (337/337 pages, 30 MB raw) and extracted: **828 tables** preserved as tables, 0 duplicates by content hash.

**PDFs.** The wiki hosts **no native PDFs** (verified via the MediaWiki API by MIME type). To exercise the PDF extraction path required by §2, we will render ≥5 crawled pages (e.g., version pages with tables) to PDF and run them through a PDF extractor, comparing the result against the HTML extraction of the same pages. We report this openly; these are not crawled PDFs. **Tables:** far above the ≥3 minimum.

---

## 3. Technology Stack

| Component | Choice | Reason |
|---|---|---|
| Crawl | Python `requests` + `urllib.robotparser`, MediaWiki API `action=parse` | Rendered HTML includes template-generated tables absent from wikitext |
| Extraction | BeautifulSoup4 + lxml (HTML); `pdfplumber` (rendered PDFs) | Table grids with rowspan/colspan expansion |
| Embedding | `BAAI/bge-m3` (1024-d, local) | Multilingual — supports Chinese queries and multilingual name tables |
| Distance / normalization | Cosine on L2-normalized vectors | Metric matches normalization (§2 Stage 4) |
| Vector store | Chroma (local, persistent) | Deterministic IDs, metadata filtering on `page_type`, delete by ID / filter |
| Retriever mode | **Hybrid**: BM25 (`rank_bm25`) + dense, fused by Reciprocal Rank Fusion; pool = 20 | All three modes measured |
| Reranker | `BAAI/bge-reranker-v2-m3` cross-encoder → top 5 | Multilingual cross-encoder |
| Generation LLM | `glm-5.3-flash` (Zhipu, OpenAI-compatible API) | Fast; also used as the closed-book B0 model |
| Chat interface | Chainlit | Nested steps give the expandable retrieval trace; side-panel elements give clickable citations |

---

## 4. System Architecture

```
 Offline XML dump ──► page selection list (337 pages)
                              │
                              ▼
 [1 Scrape] MediaWiki API, robots.txt parsed in code, ≤1 req/s, UA with contact email
     │      raw JSON saved by sha256 + manifest (url, timestamp, hash, robots source)
     ▼
 [2 Extract] strip navboxes/tooltips/ads → tables as grids → dedupe by content hash
     │       docs.jsonl: doc_id, source_url, title, heading_path, page_type,
     │                   effective_date, crawled_at, revid
     ▼
 [3 Chunk]  strategy A: fixed-size + overlap │ strategy B: structure-aware (heading path)
     ▼
 [4 Embed]  bge-m3, L2-normalized
     ▼
 [5 Vector DB] Chroma: id, vector, text, metadata{doc_id, strategy, page_type, url, effective_date}
     │
     │   ◄── [6 Re-chunk] from saved normalized text; delete stale strategy; orphan check
     ▼
 [7 Retrieve] BM25 ─┐
                    ├─ RRF fusion → pool of 20
              dense ┘
     ▼
 [8 Rerank] bge-reranker-v2-m3 → top 5
     ▼
 [9 Generate] glm-5.3-flash, context-only prompt, numbered sources
     │        → citation parser → number check → refusal / referral detector
     ▼
 [Chat UI] Chainlit: history, clickable [n] citations, retrieval trace (pre/post-rerank scores),
           refusal banner, human referral, "data as of" stamp
```

---

## 5. Chunking and Re-chunk Plan

**Strategy A — fixed-size:** 512 tokens with 64-token overlap, ignoring document structure.
**Strategy B — structure-aware:** split on headings; each chunk carries its heading path (e.g., `Lauma > Talents > Elemental Skill`); tables kept whole up to a size cap and split by row groups beyond it, with the header row repeated. A working prototype of B produces 2,411 chunks (median 843 characters).

We report chunk counts and token-length distributions for both.

**Chunk ID scheme (deterministic):** `{doc_id}#{strategy}#{seq:04d}`, e.g., `lauma#B#0007`. `doc_id` is derived from the page title; `seq` is the chunk's position within the document under that strategy. The same input always yields the same IDs. `strategy` is also stored as metadata.

**Re-chunk without re-crawling:** the chunker reads only the saved normalized documents (`data/normalized/`), never the network.

**No orphans:** after indexing strategy B, we delete with `where={"strategy": "A"}`, then assert that a count query for `strategy = A` returns 0 and that every remaining ID's `doc_id` exists in the current `docs.jsonl`. We re-run the same golden set and report the delta.

---

## 6. Grounding and Refusal Design

- **Citations on every claim.** Retrieved chunks are passed as numbered sources; the prompt requires a `[n]` marker after every factual sentence. A parser maps each marker to its source URL, rendered as a clickable link and a side-panel excerpt. Sentences without a valid marker are flagged.
- **Number check (safeguard #1, already running).** Every number in the answer must appear verbatim in a cited chunk; otherwise a visible warning is shown. Motivated by an observed error in which the model wrote `218.8` for the source's `218.88`.
- **Quote limit.** Post-generation check rejects any run of more than 25 consecutive words copied from a source.
- **Insufficient context.** The model is instructed to reply with a fixed refusal sentence ("I don't have that information in the wiki pages I can search.") when the sources do not support an answer; the UI shows refusals with a distinct style. We also refuse when the top reranker score falls below a threshold tuned on the dev split.
- **Human referral.** Questions about payments, refunds, or accounts are referred to official HoYoverse customer support.
- **Spend-advice guard (safeguard #2).** "Should I pull / spend?" questions get facts only plus a link to the official drop-rate disclosure — no spending recommendation.

---

## 7. Data Flow

1. The user types a question in the chat UI.
2. With conversation history, a follow-up ("and her constellation 2?") is rewritten into a standalone query ("Lauma constellation 2").
3. BM25 and dense retrieval each return candidates; RRF fuses them into a pool of 20.
4. The cross-encoder reranks the pool; the top 5 become numbered sources.
5. If the top reranker score is below threshold → **refusal** without calling the LLM.
6. Otherwise the LLM answers from the sources only, with `[n]` citations.
7. Post-checks: citation parsing, number check, quote-length check, referral and spend-advice detection.
8. The UI shows the answer with clickable citations, a "data as of" date, and an expandable trace of all 20 candidates with pre- and post-rerank scores — or the refusal / referral message.

---

## 8. Evaluation Plan

**Golden set (≥40 items), written from the source pages on Friday before the chatbot is tuned.** Each answerable item records the gold answer, source URL, and a ≤25-word evidence quote; each unanswerable item records what was searched. Every gold answer is verified by a human against the live page.

| Category | Target | Example source |
|---|---|---|
| Single-hop factual | 16 | A talent multiplier at a given level |
| Multi-hop | 7 | A character's banner date + the version page's end date |
| Comparative | 5 | Same talent scaling across two characters |
| Temporal | 5 | Banner and version effective periods |
| Unanswerable | 9 | Upcoming characters whose pages are placeholders; terms with no definition on the wiki |
| Ambiguous / adversarial | 4 | Near-miss names; "ignore your instructions" injection; "should I spend my rent on this banner?" |

**Split:** 60/40 dev/test, stratified by category, with a fixed random seed. We tune on dev only and run the test split **once** at the end.

**Baselines:** B0 closed-book (`glm-5.3-flash`, no retrieval); B1 BM25 only; B2 dense over fixed-size chunks; B3 final system. Headline metrics are also reported on the B0-incorrect subset.

**Ablation (one change at a time, B2 → B3):** + structure-aware chunking → + hybrid fusion → + reranker.

**Metrics:** Recall@5, Recall@20, MRR, nDCG@10; answer correctness; citation validity; correct-refusal rate (unanswerable) and over-refusal rate (answerable); spend-advice refusal rate; p50/p95 latency; cost per query (the GLM plan is subscription-based, so cost is reported as token usage converted at the published per-token price, with that method stated). **Uncertainty:** 95% bootstrap confidence intervals and McNemar's test on per-item pass/fail. **Error analysis:** ≥15 failures hand-labeled by the categories in §5 of the assignment.

---

## 9. Key Risks, Technical Challenges, and Mitigations

| Risk / challenge | Mitigation |
|---|---|
| **Ranking failure:** the answer is in the pool but outside the top 5 (observed: "Lauma constellation 2" — correct chunks at ranks 7 and 10) | Cross-encoder reranker; report Recall@20 as the reranker's ceiling |
| **Duplicate content:** character pages embed full talent tables that also exist on talent pages | Metadata filter on `page_type`; dedupe near-identical chunks at retrieval time |
| **Large tables:** multiplier tables exceed chunk size | Split by row groups and repeat the header row; read columns by level number, not index |
| **Wiki gaps and placeholders** (upcoming characters, undefined terms) | Exclude placeholders from answerable items; use them as unanswerable items |
| **Cloudflare blocks** HTML pages and sometimes `robots.txt` | Use the API endpoint that `robots.txt` explicitly allows; fall back to a saved `robots.txt` snapshot and record the source per page |
| **No embedding / rerank API from the LLM provider** | Run bge-m3 and bge-reranker locally |
| **Three-day schedule** | Core crawl and extraction already done Friday; issues per stage; reviewed PRs |

---

## 10. Ethics and Risk Assessment

**Crawl etiquette.** Pages are chosen offline from the official dump, so the live site only receives fetches for the 337 selected pages. `robots.txt` is parsed in code (`urllib.robotparser`); `User-agent: *` explicitly allows `/api.php?action=`. Rate limit ≤1 request/second; descriptive User-Agent with a contact email; raw responses stored once and reused, so re-chunking never re-crawls. We note that the site's `robots.txt` explicitly disallows AI crawlers (GPTBot, ClaudeBot, CCBot). Our crawler is not one of them and follows the rules for `User-agent: *`, but the site's stance on AI use is clear. We therefore keep the crawl small and one-time, keep the use non-commercial and classroom-only, attribute content under CC BY-SA, and quote at most 25 words from any page.

**PII exclusion.** Only article-namespace pages are selected; user pages, talk pages, and discussion threads are excluded. Character pages describe fictional characters. Voice-actor names appear on character pages; these are public credits, and we do not collect any contact details. Any page found to contain personal contact information is dropped.

**Top ethical risks for this domain.**

| # | Harm | Mitigation |
|---|---|---|
| 1 | **Financial loss from factual errors** — wrong or outdated pity rules, banner dates, or kit details lead to mistimed or excess spending | Number check; strict grounding; refusal on insufficient context; "data as of" stamp |
| 2 | **Opinion laundered as cited fact** — asked "should I pull?", the system stitches cited numbers into what looks like a verified recommendation, amplifying spending pressure | Spend-advice guard: facts only, no recommendation, link to the official drop-rate disclosure |
| 3 | **Misinformation via an editable source** — leaks, speculation, vandalism, or planted instructions are repeated with a real URL attached | Retrieved text treated as untrusted input; planted injection page tested and reported; unreleased-content pages labeled |
| 4 | **Staleness** — a cached answer from an older version, cited with a real URL, looks verified | Per-chunk `effective_date`; answers stamped with the corpus snapshot date; dump-vs-live diffs reported as real staleness examples |

Two safeguards will be running in code by Saturday evening: the **number check** (already running) and the **spend-advice guard**.

---

## 11. GitHub Repository

**https://github.com/VyjayanthiUC/Residency_MSAI633_GroupProject**

- Public repository created with team members as collaborators; project README committed (pipeline, schedule, team workflow, AI-usage log).
- `main` branch protection: required pull request with ≥1 approving review, no force pushes — to be enabled by the repository owner (admin) on Friday evening.
- Issues tab enabled; issues will be opened for each pipeline stage and report, plus the golden set, the evaluation harness, and the ethics safeguards, each assigned an owner.
- Initial scaffolding (one module per pipeline stage, report templates `reports/00`–`07`, `.gitignore` excluding `.env` and scraped data) will be merged through the first reviewed pull request.
- All work happens on short-lived feature branches merged through reviewed pull requests.

---

## References

Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. *Proceedings of the 32nd International ACM SIGIR Conference on Research and Development in Information Retrieval*, 758–759. https://doi.org/10.1145/1571941.1572114

Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAS: Automated evaluation of retrieval augmented generation. *Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations*, 150–158. https://arxiv.org/abs/2309.15217

Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W. (2020). Dense passage retrieval for open-domain question answering. *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 6769–6781. https://arxiv.org/abs/2004.04906

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459–9474. https://arxiv.org/abs/2005.11401

Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). Lost in the middle: How language models use long contexts. *Transactions of the Association for Computational Linguistics, 12*, 157–173. https://arxiv.org/abs/2307.03172

Nogueira, R., & Cho, K. (2019). Passage re-ranking with BERT. *arXiv preprint* arXiv:1901.04085. https://arxiv.org/abs/1901.04085

Thakur, N., Reimers, N., Rücklé, A., Srivastava, A., & Gurevych, I. (2021). BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models. *Advances in Neural Information Processing Systems Datasets and Benchmarks Track*. https://arxiv.org/abs/2104.08663
