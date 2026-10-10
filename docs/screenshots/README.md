# Chat UI screenshots

Proof-of-concept captures of the Chainlit chat interface running against the local corpus snapshot and index (bge-m3 embeddings, hybrid retrieval, bge-reranker-v2-m3, strategies A/B).

- `2026-10-10_cited-answer-arlecchino-element.png` — cited answer with retrieval trace, number check, and the expandable source panel (infobox fields for Arlecchino).
- `2026-10-10_refusal-unanswerable-questions.png` — correct refusal behavior on out-of-corpus questions ("archon names", "game launch date") with the searched query shown.
- `2026-10-10_welcome-and-nod-krai-answer.png` — welcome screen plus an answered question; flags a case where the answer cited sources (`S2`, `S4`) but the UI's citation check reported "no source" — worth a look by whoever owns `rag/grounding.py`.

Add new screenshots as `YYYY-MM-DD_short-description.png` and a line here.
