// Search on the home page, and the chat pop-up: the full chat (/chat) in an iframe on the same origin, so its login,
// citations and history work unchanged. "Ask about …" buttons open the panel and type the question into the chat.
(() => {
  const CHAT = document.body.dataset.chat || "/chat";
  const $ = s => document.querySelector(s);
  const panel = $("#panel"), launcher = $("#launcher"), toast = $("#toast");
  const say = msg => { toast.textContent = msg; toast.classList.add("show"); setTimeout(() => toast.classList.remove("show"), 4000); };

  // --- search (home page only) ---
  const q = $("#q");
  if (q) q.addEventListener("input", () => {
    const term = q.value.trim().toLowerCase();
    const hit = el => !term || el.dataset.search.includes(term);
    let shown = 0;
    document.querySelectorAll("section.block").forEach(sec => {
      let n = 0;
      sec.querySelectorAll(".card, tr[data-search]").forEach(c => {
        const h = hit(c); n += h;
        if (c.closest("table[data-page-size]")) c.dataset.match = h ? "1" : "0"; else c.hidden = !h;
      });
      sec.querySelectorAll("table[data-page-size]").forEach(t => t.showPage?.(1));
      sec.querySelectorAll("details.who").forEach(d => {      // a character row: matches by name, or by its abilities
        const all = hit(d), items = [...d.querySelectorAll("li[data-search]")];
        let m = 0;
        items.forEach(li => { const h = all || hit(li); li.hidden = !h; m += h; });
        d.hidden = m === 0; n += term ? m : 0;
        if (term && !all) d.open = m > 0;
      });
      sec.hidden = term && n === 0; shown += n;
    });
    $("#empty").hidden = !term || shown > 0;
    $("#results").textContent = term ? `${shown} ${shown === 1 ? "page" : "pages"} found` : "";
  });

  // --- sortable tables: click a column heading; aria-sort tells screen readers the order ---
  document.querySelectorAll("table.sortable th button").forEach(btn => btn.addEventListener("click", () => {
    const th = btn.parentElement, table = th.closest("table"), col = [...th.parentElement.children].indexOf(th);
    const dir = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
    table.querySelectorAll("thead th").forEach(h => h.hasAttribute("aria-sort") && h.setAttribute("aria-sort", "none"));
    th.setAttribute("aria-sort", dir);
    const key = r => r.children[col].dataset.sort || "";
    const cmp = btn.dataset.kind === "num" ? (a, b) => parseFloat(key(a) || 0) - parseFloat(key(b) || 0)
                                           : (a, b) => key(a).localeCompare(key(b), undefined, { numeric: true });
    const body = table.tBodies[0];
    [...body.rows].sort((a, b) => dir === "ascending" ? cmp(a, b) : cmp(b, a)).forEach(r => body.appendChild(r));
    table.showPage?.(1);
  }));

  // --- pagination for long tables (data-page-size): Previous / page numbers / Next, plus a "Showing 1–12 of 40" status ---
  document.querySelectorAll("table[data-page-size]").forEach(table => {
    const size = +table.dataset.pageSize, label = table.caption?.textContent.split(",")[0] || "Table";
    const pager = document.createElement("nav");
    pager.className = "pager"; pager.setAttribute("aria-label", `${label} pages`);
    table.closest(".tablewrap").after(pager);
    let page = 1;
    table.showPage = (want) => {
      const rows = [...table.tBodies[0].rows], live = rows.filter(r => r.dataset.match !== "0");
      const pages = Math.max(1, Math.ceil(live.length / size));
      page = Math.min(Math.max(1, want), pages);
      rows.forEach(r => r.hidden = true);
      live.slice((page - 1) * size, page * size).forEach(r => r.hidden = false);
      const from = live.length ? (page - 1) * size + 1 : 0, to = Math.min(page * size, live.length);
      const btn = (text, p, extra = "") => `<button type="button" data-p="${p}" ${extra}>${text}</button>`;
      let nums = "";
      for (let i = 1; i <= pages; i++) nums += btn(i, i, i === page ? 'aria-current="page"' : `aria-label="Page ${i}"`);
      pager.innerHTML = pages < 2 ? `<span class="pagerinfo" role="status">Showing ${to} of ${live.length}</span>` :
        btn("‹ Previous", page - 1, page === 1 ? "disabled" : "") + nums + btn("Next ›", page + 1, page === pages ? "disabled" : "") +
        `<span class="pagerinfo" role="status">Showing ${from}–${to} of ${live.length}</span>`;
    };
    pager.addEventListener("click", ev => {
      const b = ev.target.closest("button[data-p]");
      if (!b || b.disabled) return;
      table.showPage(+b.dataset.p);
      pager.querySelector('[aria-current="page"]')?.focus();
      table.closest("section").scrollIntoView({ block: "start" });
    });
    table.showPage(1);
  });

  // --- chat panel ---
  let frame = null;
  function open(show = true) {
    if (show && !frame) {
      frame = document.createElement("iframe");
      frame.src = CHAT; frame.title = "Ask a question";
      panel.appendChild(frame);
    }
    panel.hidden = !show;
    launcher.setAttribute("aria-expanded", String(show));
    launcher.setAttribute("aria-label", show ? "Close chat" : "Open chat");
    if (show) frame.focus(); else launcher.focus();  // keyboard users land inside the panel, then back on the button
  }
  launcher.addEventListener("click", () => open(panel.hidden));
  $("#close").addEventListener("click", () => open(false));
  document.addEventListener("keydown", ev => { if (ev.key === "Escape" && !panel.hidden) open(false); });

  // Type a question into the chat's message box and send it (same origin, so the page can reach into the iframe).
  function send(question) {
    let tries = 0;
    const timer = setInterval(() => {
      const doc = frame && frame.contentDocument;
      const box = doc && doc.querySelector("#chat-input");
      if (!box && ++tries < 80) return;
      clearInterval(timer);
      if (!box) { navigator.clipboard?.writeText(question); say("Question copied. Paste it into the chat."); return; }
      box.focus();
      if (box.isContentEditable) {
        box.textContent = question;
        box.dispatchEvent(new InputEvent("input", { bubbles: true }));
      } else {
        const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(box), "value").set;
        setter.call(box, question);
        box.dispatchEvent(new Event("input", { bubbles: true }));
      }
      setTimeout(() => {
        const submit = doc.querySelector("#chat-submit");
        if (submit && !submit.disabled) submit.click();
        else box.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
      }, 120);
    }, 150);
  }
  document.addEventListener("click", ev => {
    const b = ev.target.closest(".ask[data-q]");
    if (!b) return;
    open(true);
    send(b.dataset.q);
  });
})();

