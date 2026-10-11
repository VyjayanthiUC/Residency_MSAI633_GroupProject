/* Deck icons (SVG <symbol>, viewBox 24, stroke = currentColor). Game-flavoured icons — element emblems e-*, primogem r-primo,
 * Mora r-mora, gold emblem s-emblem-gold — come from genshin-quest (icons/gq-icons.js, icons/gq-emblems.js).
 * Use: <svg class="ico"><use href="#m-retrieval"/></svg> */
document.body.insertAdjacentHTML("afterbegin", `<svg width="0" height="0" style="position:absolute;overflow:hidden" aria-hidden="true"><defs>
<symbol id="m-data" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 3.5h10.5L19 7v13.5H5Z" fill="currentColor" fill-opacity=".15"/><path d="M15.5 3.5V7H19M8 11h8M8 14h8M8 17h5"/></symbol>
<symbol id="m-indexing" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <rect x="3" y="7" width="11" height="14" rx="1.5" fill="currentColor" fill-opacity=".15"/><path d="M7 4h11.5A1.5 1.5 0 0 1 20 5.5V17"/><path d="M6 11h5M6 14h5M6 17h3" stroke-linecap="round"/></symbol>
<symbol id="m-retrieval" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
  <circle cx="10.5" cy="10.5" r="6.5" fill="currentColor" fill-opacity=".15"/><path d="m15.5 15.5 5 5"/><path d="M8 10.5h5M10.5 8v5" stroke-width="1.6"/></symbol>
<symbol id="m-generation" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2.5 20 5.5v6c0 5-3.4 8.6-8 10.5-4.6-1.9-8-5.5-8-10.5v-6Z" fill="currentColor" fill-opacity=".15"/><path d="M9 15.5c3-1 5-4 6-8-3 1-6 3.5-6 8Zm0 0-1 1.5"/></symbol>
<symbol id="m-chat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <path d="M4 5h16v11H11l-5 4v-4H4Z" fill="currentColor" fill-opacity=".15"/><path d="M8 9.5h8M8 12.5h5" stroke-linecap="round"/></symbol>
<symbol id="m-evaluation" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 3.5h12v17H6Z" fill="currentColor" fill-opacity=".15"/><path d="m8.5 9 1.5 1.5L13 7.5M8.5 15l1.5 1.5 3-3M15 9.5h1M15 15.5h1"/></symbol>
<symbol id="i-refuse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
  <circle cx="12" cy="12" r="9" fill="currentColor" fill-opacity=".14"/><path d="M5.6 18.4 18.4 5.6"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="9" fill="currentColor" fill-opacity=".14"/><path d="m7.5 12.5 3 3 6-7"/></symbol>
<symbol id="i-cross" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
  <circle cx="12" cy="12" r="9" fill="currentColor" fill-opacity=".14"/><path d="m8.5 8.5 7 7M15.5 8.5l-7 7"/></symbol>
<symbol id="i-memory" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M9 4.5a3 3 0 0 0-5 3 3.5 3.5 0 0 0 0 6 3 3 0 0 0 5 3.5V4.5ZM15 4.5a3 3 0 0 1 5 3 3.5 3.5 0 0 1 0 6 3 3 0 0 1-5 3.5V4.5Z" fill="currentColor" fill-opacity=".15"/><path d="M9 20v-3.5M15 20v-3.5"/></symbol>
<symbol id="i-book" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <path d="M2.5 5.5c3.2-1.4 6.4-1.3 9.5.6 3.1-1.9 6.3-2 9.5-.6v13.2c-3.2-1.3-6.4-1.2-9.5.6-3.1-1.8-6.3-1.9-9.5-.6Z" fill="currentColor" fill-opacity=".15"/><path d="M12 6.2v13.3"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
  <circle cx="12" cy="12" r="9" fill="currentColor" fill-opacity=".14"/><path d="M12 7v5l3.5 2"/></symbol>
<symbol id="i-robot" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <rect x="4.5" y="8" width="15" height="11" rx="3" fill="currentColor" fill-opacity=".15"/><path d="M12 8V4.5M9.5 13h.01M14.5 13h.01" stroke-linecap="round" stroke-width="2.6"/><path d="M2.5 12v3M21.5 12v3" stroke-linecap="round"/></symbol>
<symbol id="i-hash" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
  <path d="M9 4 7 20M17 4l-2 16M4.5 9h16M3.5 15h16"/></symbol>
<symbol id="i-person" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
  <circle cx="12" cy="8" r="4" fill="currentColor" fill-opacity=".15"/><path d="M4.5 20.5c1.2-4 4-6 7.5-6s6.3 2 7.5 6"/></symbol>
</defs></svg>`);
