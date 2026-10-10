# Report 03 — Golden Evaluation Set

**MSAI 633 Residency · Day 2 · October 10, 2026** · `evaluation/golden.jsonl` (53 items) · `evaluation/split.json` · `evaluation/golden.py`

## 1. Summary

| Requirement | Status |
|---|---|
| ≥ 40 items | **53** |
| Quotas met | yes, every category at or above its minimum (section 3) |
| Authored before tuning | the set was final at 20:00 UTC; the first system run on any split was at 20:13 UTC, and no item was written from system output |
| Gold URL and evidence quote per answerable item | 58 / 58 evidence entries carry a URL; longest quote 22 words (limit 25) |
| Search log for every refusal item | 11 / 11 refusal items carry a `searched` log |
| Human-verified | **53 / 53**, by Saweisra, item by item, 10:45–14:49 CDT on 2026-10-10 (log: `evaluation/golden_verification.json`) |
| Stratified 60/40 split | dev 32 / test 21, stratified by category, seed 633; regenerating it reproduces the committed file exactly |

## 2. How the set was built

| Time (UTC, 10-10) | Step | Where |
|---|---|---|
| 15:28 | 46 items drafted by a teammate from the committed snapshot | PR #58 |
| 15:45–19:09 | Machine pre-checks (section 6), then **human verification of all 46**; five items fixed | `e27b4bb`, merged 19:16 |
| 19:39 | Gold URLs and search logs added; five *player-task* (`synthesis`) items written from snapshot pages and verified; one item re-categorised | PR #73, merged 19:47 |
| 19:51 | Two more synthesis items (a constellation question and a pull-advice question), verified | PR #79, merged 20:00 — **set frozen** |
| 20:13 | First evaluation run (retrieval, dev) | PR #82 |

Items were written **from wiki pages only**, never from system answers. The split was regenerated (`golden split --force`) when items
were added, which was allowed because no system had been run on any split yet. AI use: the synthesis items and the machine checks
were drafted with Claude Code; every item, including those, was then verified by a person (section 5).

### Item schema

```json
{"id": "sh07", "category": "single_hop", "question": "What is the base ATK range (level 1 to 90) of the bow Golden Frostbound Oath?",
 "expected_behavior": "answer", "answer_keys": ["44", "542"],
 "evidence": [[{"title": "Golden Frostbound Oath", "needles": ["Base ATK (Lv. 1 - 90): 44 - 542"], "url": "https://genshin-impact.fandom.com/wiki/Golden_Frostbound_Oath"}]],
 "gold_answer": "44 at level 1, 542 at level 90.", "verified_by": "Saweisra 2026-10-10"}
```

- `evidence` is a list of **requirements** (all must be met), each a list of **alternatives** (any one is enough). A chunk meets an
  alternative when it comes from that page and contains every needle. This label does not depend on chunk IDs, so the same set
  scores both chunking strategies (`evaluation/golden.py`).
- `expected_behavior` is one of `answer` (39), `refuse` (11), `no_spend_advice` (2), `no_injection` (1).
- Refusal items carry `searched`: each query run over the snapshot and the number of pages it hit.

## 3. Quotas and split

| Category | Items | Minimum | Dev | Test | What it tests |
|---|---:|---:|---:|---:|---|
| single_hop | 16 | 15 | 10 | 6 | one fact on one page |
| multi_hop | 7 | 6 | 4 | 3 | a fact found by first finding another fact on another page |
| comparative | 5 | 4 | 3 | 2 | the same field on two pages |
| temporal | 5 | 4 | 3 | 2 | dates and versions (reruns, release order) |
| unanswerable | 8 | 8 | 5 | 3 | the snapshot does not contain the answer |
| adversarial | 5 | 3 | 3 | 2 | false premise, fabricated near-name, closed-book trap, prompt injection, spend pressure |
| synthesis | 7 | — | 4 | 3 | questions players actually ask: upgrade costs, reaction requirements, team conditions, out-of-scope requests |
| **Total** | **53** | 40 | **32** | **21** | |

Dev is for tuning; **test is run once**, after the configuration is frozen (`evaluation.run … --split test --final`, which refuses to
run without `--final` and records the run).

## 4. Design rules

**Answer keys must pin the answer.** Every key must appear in the answer, matched on token and number boundaries ("5" does not
match "15"; "12" matches "12s"). One key is not always enough: `542` is also the level-90 base ATK of other weapons, so `sh07`
requires both `44` and `542`; `sh05` and `cmp05` were tightened the same way. Comparative and multi-hop items need one key per side
or hop.

**Questions must not give away a hop.** `mh02` originally named the version (Luna I) in the question, which turned the multi-hop
item into a single lookup; it now asks for the version and its full title.

**Questions must have one answer in the snapshot.** `temp03` said "(2026)", but the banner ran twice that year; it now asks for the
third run.

**Unanswerable items are checked by full-text search, and the search is recorded.** Five kinds:

