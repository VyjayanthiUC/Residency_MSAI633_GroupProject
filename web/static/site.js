// Search on the home page, and the chat pop-up: the full chat (/chat) in an iframe on the same origin, so its login,
// citations and history work unchanged. "Ask about …" buttons open the panel and type the question into the chat.
// While the chat is open, citations and site links swap the main page in place (no reload), so the conversation stays.
(() => {
  const CHAT = document.body.dataset.chat || "/chat";
  const $ = s => document.querySelector(s);
  const panel = $("#panel"), launcher = $("#launcher"), toast = $("#toast");
  const say = msg => { toast.textContent = msg; toast.classList.add("show"); setTimeout(() => toast.classList.remove("show"), 4000); };

  function initMain() {
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
      // While searching, the page collapses to the results (#98): banner shrinks, region cards and section links hide,
      // and the count under the box is visible (it is also the aria-live status).
      document.body.classList.toggle("searching", !!term);
      $("#results").textContent = term ? (shown ? `${shown} ${shown === 1 ? "page" : "pages"} found. Press Enter to go to the first.`
                                                : "No pages match your search.") : "";
    });
    const firstResult = () => [...document.querySelectorAll("section.block:not([hidden]) a[href^='/wiki/']")]
      .find(a => a.offsetParent !== null && !a.closest("[hidden]"));
    if (q) q.addEventListener("keydown", ev => {
      if (ev.key === "Enter") {
        const a = firstResult();
        if (a) { ev.preventDefault(); a.scrollIntoView({ block: "center" }); a.focus({ preventScroll: true }); }
      } else if (ev.key === "Escape" && q.value) {
        ev.stopPropagation();                           // don't also close the chat panel
        q.value = ""; q.dispatchEvent(new Event("input"));
      }
    });
    if (q) q.addEventListener("search", () => q.dispatchEvent(new Event("input")));   // the box's ✕ button

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
    // --- tabs in talent / constellation cards: click, or arrow keys along the tab row ---
    document.querySelectorAll('.tabs[role="tablist"]').forEach(list => {
      const tabs = [...list.querySelectorAll('[role="tab"]')];
      const pick = (t, focus) => {
        tabs.forEach(x => {
          const on = x === t;
          x.setAttribute("aria-selected", String(on)); x.tabIndex = on ? 0 : -1;
          document.getElementById(x.getAttribute("aria-controls")).hidden = !on;
        });
        if (focus) t.focus();
      };
      list.addEventListener("click", ev => { const t = ev.target.closest('[role="tab"]'); if (t) pick(t); });
      list.addEventListener("keydown", ev => {
        const i = tabs.indexOf(document.activeElement), step = { ArrowRight: 1, ArrowLeft: -1 }[ev.key];
        if (i < 0 || !step) return;
        ev.preventDefault(); pick(tabs[(i + step + tabs.length) % tabs.length], true);
      });
    });
    initBanner();
    dropBrokenImages();
  }

  // --- chat panel ---
  let frame = null;
  function open(show = true) {
    if (show && !frame) {
      frame = document.createElement("iframe");
      frame.src = CHAT; frame.title = "Ask a question";
      frame.addEventListener("load", wireChat);
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
  // If an answer is still streaming, the chat's send button is missing or disabled: wait for it before typing, so the
  // question is actually sent (review on #90).
  let pending = null;
  function send(question) {
    if (pending) clearInterval(pending);
    let tries = 0, told = false;
    const ready = doc => {
      const submit = doc.querySelector("#chat-submit");
      return submit && !doc.querySelector("#stop-button");
    };
    pending = setInterval(() => {
      const doc = frame && frame.contentDocument;
      let box = doc && doc.querySelector("#chat-input");
      tries++;
      if (!box) {
        if (tries < 80) return;                                    // chat never loaded (~12 s)
        clearInterval(pending); pending = null;
        navigator.clipboard?.writeText(question); say("Question copied. Paste it into the chat."); return;
      }
      if (!ready(doc)) {
        if (!told && tries > 6) { told = true; say("Waiting for the current answer to finish…"); }
        if (tries < 1200) return;                                  // give up after ~3 minutes
        clearInterval(pending); pending = null;
        navigator.clipboard?.writeText(question); say("Question copied. Paste it into the chat when the answer finishes."); return;
      }
      clearInterval(pending); pending = null;
      const type = el => {
        el.focus();
        if (el.isContentEditable) {
          el.textContent = question;
          el.dispatchEvent(new InputEvent("input", { bubbles: true }));
        } else {
          const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value").set;
          setter.call(el, question);
          el.dispatchEvent(new Event("input", { bubbles: true }));
        }
      };
      type(box);
      let waits = 0;                                               // the button enables once the text is in
      const click = setInterval(() => {
        // On a fresh pop-up Chainlit mounts the message box a second time once its session connects, and the new box
        // is empty: type the question again into whichever box is there now.
        const now = doc.querySelector("#chat-input");
        if (now && (now !== box || !(now.value ?? now.textContent))) { box = now; type(box); }
        const submit = doc.querySelector("#chat-submit");
        if (submit && !submit.disabled && (box.value ?? box.textContent)) { clearInterval(click); submit.click(); }
        else if (++waits > 40) {
          clearInterval(click);
          box.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
        }
      }, 100);
    }, 150);
  }
  document.addEventListener("click", ev => {
    const b = ev.target.closest(".ask[data-q]");
    if (!b) return;
    open(true);
    send(b.dataset.q);
  });

  // --- citations and site links: swap the main page in place while the chat is open ---
  // A full page load would reload the chat iframe and drop the conversation, so once the chat exists, same-site links
  // (and citation links clicked inside the chat) fetch the page and replace <main> instead.
  const main = $("#main");
  const internal = href => {
    const u = new URL(href, location.href);
    return u.origin === location.origin && (u.pathname === "/" || u.pathname.startsWith("/wiki/")) ? u : null;
  };
  // Highlight the cited section: its own <details>, or (a chunk under a parent heading) every subsection under it.
  // body.cite-open is the only state: it dims the other sections (site.css); clicking elsewhere or Esc clears it.
  function clearCite() {
    document.body.classList.remove("cite-open");
    main.querySelectorAll(".cited").forEach(el => el.classList.remove("cited"));
    main.querySelectorAll(".citetag").forEach(el => el.remove());
  }
  function reveal(hash, label = "") {
    clearCite();
    const id = decodeURIComponent((hash || "").slice(1));
    const exact = id && document.getElementById(id);
    // No section in the link: the chunk is the page's opening text. That is the lead paragraph, or on pages without one
    // (characters) the text the snapshot's Markdown puts at the end of the Infobox section.
    const opening = () => { const lead = main.querySelector(".page > .lead") || document.getElementById("sec-infobox");
                            return lead ? [lead] : []; };
    const hits = exact ? [exact] : id ? [...main.querySelectorAll(`details[id^="${CSS.escape(id)}-"]`)]
      : label ? opening() : [];
    if (!hits.length) { window.scrollTo(0, 0); return; }
    hits.forEach(el => {
      if (el.tagName === "DETAILS") el.open = true;
      el.classList.add("cited");
      if (label) {
        const tag = document.createElement("span");
        tag.className = "citetag"; tag.textContent = `Cited as ${label}`;
        const summary = el.querySelector(":scope > summary");
        summary ? summary.append(tag) : el.prepend(tag);   // right end of a section heading; top right of the lead
      }
    });
    document.body.classList.add("cite-open");
    hits[0].scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }
  main.addEventListener("click", ev => { if (document.body.classList.contains("cite-open") && !ev.target.closest(".cited")) clearCite(); });
  window.addEventListener("keydown", ev => {
    if (ev.key === "Escape" && document.body.classList.contains("cite-open")) { clearCite(); ev.stopImmediatePropagation(); }
  }, true);
  async function go(u, push = true, label = "") {
    try {
      const res = await fetch(u.pathname);
      if (!res.ok) throw new Error(res.status);
      const doc = new DOMParser().parseFromString(await res.text(), "text/html");
      main.innerHTML = doc.querySelector("#main").innerHTML;
      document.title = doc.title;
    } catch { location.href = u.href; return; }   // fall back to a normal page load
    if (push) history.pushState(null, "", u.pathname + u.hash);
    initMain();
    main.classList.remove("swapped"); void main.offsetWidth; main.classList.add("swapped");   // replay the entrance
    reveal(u.hash, label);
    main.focus({ preventScroll: true });
  }
  window.addEventListener("popstate", () => { if (frame) go(new URL(location.href), false); else location.reload(); });
  document.addEventListener("click", ev => {
    const a = ev.target.closest("a[href]");
    if (!frame || !a || a.target || ev.defaultPrevented || ev.button || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    const u = internal(a.getAttribute("href"));
    if (!u) return;
    ev.preventDefault();
    if (u.pathname === location.pathname && u.hash) { history.pushState(null, "", u.hash); reveal(u.hash); return; }
    go(u);
  });

  // Inside the chat: a citation ("S2 Lauma" in the Sources line, or the S2 badge in the answer) opens the cited section
  // in the main page. Chainlit's own source view is not used in the narrow pop-up, where it would cover the answer (#97).
  function wireChat() {
    const doc = frame.contentDocument;
    if (!doc || doc.__wired) return;
    doc.__wired = true;
    doc.addEventListener("click", ev => {
      if (ev.button || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
      const badge = ev.target.closest(".element-link");   // itself an <a href="#">
      let link = badge ? null : ev.target.closest("a[href]");
      if (badge) {   // the badge's message also has "Sn [Title](/wiki/…)" in its Sources line: the link right after Sn
        const label = badge.textContent.trim();
        for (let box = badge.parentElement; box && box !== doc.body && !link; box = box.parentElement)
          link = [...box.querySelectorAll(".element-link")].map(b => b.nextElementSibling)
            .find(a => a?.matches('a[href*="/wiki/"]') && a.previousElementSibling.textContent.trim() === label);
      }
      const u = link && internal(new URL(link.getAttribute("href"), frame.contentWindow.location.href).href);
      if (!u) return;
      ev.preventDefault(); ev.stopPropagation();
      const before = link.previousElementSibling;   // "S2" badge right before a Sources-line link
      const label = badge ? badge.textContent.trim() : before?.matches(".element-link") ? before.textContent.trim() : "";
      // On phones the panel covers the page: fold it away to show the source (the launcher brings the chat back as it was)
      if (matchMedia("(max-width: 560px)").matches) open(false);
      if (u.pathname === location.pathname) { history.pushState(null, "", u.hash || u.pathname); reveal(u.hash, label); return; }
      go(u, true, label);
    }, true);
    // Chainlit opens its source view by itself when an answer arrives; in the pop-up it is a dialog over the answer.
    // Close it with its own ✕ button (a synthetic Escape is ignored): the main page shows the sources instead.
    const closeView = () => {
      const dialog = doc.getElementById("side-view-content")?.closest('[role="dialog"]');
      dialog?.querySelector("button.absolute")?.click();
    };
    new MutationObserver(() => { if (doc.getElementById("side-view-content")) requestAnimationFrame(closeView); })
      .observe(doc.body, { childList: true, subtree: true });
  }

  document.addEventListener("DOMContentLoaded", initMain);   // after the helpers below this block are defined
})();


// Wiki images load from another server; if one fails, drop it so no broken-image icon shows.
var WIKI_IMG = "img.thumb, img.mini, img.regionimg, img.pageimg, img.bannerimg";
document.addEventListener("error", (ev) => { if (ev.target.matches?.(WIKI_IMG)) ev.target.remove(); }, true);
function dropBrokenImages() {   // images that failed before this script ran, or before a swapped-in page was wired
  document.querySelectorAll(WIKI_IMG).forEach(i => { if (i.complete && !i.naturalWidth) i.remove(); });
}

// Home banner background video: plays the newest characters' gameplay clips in turn, muted. "Pause background" stops
// it and fades back to the key art image; if no clip loads, the key art stays.
function initBanner() {
  const v = document.querySelector(".bannervideo"), btn = document.querySelector(".bgtoggle");
  if (!v) return;
  const reel = JSON.parse(v.dataset.reel || "[]"), credit = document.querySelector(".bannercredit");
  const still = credit && { text: credit.textContent, href: credit.getAttribute("href") };
  if (!reel.length) return;
  let i = 0, fails = 0, paused = false, started = false;   // team decision: plays for everyone; Pause shows the key art
  const load = () => {
    const c = reel[i];
    v.src = c.src;
    if (credit) { credit.textContent = `Gameplay: ${c.name}`; credit.href = c.href; }
    v.play().catch(() => {});
  };
  v.addEventListener("playing", () => { if (paused) { v.pause(); return; } v.classList.add("on"); btn.hidden = false; fails = 0; });
  // Browsers may pause muted background video to save power (hidden tab, off screen): resume when it can play again.
  // The visitor didn't pause it (paused === false), so any other pause is the browser's: try again, a few times.
  let retries = 0;
  const resume = () => {
    if (!started || paused || !v.paused || v.ended || retries > 8) return;
    retries++;
    v.play().catch(() => {});
  };
  v.addEventListener("canplay", resume);
  v.addEventListener("pause", () => setTimeout(resume, 400));
  v.addEventListener("playing", () => { retries = 0; });
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
  const showCredit = () => {
    if (!credit) return;
    if (paused && still) { credit.textContent = still.text; credit.href = still.href; }
    else { credit.textContent = `Gameplay: ${reel[i].name}`; credit.href = reel[i].href; }
  };
  btn.addEventListener("click", () => {
    paused = !paused;
    if (!paused && !started) { started = true; load(); }
    else if (paused) { v.pause(); v.classList.remove("on"); }       // fade the video out: the key art shows again
    else { retries = 0; v.play().catch(() => {}); }               // "playing" fades it back in
    label(); showCredit();
  });
  started = true; load();
}
