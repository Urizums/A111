# Independent validation report: preset catalog v1

**Disposition: blocked / not accepted.** The local browser run found working filters, persistence, retry and responsive behavior, but a keyboard activation of the dialog’s focused Confirm control closed the dialog without applying the review decision or annotation deletion. The review success wait timed out, and the final stock conflict write was still busy when the harness sampled localStorage. Those are unresolved acceptance paths, so this report does not grant semantic acceptance.

## Scope and integrity

I read the immutable host request and original brief, then `acceptance.json`, and froze the checks in `check-plan.md` before inspecting candidate code. I used only `candidate/v1/` and `candidate-lock.json`; I did not inspect sibling reports, Root tests, state, or expected outputs. I made no candidate/source edits and made no failure-driven corrections or reruns.

Chromium 151.0.7922.173 ran through Python Playwright 3.12.14 against a Python HTTP server bound to `127.0.0.1:8765`. The server was stopped after the single run. Recorded requests were loopback-only. Chromium’s automatic `GET /favicon.ico` received a 404 and produced one console error; there were no uncaught page errors.

All four candidate file hashes matched the frozen candidate lock both before and after the run:

| Candidate file | SHA-256 |
| --- | --- |
| `index.html` | `4ce5d4060b7f53cecd06656e40919e57da2e6942c1e9951ce94b0b706e4b2b24` |
| `styles.css` | `091df585fb6efee5ba3dc53a86f2759691bc5332fcdb92674e8784abb87feec1` |
| `app.js` | `d730e51f1f2aa76bb2b12819c23ad3484c9260c886d24cf8cc37853148649746` |
| `catalog.json` | `04ad4df1b3c52ab9fd779d709f2ddf095cba3e46f7842e5dfda8eaf21611e9fa` |

The saved source copies and lock are in `source_snapshots/`. The frozen plan SHA-256 is `9610d879335bd2d785e8d3a84ce7b00dbba22f62b5f144062236696e11d127c3`. The original brief SHA-256 matches the host request: `1d93a516f107b120548e5fb9cc0d41d924a9a683424c6669718b6f0ff633564d`.

## Catalog checks

The catalog declares schema `forge-preset-catalog/1`, version `1.0.0`, source revision `R05-original-web-v1`, and three variants: dense review queue, handheld stock count, and long document with annotations. Each names its responsive web platform, layout, and states. The stock entry explicitly says physical Android is unverified. The catalog states default and reduced-motion behavior, and limits its claims to local examples without backend, physical-device, assistive-technology, or productivity proof.

Seven external source declarations have 64-character snapshot hashes and the reuse label `observation_only_no_assets_or_code_reused`; catalog-wide reuse says the implementation uses original authored code and tokens. The source declarations were inspected locally, but I did not fetch external snapshots. All seven declared semantic color pairs exceed 4.5:1 by calculation: surface 14.679, primary 6.702, selected 8.490, error 7.597, success 7.294, warning 6.607, and annotation 11.363.

## Browser observations

The review queue loaded three records. Searching for an unmatched phrase showed the empty state; Clear restored the three rows; searching `北侧` found original record R-041, which could be selected. Escape and the Cancel button both closed the confirmation dialog without changing the record and returned focus to the approval trigger. After tabbing to Confirm and pressing Enter, the dialog closed but the expected approval status did not appear within 30 seconds. The review journey therefore stopped before verifying confirmation and preservation of unrelated rows.

The stock form rejected `12x`, retained the entered value, and exposed an error. A valid quantity and note saved as localStorage version 1; both values and the restored-status message survived a page reload. The delayed save disabled its button and exposed `aria-busy`; a second programmatic submit did not create a second version. The conflict example wrote an incoming version 2 while retaining the user’s quantity and note. Cancel preserved that draft. The conflict confirmation showed both compared quantities. The harness’s phrase check expected “另一份” although the actual dialog body presents the current and draft quantities without that phrase. A later pointer confirmation showed the “saving” status and disabled button in `stock-390.png`, while the immediate storage sample still showed version 2; the final version 3 write was not captured, so conflict resolution remains unverified.

The reader contents link focused the selected heading. A new annotation persisted in localStorage and reappeared after reload. The simulated retryable save error retained the edited draft while leaving the previous saved note intact; the next save persisted the draft. Canceling a later edit preserved the saved note. Canceling deletion preserved the annotation and returned focus to its Delete button. Tabbing to Confirm and pressing Enter closed the dialog but left the annotation stored and visible, so keyboard deletion did not complete.

At 1280, 390, and 320 CSS px, each of the three views had equal document/body width to the viewport: no horizontal overflow was measured in any of the nine combinations. A 3px visible focus outline was measured in all nine. Reduced motion kept each view’s text unchanged, set the section transition duration to zero, and did not enable smooth scrolling. The rendered-text contrast snapshots had no sampled ratios below 4.5:1.

I opened and inspected the saved full-page screenshots. The 390px stock view showed a single-column item card and form with no horizontal clipping; its capture caught the conflict save while busy. The 320px reader view showed the contents links, reading column, and annotation within the viewport width. Its full-page capture was taken after anchor navigation and places the fixed skip link over the scrolled content in the stitched image; this is recorded as a screenshot capture condition, not a separate browser behavior claim.

## Evidence and limits

`browser-results.failed1.json` and `logs/run-1.log` preserve the unmodified first-run observations. `logs/failure-1.md` records the exact command and failure before any later action. The accessible-name sweep reported the stock and review example buttons inside collapsed `details` as unnamed because it read `innerText` from descendants that were not visible. The source markup gives those buttons text labels, so those three flags are not treated as verified unlabeled visible controls; a corrected visible-control sweep was not run. The one review timeout, incomplete stock conflict write observation, and keyboard-confirmation findings remain unresolved.

Screenshots:

- `screenshots/stock-390.png` — SHA-256 `6b7e6ae2f2ac3114781795f846dc9610edc29c1e25153e6c1fb806bf068faf93`
- `screenshots/reader-320.png` — SHA-256 `c65dd99fd408e22b2323c1ff3f52e9cebac77ed9c0495d295499da951422abd8`

This is evidence from a browser-local example only. It does not establish real approval or inventory authority, physical Android behavior, screen-reader certification, assistive-technology conformance, a user study, or global performance. The separate host reply draft and captured `check-reply` preflight are protocol evidence only, not semantic acceptance.