| Kind | Items | Why it is hard |
|---|---|---|
| Partial knowledge: upcoming characters with a stub page (element and constellation name only) | `unans01`–`03`, `unans09` | the name retrieves real pages, but the asked-for data is absent |
| Fabricated names, including near-names of real items | `unans04`–`06`, `adv01` (near *Ineffa*) | 0 pages hit; a model may invent an answer |
| Beyond the snapshot date | `unans08` (Version 7.2; the latest in the snapshot is 7.1) | extrapolating a date counts as wrong |
| Closed-book trap | `adv03` (Diluc: no page, one voice-over mention) | the model knows the answer from training, but it is not in the corpus |
| Out-of-scope player request | `syn05` (skill rotation) | the wiki documents mechanics, not rotations: "rotation" hits 1 page, "best team" 0 |

**Synthesis items stay inside what the pages state.** An answer may (1) restate a fact or (2) combine cited facts into a conclusion
that follows directly from them (`syn03`: what triggers Lunar-Charged and which characters provide it — four chunks needed).
It may **not** (3) add a judgement that no page makes — "best team", "C2 is the key constellation". Requests of the third kind are
refusal or `no_spend_advice` items (`syn05`, `syn07`); for `syn07` a good answer also corrects the false premise that the character
is on the current banner.

## 5. Human verification

**Who and how.** Saweisra verified every item on 2026-10-10 (10:45–14:49 CDT). The tool showed, for each item, the question, the
gold answer, and the evidence highlighted inside the **snapshot** text, with the live Fandom page as a reference; the verifier
answered *correct* / *problem* item by item. Every verdict, with its note and timestamp, is in `evaluation/golden_verification.json`;
each item's `verified_by` records the verifier and date. The snapshot, not the live page, is the reference, because the system can only know
the snapshot. Teammate review of the set happened in PRs #58, #73 and #79.

**Outcome:** 49 items correct as drafted or with tightened keys, 4 flagged as problems; 7 items changed in total.

| Item | Problem | Fix |
|---|---|---|
| `mh02` | the question gave away the first hop | rewritten; `Luna I` added to the keys |
| `temp03` | "(2026)" is ambiguous — two runs that year | rewritten to "third run" |
| `adv03` | near-duplicate of `adv02` | replaced with the Diluc closed-book trap |
| `unans07` | drafted as unanswerable, but the *Team Bonus* page does document Elemental Resonance (same-element rule) | moved to `adversarial`, expected to **answer** by correcting the false premise "Pyro-Dendro Resonance" |
| `sh05`, `sh07`, `cmp05` | answer keys too loose (one number) | keys tightened (both numbers / both sides) |

`unans07` is the instructive one: the first check was a search for the term, which found nothing, but the rule it contradicts was
on a page with a different name. Unanswerability has to be checked against the concept, not the phrase.

## 6. Machine checks (re-run on main `7bcc416`)

- `uv run python -m evaluation.golden validate` → `53 items … verified 53/53; problems: 0`. Every needle exists on its page **and**
  inside at least one chunk of strategy A and one of strategy B, so no item is unanswerable because of a chunk boundary.
- Longest evidence quote: 22 words (limit 25). All 58 evidence entries have a gold URL; all 11 refusal items have a search log.
- `make_split` with seed 633 regenerates `split.json` exactly.

## 7. Coverage and limitations

| Page type | Pages | Share of corpus text | Evidence references |
|---|---:|---:|---:|
| talent | 123 | 22.6% | 6 |
| character | 18 | 17.5% | 13 |
| weapon | 40 | 16.5% | 11 |
| version | 10 | 15.5% | 4 |
| mechanic | 15 | 12.4% | 6 |
| constellation | 108 | 9.1% | 1 |
| artifact | 8 | 5.1% | 4 |
| event wish | 13 | 0.9% | 10 |
| upcoming character | 2 | 0.3% | 0 (used by refusal items) |

Evidence comes from 38 distinct pages.

- **Under-covered:** constellation pages are a third of the pages but short (9% of the text), and the set has one constellation item
  (`syn06`). Talent pages are the largest share of text and are under-represented. We stopped adding items at 53 because each
  round costs a re-split and a review, and the set had to be frozen before tuning.
- **Over-covered:** Arlecchino appears in 8 items; event-wish pages are over-represented relative to their text.
- **Infobox-heavy:** about ten single-hop items read one infobox field (element, birthday, base ATK). They are easy for every
  retriever, which compresses differences between configurations. Report 04 shows the opposite effect for comparative items that
  need *two* infobox fields.
- **Safety behaviours only on dev:** the split is stratified by category, not by expected behaviour, so the injection item and both
  spend-advice items landed in dev. Test does not measure those behaviours; the safeguards are demonstrated separately (report 07).
- **One alternative per requirement** can under-credit a valid source (report 04, `mh06`).
- **Key matching is literal:** "1,652,500 Mora" must appear as written; an answer saying "about 1.65 million" fails.
- n = 53 (dev 32, test 21): differences of a few items are noise, so improvement claims need a confidence interval or a paired test.

## 8. Reproduce

```bash
uv run python -m rag.chunking --strategy both        # chunks A and B, needed by validate
uv run python -m evaluation.golden validate          # needles exist on their pages and in A and B chunks
uv run python -m evaluation.golden split             # writes split.json (seed 633); refuses to overwrite without --force
```
