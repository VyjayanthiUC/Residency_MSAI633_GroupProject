# Deck style guide (for section authors)

Read this and README.md before writing, then look at a few existing sections (`sections/01-open.html`, `03-engine.html`,
`04-proof.html`) and match them.

## Files and ownership
- Each author edits **only their own** `sections/NN-name.html`. Never edit `deck.css`, `deck.js`, `charts.js`, `template.html`.
- Slide-specific CSS goes in a `<style>` block inside your section file, every selector scoped under your slide id
  (`#proof-twohop .x {…}`). Use the CSS variables from `deck.css`; no new colours.
- Build: `python3 build.py` (assembles `index.html`). Preview: `python3 serve.py`, then http://127.0.0.1:8820/.
- Screenshot to check (any Chromium-family browser): `chromium --headless=new --disable-gpu --hide-scrollbars --window-size=1920,1080
  --virtual-time-budget=4000 --screenshot=shots/<id>.png "http://127.0.0.1:8820/?export=1#<n>"`, then look at it.

## A slide
```html
<section class="slide" id="<section>-<slug>" data-speaker="Deep" data-mod="Retrieval">
  <h1>One plain-English claim, sentence case, ≤ 2 lines</h1>
  <p class="sub">Optional: one line for experts (metric names, method)</p>
  <div class="content"> … the visual … </div>
  <p class="source">Where every number comes from (report / item ids / split)</p>
  <aside class="notes">Speaker (NN s): 2–4 talking points. Not a script.</aside>
</section>
```
- `data-speaker`: Shyamala, Yanwei, Deep, Sohyun, Oyin, VJ, Ibukun. `data-mod`: Data, Indexing, Retrieval,
  Generation & Guardrails, Chat, Evaluation (comma list), `all`, or omit.
- Slides are **English**.
- Headline = a claim a non-gamer understands. Evidence = real numbers, small. Max ~25 words of body text per slide.
- No all-caps labels, no eyebrow labels above headlines, no numbered markers unless it is a real sequence.

## Building blocks (see deck.css)
- Big number: `<div class="big">53<small>caption</small></div>`
- Two columns: `<div class="cols">…</div>` (`.cols.wide-left` for 1.35 : 1)
- List: `<ul class="list"><li><b>key</b> text<small>detail</small></li></ul>` — max 4 items
- Comparison table: `.vs` (see open-mistakes). Citation chip: `<span class="cite">S1</span>`
- Bar chart: `<div class="chart" data-chart="bars" data-max="1" data-ticks="0,0.5,1">` + JSON rows
  `{"label","note","v","lo","hi","tone":"key|memory|alt","text"}`. `key` = the bar the slide is about (gold), `memory` =
  closed-book (red), `alt` = a second series. One `key` per chart. Bars animate when the slide (or wrapping .step) shows.
- Timeline: `data-chart="timeline"` + `[{"label","date","sub"}]`.
- Flow diagram: `<div class="content flow">` with absolutely placed `.node` boxes (ids), `<code>` chips for library names,
  `.node.key` for the result, and `<svg class="wires"><path data-from="a" data-to="b" data-dir="h|v"/></svg>`.
- Chat bubbles: copy the pattern from the old draft if needed — `.q` (question) and answer with `.cite` chips.

## Motion
- Presenter-paced only: add class `step` to elements revealed one per → press, in document order. No autoplay, no sound.
- Every slide's **final state must be a complete static picture** (the .pptx is built from `?export=1` screenshots).
- Custom animation: `<script>(window.SLIDE_HOOKS = window.SLIDE_HOOKS || {})["<slide id>"] = (slide, shown) => { … }</script>` inside the section file,
  where `shown` = number of revealed steps. Keep it deterministic. Budget: only the slides the brief marks as animated.

## Numbers
- Only numbers you can trace to the reports, evaluation results or GitHub. Never invent or round in a way that changes meaning.
- Label practice-split (dev) results as practice; the final exam (test split) has not been run.
