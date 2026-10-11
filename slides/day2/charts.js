/* Charts and flow wires for the deck. Each chart is declared in HTML and built here, so section authors write data, not SVG.
 *
 *   <div class="chart" data-chart="bars" data-max="1" data-ticks="0,0.5,1" data-digits="2" style="--lab:360px">
 *     <script type="application/json">[{"label":"B1 keyword","v":0.663,"lo":0.48,"hi":0.83},{"label":"B3","v":0.761,"tone":"key"}]</script>
 *   </div>
 *   tone: "key" (FanBot / the point of the slide) · "memory" (closed-book, red) · "alt" (a second series) · omitted = neutral
 *
 *   <div class="chart" data-chart="timeline"><script type="application/json">[{"label":"Luna I","date":"2025-09-10"}, …]</script></div>
 *
 * A chart animates when it becomes visible: on slide entry, or when the .step that wraps it is revealed (CHARTS.refresh).
 * Flow wires: inside .flow, <svg class="wires"><path data-from="idA" data-to="idB" data-dir="h|v"/></svg> are routed between
 * the nodes' edges after layout (CHARTS.wire). Add class "step" to a path to reveal it with the presenter's steps. */
(function () {
  "use strict";
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const data = el => JSON.parse(el.querySelector('script[type="application/json"]').textContent);

  function bars(el) {
    const rows = data(el), max = +el.dataset.max || Math.max(...rows.map(r => r.hi ?? r.v));
    const digits = el.dataset.digits ?? 2, pct = x => `${(x / max) * 100}%`;
    const ticks = (el.dataset.ticks || "").split(",").filter(Boolean).map(Number);
    el.insertAdjacentHTML("beforeend", `<div class="bars">${rows.map(r => `
      <div class="bar ${r.tone || ""}" data-cid="${esc(el.id || "chart")}-${esc(r.label)}">
        <div class="lab">${esc(r.label)}${r.note ? `<small>${esc(r.note)}</small>` : ""}</div>
        <div class="track"><div class="fill" style="--w:${pct(r.v)}"></div>
          ${r.lo != null ? `<div class="ci" style="left:${pct(r.lo)};width:${pct(r.hi - r.lo)}"></div>` : ""}</div>
        <div class="val">${r.text ?? (+r.v).toFixed(digits)}</div>
      </div>`).join("")}</div>
      ${ticks.length ? `<div class="axis"><span></span><div class="ticks">${ticks.map(t => `<span style="left:${pct(t)}">${t}</span>`).join("")}</div><span></span></div>` : ""}`);
  }

  function timeline(el) {
    const pts = data(el), t = p => new Date(p.date + "T00:00:00Z").getTime();
    const t0 = t(pts[0]), t1 = t(pts.at(-1)), x = p => ((t(p) - t0) / (t1 - t0)) * 100;
    const run = 1.8;  // seconds, matches .tl .run transition
    el.insertAdjacentHTML("beforeend", `<div class="tl"><div class="rail"><div class="run"></div></div>${pts.map((p, i) => `
      <div class="dot" style="left:${x(p)}%;--d:${(x(p) / 100) * run}s"></div>
      <div class="lbl ${i % 2 ? "down" : "up"}" style="left:${x(p)}%"><b>${esc(p.label)}</b>${esc(p.sub || p.date)}</div>`).join("")}</div>`);
  }

  // events around a ring, evenly by date; data-size (px), data-hub ("big|small") for the centre
  function cycle(el) {
    const pts = data(el), n = pts.length, t = p => new Date(p.date + "T00:00:00Z").getTime();
    const S = +el.dataset.size || 600, c = S / 2, R = S * 0.36, t0 = t(pts[0]), t1 = t(pts.at(-1));
    const span = 360 - 360 / n, ang = p => -90 + ((t(p) - t0) / (t1 - t0)) * span;
    const xy = (a, r) => [c + r * Math.cos(a * Math.PI / 180), c + r * Math.sin(a * Math.PI / 180)];
    const [sx, sy] = xy(-90, R), [ex, ey] = xy(-90 + span, R), sweep = 2 * Math.PI * R * span / 360, run = 2.6;
    const [big, small] = (el.dataset.hub || "|").split("|");
    el.insertAdjacentHTML("beforeend", `<div class="cyc" style="width:${S}px;height:${S}px">
      <svg viewBox="0 0 ${S} ${S}" width="${S}" height="${S}">
        <circle class="ring" cx="${c}" cy="${c}" r="${R}"/>
        <path class="sweep" style="--len:${Math.ceil(sweep) + 2}" d="M${sx} ${sy} A${R} ${R} 0 ${span > 180 ? 1 : 0} 1 ${ex} ${ey}"/>
        ${pts.map(p => { const a = ang(p), [x, y] = xy(a, R), [lx, ly] = xy(a, R + 62), anchor = Math.abs(Math.cos(a * Math.PI / 180)) < .3 ? "middle" : (Math.cos(a * Math.PI / 180) > 0 ? "start" : "end");
          return `<circle class="pt" cx="${x}" cy="${y}" r="13" style="--d:${((a + 90) / span) * run}s"/>
          <text class="n" x="${lx}" y="${ly - 4}" text-anchor="${anchor}">${esc(p.label)}</text><text x="${lx}" y="${ly + 26}" text-anchor="${anchor}">${esc(p.sub || p.date)}</text>`; }).join("")}
      </svg>
      <div class="hub"><b>${esc(big)}</b><span>${esc(small)}</span></div></div>`);
  }

  function build(root = document) {
    root.querySelectorAll(".chart[data-chart]:not([data-built])").forEach(el => {
      ({ bars, timeline, cycle })[el.dataset.chart]?.(el);
      el.dataset.built = "1";
    });
  }

  // route connectors between nodes; coordinates are in stage pixels (the stage is scaled, so divide by the scale)
  function wire(root = document) {
    root.querySelectorAll(".flow").forEach(flow => {
      const svg = flow.querySelector("svg.wires"); if (!svg) return;
      const scale = flow.getBoundingClientRect().width / flow.offsetWidth || 1, fr = flow.getBoundingClientRect();
      const box = id => { const r = flow.querySelector("#" + id).getBoundingClientRect();
        return { l: (r.left - fr.left) / scale, t: (r.top - fr.top) / scale, r: (r.right - fr.left) / scale, b: (r.bottom - fr.top) / scale }; };
      svg.querySelectorAll("path[data-from]").forEach(p => {
        const a = box(p.dataset.from), b = box(p.dataset.to);
        let d;
        if (p.dataset.dir === "v") { const x1 = (a.l + a.r) / 2, x2 = (b.l + b.r) / 2, y1 = a.b, y2 = b.t, m = (y1 + y2) / 2;
          d = `M${x1} ${y1} C${x1} ${m} ${x2} ${m} ${x2} ${y2}`; }
        else { const y1 = (a.t + a.b) / 2, y2 = (b.t + b.b) / 2, x1 = a.r, x2 = b.l, m = (x1 + x2) / 2;
          d = `M${x1} ${y1} C${m} ${y1} ${m} ${y2} ${x2} ${y2}`; }
        p.setAttribute("d", d);
        p.style.setProperty("--len", Math.ceil(p.getTotalLength()) + 1);
        if (!p.classList.contains("step")) p.classList.add("shown");
      });
    });
  }

  // a chart is live when its slide is showing and any .step around it has been revealed
  function refresh(slide) {
    slide.querySelectorAll(".chart").forEach(el => {
      const st = el.closest(".step");
      el.classList.toggle("live", !st || st.classList.contains("shown"));
    });
  }

  window.CHARTS = { build, wire, refresh };
})();
