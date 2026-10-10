# Chat UI verification (issues 5.1–5.5, #34–#38) — 2026-10-10

Run on main after PR #87 (`./run.sh`, default retrieval: hybrid + rerank over chunks B, `REFUSE_BELOW=0.52`),
generation model `glm-5.3-flash`, on a CPU-only machine. Each screenshot is one question typed into the chat UI.

| Issue | Requirement | Question asked | Result | Screenshot |
|---|---|---|---|---|
| #37 | Expandable retrieval trace with pre- and post-rerank scores | What is the name of Lauma's Elemental Skill? | Trace lists the 20-candidate pool and the final 5, each with its RRF score (pre) and rerank score (post) and a "used" mark; footer shows query, retriever, 20 → 5, 16.7 s | `02_retrieval_trace.png` |
| #38 | Data-as-of date | same | Answer cites S1/S2; the source panel shows the snapshot date and the game version date; the answer footer shows "Wiki snapshot 2026-10-10 (UTC)" | `01_answer_citation_date.png` |
| #38 | Refusal | When is Diluc's birthday? | Diluc is outside the corpus; the bot refuses ("I don't have that information in the wiki snapshot.") instead of answering from model memory | `03_refusal_en.png` |
| #38 | Human referral | I topped up Genesis Crystals but they never arrived. Can I get a refund? | Refusal plus referral to HoYoverse official customer support | `04_referral.png` |
| #75 | Small talk | hi | No retrieval; welcome message with the snapshot date and two example questions | `05_smalltalk_welcome.png` |
| #34 | History + session persistence | reload the thread with the questions above | After a page reload the thread reopens from the sidebar with every earlier message (Lauma, Diluc, refund, hi) | `06_history_after_reload.png` |
| #35 | Follow-up query rewriting | What element is Lauma? → What does her C2 do? | "her C2" is rewritten to `Lauma constellation 2 effect`; the answer cites the C2 text | `07_followup_rewrite.png` |
| #36 | Clickable citations + source side panel | same | Clicking a badge (S4) opens that exact source in the side panel: page › section, Fandom URL, snapshot and version date, chunk text | `07_followup_rewrite.png`, `01_answer_citation_date.png` |
| #34 | Follow-ups still work after a reload | reload, then: And what about her C6? | The restored conversation still resolves "her" → `Lauma Constellation Level 6`, cited answer | `08_followup_after_reload.png` |

The source panel on the right of screenshots 03–05 is left over from clicking S2 in the first answer.

**Known UI quirk (not a citation error):** if the source panel is left open while a new answer arrives, its header can
show the new answer's tag with an older source underneath. Clicking the badge always shows the right source.

**Failure-analysis example:** the S5 chunk in `08_followup_after_reload.png` (Lauma › Gameplay Info › Talents) starts
with `Description Gameplay Notes Advanced Properties…` — the known extraction issue where the character page's nested
Talents table is flattened into one cell (see `ingest/README.md`).
