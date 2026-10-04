# Independent preset browser acceptance

## Result

The final main browser run passed its action journeys on the assigned local preset. One additional 390px review found a limited keyboard focus visibility issue in the horizontal primary navigation: the Preferences link can be reached and activated by keyboard, but its right side and part of its focus outline remain clipped until the navigation is scrolled horizontally. Pointer scrolling reveals the full link. This finding is recorded in `results.json` and `mobile-nav-access-attempt-1.json`.

The original brief required “desktop and 390px narrow keyboard/pointer operation and horizontal overflow/scroll access” and said “Visible internal scrolling is not automatically a defect; verify all controls accessible.” The exact target clauses are:

```html
<nav class="primary-nav" aria-label="Sample workspace sections">
  <a href="#overview">Overview</a>
  <a href="#runs" aria-current="location">Runs</a>
  <a href="#workflows">Workflows</a>
  <a href="#settings">Preferences</a>
</nav>
```

```css
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
summary:focus-visible {
  outline: 3px solid var(--color-focus);
  outline-offset: 3px;
}

@media (max-width: 680px) {
  .primary-nav {
    display: flex;
    overflow-x: auto;
    gap: var(--space-1);
  }
  .primary-nav a {
    flex: 0 0 auto;
  }
}
```

These clauses are in [ui-presets.html](/workspace/A111/skills/design-product-experience/assets/ui-presets.html:19), [ui-presets.css](/workspace/A111/skills/design-product-experience/assets/ui-presets.css:191), and [ui-presets.css](/workspace/A111/skills/design-product-experience/assets/ui-presets.css:834). At 390×844, six Tab presses focus Preferences while `nav.scrollLeft` stays 0; its right edge is 418.125px while the nav edge is 374px, clipping about 44px. The screenshot shows the clipped text and outline. Enter changes the URL fragment to `#settings`. A horizontal pointer wheel scroll sets `scrollLeft` to 44 and brings the link inside the nav. This finding is about full visual focus visibility; it does not mean the link is unreachable or cannot be activated.

## Frozen scope and source identity

I read the original brief and both required design references before inspecting the target, then froze checks in [expected-checks.md](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/expected-checks.md) before reading target code. The supplied brief SHA-256 is `e15c163677c869ecd68fecd99ae57fe48e258c0fa61e538505325313b3c54423`; the frozen checks SHA-256 is `de22d0172f13b00cad1e89237b24f36ce35362078ab903a12020a853388bd968`.

The unchanged assigned sources were:

- `/workspace/A111/skills/design-product-experience/assets/ui-presets.html` — SHA-256 `1382fe6726dba5b81aaa91ba83e77de59bcefb910594e78e9b6122582c52d688`
- `/workspace/A111/skills/design-product-experience/assets/ui-presets.css` — SHA-256 `39483287fceec40f32ecf54f24fbc630cd63e03e2811986283689b190611657a`

The original three local rows were `r-1842` / Release checks / succeeded, `r-1841` / Release checks / failed, and `r-1840` / Dependency audit / succeeded. The HTML explicitly says this is fictional local sample data with no account or network connection, and that refresh is simulated; I make no real-service claim.

## Browser evidence

Chromium 151.0.7922.173 (`/usr/bin/chromium`) with Python Playwright ran headlessly at 1440×1000 and 390×844. The server bound only to `127.0.0.1:8765` and served the source assets directory. No target source was edited. The exact server command was:

```sh
python -u -m http.server 8765 --bind 127.0.0.1 --directory /workspace/A111/skills/design-product-experience/assets > /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/server.log 2>&1
```

The acceptance harness command was run three times, each from a fresh browser page:

```sh
python -m py_compile /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/validate_presets.py && python /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/validate_presets.py
```

The final run verified the original rows; text/status filters, empty feedback and clear; detail close by Escape and named control with focus returned to the opener; Run again adding one queued row for the selected Dependency audit workflow; delete cancel retaining the row and confirmation removing only the selected row; refresh busy/current-row feedback, cancel/retry and recoverable-error retry; independent palette and density changes; both drawer motions and a usable reduced-motion state; desktop and 390px keyboard/pointer interaction; document/table overflow access; semantic names; focus visibility; and rendered text contrast.

The 390px document width remained 390px. The table had a 358px client width and 369px scroll width; scrolling it exposed the last-column View control. The two palette captures measured representative text at or above the 4.5:1 normal-text threshold. The live queued label was absent from the fresh three-row contrast capture, so it was measured separately: 6.82:1 in Clear and 11.73:1 in Night. The `results.json` records computed foreground/background colors and ratios. The desktop Tab traversal visited all 19 visible controls with a 3px focus outline; keyboard opening and Escape closing the detail drawer returned focus to its View button.

Screenshots were opened and visually inspected:

- [Desktop initial](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/desktop-initial.png)
- [Desktop detail drawer](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/desktop-detail.png)
- [Desktop keyboard focus](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/desktop-keyboard-focus.png)
- [Night palette](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/desktop-night-palette.png)
- [390px initial](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/mobile-390-initial.png)
- [390px detail drawer](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/mobile-390-detail.png)
- [390px keyboard focus on Preferences](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/mobile-nav-keyboard.png)
- [390px after pointer horizontal scroll](/workspace/A111/runs/future/preset_browser_acceptance/independent/worker/screenshots/mobile-nav-pointer-scroll.png)

## Attempts, failures, and limits

Attempt 1 passed the main action journeys through motion, but failed three harness checks: the empty-state form reset was asserted before its scheduled reset handler ran, and two later browser-evaluation expressions had malformed selectors. Chromium also requested `/favicon.ico`, producing a 404 unrelated to either assigned source. The full result and server log are retained in `attempt-1-results.json` and `server-attempt-1.log`.

Attempt 2 corrected those expressions and waited for the scheduled empty-state reset. It exposed a second harness issue: earlier pointer activity left Chromium’s sequential Tab position near the end of the page, so the scan sampled `body` after the final control. It also caught the ordinary Clear filters reset before the scheduled filter update. The diagnostics and full failures remain in `attempt-2-results.json` and `tab-diagnostic-flow.json`.

Attempt 3 made the second and final main-harness correction: it waited for Clear filters to apply and started focus-order measurement in a freshly loaded page. All main-harness outcomes passed; the separate navigation finding above remains. The final `raw_errors` list is empty. The initial favicon 404 was suppressed with a local 204 route in later runs; no non-loopback network was used.

A separate mobile-navigation probe intentionally stopped at its first failed keyboard-scroll assertion; that failure is the responsive focus visibility finding above, not a repaired or hidden harness failure. Independent pointer-scroll and Enter-activation evidence is retained in `mobile-nav-pointer-access.json` and `mobile-nav-keyboard-activation.json`. A separate live queued-status contrast probe passed in both palettes. The preliminary Playwright import probe’s teardown warning is preserved in `setup-probe.log`; the actual acceptance runs use a correctly scoped Playwright context manager and do not reproduce it.

The first `hostdraft.py reply` invocation included `--flow-outcome` and was rejected because that option applies only to package requests; its exact response is in `hostdraft-reply-attempt-1.json`. A second invocation with the supplied new request and no package-only flag created the separate incomplete `reply-draft.json`. The final `check-reply` output is captured in `reply-preflight.json`; that protocol preflight does not establish semantic acceptance.

No user study, global performance result, real backend behavior, or service-level claim was run or inferred. Token count, cost, provider identity, and active time are unavailable and recorded as `null`.