// Wiki images load from another server; if one fails, drop it so no broken-image icon shows.
const WIKI_IMG = "img.thumb, img.mini, img.regionimg, img.pageimg, img.bannerimg";
document.addEventListener("error", (ev) => { if (ev.target.matches?.(WIKI_IMG)) ev.target.remove(); }, true);
document.querySelectorAll(WIKI_IMG).forEach(i => { if (i.complete && !i.naturalWidth) i.remove(); });  // failed before this script ran

// Home banner background video: plays the newest characters' gameplay clips in turn, muted. With reduced motion it
// waits until the pointer passes over the banner (or the button is pressed); the button also pauses it; if a clip
// fails the key art image shows.
(() => {
  const v = document.querySelector(".bannervideo"), btn = document.querySelector(".bgtoggle");
  if (!v) return;
  const reel = JSON.parse(v.dataset.reel || "[]"), credit = document.querySelector(".bannercredit");
  const still = credit && { text: credit.textContent, href: credit.getAttribute("href") };
  if (!reel.length) return;
  // Reduced motion: don't start it; offer a "Play background" button instead.
  let i = 0, fails = 0, paused = matchMedia("(prefers-reduced-motion: reduce)").matches, started = false;
  const load = () => {
    const c = reel[i];
    v.src = c.src;
    if (credit) { credit.textContent = `Gameplay: ${c.name}`; credit.href = c.href; }
    v.play().catch(() => {});
  };
  v.addEventListener("playing", () => { v.classList.add("on"); btn.hidden = false; fails = 0; });
  // Browsers may pause muted background video to save power (hidden tab, off screen): resume when it can play again.
  const resume = () => { if (started && !paused && v.paused && !document.hidden) v.play().catch(() => {}); };
  v.addEventListener("canplay", resume);
  document.addEventListener("visibilitychange", resume);
  new IntersectionObserver(es => es[0].isIntersecting && resume()).observe(v);
  v.addEventListener("ended", () => { i = (i + 1) % reel.length; load(); });
  v.addEventListener("error", () => {
    if (++fails >= reel.length) {                    // none will play: back to the still image and its credit
      v.classList.remove("on"); btn.hidden = true;
      if (credit && still) { credit.textContent = still.text; credit.href = still.href; }
      return;
    }
    i = (i + 1) % reel.length; load();
  });
  const label = () => { btn.setAttribute("aria-pressed", String(paused)); btn.textContent = paused ? "Play background" : "Pause background"; };
  btn.addEventListener("click", () => {
    paused = !paused;
    if (!paused && !started) { started = true; load(); }
    else paused ? v.pause() : v.play().catch(() => {});
    btn.setAttribute("aria-pressed", String(paused));
    btn.textContent = paused ? "Play background" : "Pause background";
  });
  if (paused) {
    // Reduced motion: start when the visitor moves the pointer over (or tabs into) the banner, or presses the button.
    label(); btn.hidden = false;
    const banner = v.closest(".banner");
    const start = () => { if (started) return; started = true; paused = false; label(); load(); };
    banner.addEventListener("pointerenter", start, { once: true });
    banner.addEventListener("focusin", start, { once: true });
  } else { started = true; load(); }
})();
