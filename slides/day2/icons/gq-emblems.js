/* Element emblems drawn in code (viewBox 64): e-anemo, e-geo, e-electro, e-dendro, e-hydro, e-pyro, e-moon, e-cryo, plus a few
 * UI symbols. Stroke uses currentColor. From aozaki's genshin-quest project, reused with the author's permission. */
document.body.insertAdjacentHTML("afterbegin", `<svg width="0" height="0" style="position:absolute;overflow:hidden" aria-hidden="true"><defs>
<symbol id="e-anemo" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
  <path d="M10 24c10-1 24-1 30-6 5-4 1-11-5-9-4 1-4 6-1 7"/><path d="M6 34c14 0 34 1 42-4 7-4 5-14-3-13"/>
  <path d="M12 44c10 0 22 0 28 4 5 4 1 11-5 9-4-1-4-6-1-7"/><circle cx="52" cy="44" r="2.5" fill="currentColor" stroke="none"/></symbol>
<symbol id="e-geo" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round">
  <path d="M32 6 52 20 46 52H18L12 20Z" fill="currentColor" fill-opacity=".14"/><path d="M32 6v20M12 20l20 6 20-6M18 52l14-26 14 26"/></symbol>
<symbol id="e-electro" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round">
  <circle cx="32" cy="32" r="25" stroke-opacity=".45" stroke-dasharray="4 5"/><path d="M36 8 20 35h11l-4 21 17-29H33Z" fill="currentColor" fill-opacity=".22"/></symbol>
<symbol id="e-dendro" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 52C10 28 26 10 54 10c0 28-18 44-42 42Z" fill="currentColor" fill-opacity=".16"/><path d="M12 52 40 24M24 40h10M30 34l1-10M36 28h8"/></symbol>
<symbol id="e-hydro" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M32 6C24 20 16 28 16 39a16 16 0 0 0 32 0c0-11-8-19-16-33Z" fill="currentColor" fill-opacity=".16"/><path d="M22 40c4 3 8 3 10 0s6-3 10 0"/></symbol>
<symbol id="e-pyro" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M32 58c-11 0-18-8-18-18 0-12 10-16 10-28 7 4 11 10 11 17 3-3 4-6 4-10 7 6 9 13 9 21 0 10-6 18-16 18Z" fill="currentColor" fill-opacity=".18"/>
  <path d="M32 58c-5 0-8-4-8-8 0-6 6-8 6-14 5 4 10 8 10 14 0 4-3 8-8 8Z"/></symbol>
<symbol id="e-moon" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round">
  <path d="M40 8a24 24 0 1 0 16 38A20 20 0 0 1 40 8Z" fill="currentColor" fill-opacity=".16"/>
  <path d="M46 16l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="currentColor" stroke-width="1.5"/></symbol>
<symbol id="e-cryo" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
  <path d="M32 6v52M9.5 19l45 26M9.5 45l45-26"/><path d="M26 10l6 6 6-6M26 54l6-6 6 6M10 26l8 2-2-8M54 38l-8-2 2 8M10 38l8-2-2 8M54 26l-8 2 2-8"/>
  <circle cx="32" cy="32" r="5" fill="currentColor" fill-opacity=".3"/></symbol>

<symbol id="s-archon" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <path d="M6 12l4 3 6-8 6 8 4-3-2 9H8Z" fill="currentColor" fill-opacity=".25"/><path d="M16 20l3.5 4-3.5 4-3.5-4Z" fill="currentColor"/><circle cx="16" cy="6" r="1.4" fill="currentColor"/></symbol>
<symbol id="s-legend" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6">
  <circle cx="16" cy="16" r="11" stroke-dasharray="2 3"/><path d="M16 4l2.6 9.4L28 16l-9.4 2.6L16 28l-2.6-9.4L4 16l9.4-2.6Z" fill="currentColor" fill-opacity=".3" stroke-linejoin="round"/></symbol>
<symbol id="s-world" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6">
  <circle cx="16" cy="16" r="12"/><circle cx="16" cy="16" r="8.5" stroke-opacity=".4"/><path d="M16 5l3 11-3 11-3-11Z" fill="currentColor" fill-opacity=".3" stroke-linejoin="round"/><path d="M5 16h3M24 16h3"/></symbol>
<symbol id="s-trail" viewBox="0 0 32 32" fill="currentColor">
  <ellipse cx="10" cy="22" rx="3.2" ry="4.6" transform="rotate(-12 10 22)" fill-opacity=".85"/><circle cx="7.6" cy="15.6" r="1.1"/><circle cx="10.2" cy="15" r="1.1"/><circle cx="12.6" cy="15.8" r="1.1"/>
  <ellipse cx="21" cy="12" rx="3.2" ry="4.6" transform="rotate(12 21 12)" fill-opacity=".55"/><circle cx="18.6" cy="5.6" r="1.1" fill-opacity=".6"/><circle cx="21.2" cy="5" r="1.1" fill-opacity=".6"/><circle cx="23.6" cy="5.8" r="1.1" fill-opacity=".6"/></symbol>
<symbol id="s-act" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <path d="M4 6h24"/><path d="M5 6c0 9 2 16 5 20h3c-2-6-3-13-3-20M27 6c0 9-2 16-5 20h-3c2-6 3-13 3-20" fill="currentColor" fill-opacity=".25"/></symbol>
<symbol id="s-node" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <path d="M9 28V5"/><path d="M9 6h15l-4 5 4 5H9" fill="currentColor" fill-opacity=".3"/><path d="M9 28l-3-3 3-3 3 3Z" fill="currentColor"/></symbol>
<symbol id="s-forge" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
  <path d="M5 13h17c0 3 2 4 5 4v2H21l-2 4h4v3H9v-3h4l-2-4H5Z" fill="currentColor" fill-opacity=".25"/><path d="M14 4l6 6M12 6l4-4 4 4-4 4Z"/></symbol>
<symbol id="s-bounty" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8">
  <circle cx="16" cy="16" r="11"/><circle cx="16" cy="16" r="6"/><circle cx="16" cy="16" r="1.8" fill="currentColor"/><path d="M16 2v6M16 24v6M2 16h6M24 16h6"/></symbol>
<symbol id="f-cal" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3.5" y="5" width="17" height="15" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/><path d="M12 13.2l1.1 2.2 2.2 1.1-2.2 1.1L12 19.8l-1.1-2.2-2.2-1.1 2.2-1.1Z" fill="currentColor" stroke="none"/></symbol>
<symbol id="f-due" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M6 3h12M6 21h12M7 3c0 5 10 5 10 9s-10 4-10 9M17 3c0 5-10 5-10 9s10 4 10 9"/><path d="M9.5 18.5h5L12 16Z" fill="currentColor"/></symbol>
<symbol id="f-clock" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2.5"/></symbol>
<symbol id="f-repeat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11a7 7 0 0 1 12-5l2 2M20 13a7 7 0 0 1-12 5l-2-2"/><path d="M18 3v5h-5M6 21v-5h5"/></symbol>
<symbol id="f-home" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3l8 6v11H4V9Z" fill="currentColor" fill-opacity=".15"/><path d="M12 11l2 3-2 3-2-3Z" fill="currentColor"/></symbol>
<symbol id="f-wait" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="9" cy="8" r="3.5"/><path d="M3 20c.5-4 3-6 6-6 1.2 0 2.3.3 3.2.9"/><circle cx="17.5" cy="16.5" r="4.5"/><path d="M17.5 14.5v2l1.5 1"/></symbol>
<symbol id="f-win" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 16h18"/><path d="M7 16a5 5 0 0 1 10 0"/><path d="M12 5v3M5 9l2 2M19 9l-2 2"/></symbol>
<symbol id="f-status" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l9 9-9 9-9-9Z"/><path d="M12 8l4 4-4 4-4-4Z" fill="currentColor"/></symbol>
<symbol id="b-move" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="5" width="13" height="13" rx="2"/><path d="M2.5 9.5h13M6 3v4M12 3v4M15 14h7M19 11l3 3-3 3"/></symbol>
<symbol id="b-portal" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><ellipse cx="12" cy="12" rx="6.5" ry="9.5"/><path d="M12 6c-2.5 0-3.5 2.5-3.5 6s1 6 3.5 6M12 9.5c-1 0-1.5 1-1.5 2.5s.5 2.5 1.5 2.5"/><path d="M3 12h2M19 12h2" stroke-opacity=".6"/></symbol>
<symbol id="b-skip" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 6l6 6-6 6M13 6l6 6-6 6"/></symbol>
<symbol id="b-enter" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h5v16h-5"/><path d="M3 12h11M10 8l4 4-4 4"/></symbol>
<symbol id="b-wake" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M5 10h14l-1.5 9h-11Z" fill="currentColor" fill-opacity=".2"/><path d="M12 3v8M9 6l3-3 3 3"/></symbol>
</defs></svg>`);
