# Day 2 presentation deck

The Day 2 presentation (20 minutes including demo and Q&A) as an HTML deck: a 1920×1080 stage, presenter-paced
steps, animated charts and diagrams. The submitted `.pptx` is exported from it (one screenshot per slide plus speaker
notes). Present from the HTML version: the animations and the Q&A jump links only work there.

## Run it

Everything here uses the Python standard library, except the `.pptx` export.

```bash
cd slides/day2
python3 fetch_images.py      # game art into img/ (git-ignored, see "Images" below); once
python3 build.py             # sections/*.html + template.html -> index.html (git-ignored, regenerate after edits)
python3 serve.py             # http://127.0.0.1:8820/   (← → or Space to step, Home / End)
```

On Windows, where `python3` usually isn't on PATH, run the same scripts with `uv run --no-project python <script>.py`.

Export (needs the server running and a Chromium-family browser; Chrome or Edge is found automatically, including their
default Windows install paths; otherwise set `BROWSER=/path/to/chrome`):

```bash
uv run --with python-pptx python export.py FanBot_Day2_Presentation.pptx
```

`?export=1` on the URL shows every slide in its final state (all steps revealed); that is what the export captures.
`#n` jumps to slide n.

## Layout

| Path | What |
|---|---|
| `sections/NN-*.html` | the slides, one file per speaker segment, in speaking order |
| `template.html` | page shell; `build.py` inserts the sections |
| `deck.css` | design tokens and building blocks (type, colours, module band, speaker band, charts, flow diagrams) |
| `deck.js` | stage scaling, keyboard steps, module band, speaker band, per-slide animation hooks |
| `charts.js` | bar charts with confidence intervals, the version cycle, flow-diagram connectors |
| `icons/` | SVG icon sets (module icons, element emblems, primogem / Mora) |
| `fonts/` | Fraunces, Inter, Cinzel Decorative (SIL Open Font License, licences included) |
| `STYLE.md` | rules for adding or editing slides (written for people and coding agents) |
| `serve.py`, `build.py`, `export.py`, `fetch_images.py` | preview server, assembler, pptx export, image download |

Each slide is a `<section class="slide">` with `data-speaker` (lights the speaker's element in the bottom band),
`data-mod` (lights the system modules in the top band), a source line naming where every number comes from, and
`<aside class="notes">` speaker notes (copied into the pptx notes). Numbers are from the practice (dev) split:
reports 01–06 and `evaluation/results/`; the test split runs once on Sunday.

## Fonts and images

- Headlines use Fraunces, body text MiSans when it is installed locally, otherwise Inter. MiSans is not redistributed.
- Character portraits, the weapon icon and the version key art are HoYoverse game art shown by the Genshin Impact
  Fandom wiki under fair use. The image files are not committed; `fetch_images.py` downloads them from the wiki's image
  server (the same URLs the team website uses, `web/images.py`). Slides that show them credit HoYoverse in the source
  line. The submitted export, `FanBot_Day2_Presentation.pptx` at the repository root, contains them as part of the
  slide screenshots.
- `img/site-chat.png` is a screenshot of our own website with the chat pop-up open.
