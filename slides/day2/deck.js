/* Deck runtime: scale the 1920×1080 stage, keyboard navigation with presenter-paced steps, module strip, speaker
 * constellation, chart/wire hooks, comment hooks.
 * Keys: → / Space / PageDown next step or slide · ← / PageUp back · Home / End · C toggles comment mode (review/comments.js).
 * ?export=1 shows every step at its final state and hides the UI (used by export.py for the .pptx screenshots).
 *
 * Per slide (on <section class="slide">): data-speaker="Deep"  data-mod="Retrieval" (comma list, "all", or omitted).
 * Steps: any element with class "step" is revealed in document order, one per → press.
 * Custom animation: window.SLIDE_HOOKS[<section id>] = (slideEl, shownStepCount) => { … } runs after every step change. */
(function () {
  "use strict";
  const stage = document.getElementById("stage");
  const slides = [...document.querySelectorAll(".slide")];
  const SPEAKERS = ["Shyamala", "Yanwei", "Deep", "Sohyun", "Oyin", "VJ", "Ibukun"];
  // one element per speaker, in the seven nations' order (Mondstadt → Snezhnaya); colours from genshin-quest lore.js
  const ELEM = [["anemo", "#6fe0c8", "111,224,200"], ["geo", "#f0c060", "255,200,90"], ["electro", "#b48cff", "180,140,255"],
    ["dendro", "#8fd14f", "150,215,90"], ["hydro", "#5ab8ff", "90,180,255"], ["pyro", "#ff8a4c", "255,140,80"], ["cryo", "#9fe6f2", "160,230,245"]];
  const MODS = ["Data", "Indexing", "Retrieval", "Generation & Guardrails", "Chat", "Evaluation"];
  const ICONS = ["m-data", "m-indexing", "m-retrieval", "m-generation", "m-chat", "m-evaluation"];
  const exportMode = new URLSearchParams(location.search).has("export");
  if (exportMode) document.body.classList.add("export");
  window.SLIDE_HOOKS = window.SLIDE_HOOKS || {};
  let cur = 0;

  function fit() {
    const s = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(${(innerWidth - 1920 * s) / 2}px,${(innerHeight - 1080 * s) / 2}px) scale(${s})`;
    if (slides[cur]) window.CHARTS?.wire(slides[cur]);
  }

  const sky = document.querySelector(".sky");
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 90; i++) { const s = document.createElement("i"); s.style.left = rnd() * 1920 + "px"; s.style.top = rnd() * 780 + "px"; s.style.opacity = .15 + rnd() * .55; sky.appendChild(s); }

  slides.forEach((sl, n) => {
    sl.dataset.cid = sl.id || `s${n + 1}`;
    if (sl.classList.contains("title")) return;
    const at = SPEAKERS.indexOf(sl.dataset.speaker);
    sl.insertAdjacentHTML("beforeend", `<div class="cons">${SPEAKERS.map((p, i) => `<span class="${i < at ? "done" : i === at ? "now" : ""}" style="--ec:${ELEM[i][1]};--eg:${ELEM[i][2]}"><svg class="em"><use href="#e-${ELEM[i][0]}"/></svg>${p}</span>`).join("")}</div>
      <div class="pageno">${n + 1} / ${slides.length}</div>`);
    const mod = sl.dataset.mod;
    if (mod) {
      const on = mod === "all" ? MODS : mod.split(",").map(s => s.trim());
      sl.insertAdjacentHTML("beforeend", `<div class="mods">${MODS.map((m, i) => `<span class="${on.includes(m) ? "on" : ""}"><svg class="ico"><use href="#${ICONS[i]}"/></svg>${m}</span>`).join("")}</div>`);
    }
  });
  window.CHARTS?.build();
  slides.forEach(sl => sl.querySelectorAll("h1,.sub,.big,.list li,.vs .c,.node,.chart,.bar,.source,.mark,.team,.cols>*").forEach((el, i) => {
    if (!el.dataset.cid) el.dataset.cid = `${sl.dataset.cid}-${el.id || i}`;
  }));

  const steps = sl => [...sl.querySelectorAll(".step")];
  function after() {
    const sl = slides[cur];
    requestAnimationFrame(() => requestAnimationFrame(() => {   // two frames so entering charts animate from zero
      window.CHARTS?.wire(sl); window.CHARTS?.refresh(sl);
      window.SLIDE_HOOKS[sl.id]?.(sl, steps(sl).filter(s => s.classList.contains("shown")).length);
    }));
  }
  function show(n, stepAll) {
    slides[cur]?.querySelectorAll(".chart.live").forEach(c => c.classList.remove("live"));
    cur = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, i) => s.classList.toggle("on", i === cur));
    steps(slides[cur]).forEach(s => s.classList.toggle("shown", !!stepAll || exportMode));
    history.replaceState(null, "", `${location.search}#${cur + 1}`);
    window.CMT?.refresh();
    after();
  }
  function next() {
    const hidden = steps(slides[cur]).find(s => !s.classList.contains("shown"));
    if (hidden) { hidden.classList.add("shown"); after(); } else if (cur < slides.length - 1) show(cur + 1);
  }
  function prev() {
    const shown = steps(slides[cur]).filter(s => s.classList.contains("shown"));
    if (shown.length) { shown.at(-1).classList.remove("shown"); after(); } else if (cur > 0) show(cur - 1, true);
  }
  document.addEventListener("keydown", e => {
    if (e.target.closest?.("textarea,input")) return;
    if (["ArrowRight", " ", "PageDown"].includes(e.key)) { next(); e.preventDefault(); }
    else if (["ArrowLeft", "PageUp"].includes(e.key)) { prev(); e.preventDefault(); }
    else if (e.key === "Home") show(0); else if (e.key === "End") show(slides.length - 1);
  });
  addEventListener("hashchange", () => { const n = parseInt(location.hash.slice(1)) - 1; if (n !== cur && !isNaN(n)) show(n); });
  addEventListener("resize", fit);

  window.COMMENTS_CFG = {
    doc: "slides", root: "#stage", pick: "[data-cid]",
    context: () => ({ screen: slides[cur].dataset.cid, label: slides[cur].querySelector("h1")?.innerText.replace(/\s+/g, " ") || "" }),
  };
  window.DECK = { show, count: slides.length, notes: () => slides.map(s => ({ id: s.dataset.cid, speaker: s.dataset.speaker || "", title: s.querySelector("h1")?.innerText || "", notes: s.querySelector("aside.notes")?.innerText.trim() || "" })) };
  fit();
  show((parseInt(location.hash.slice(1)) || 1) - 1);
  document.fonts.ready.then(() => { fit(); after(); });
})();
