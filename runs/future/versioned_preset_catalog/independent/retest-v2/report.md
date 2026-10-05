# Independent catalog v2 retest

**Terminal state:** execution completed after one Chromium browser run. **Semantic result: blocked / not fully accepted.** The v2 candidate passed 74 of 76 recorded checks; the two failures are the 390 CSS-pixel visible-keyboard-focus checks for Review and Stock. The original v1 report and host reply remain frozen in `../worker/` and were not edited. This is an independent follow-up record, not a new host job or acceptance invocation.

## Scope and candidate identity

This retest applies the original frozen acceptance cases (`catalog`, `review`, `stock`, `reader`, `access`) and original local interaction data to candidate `v2`, without adding criteria. The check plan was frozen in `check-plan.md` before inspecting v2 implementation. The candidate lock identifies version `1.0.1`, source revision `R05-original-web-v1-repair1`, and one candidate repair used of two. The lock SHA-256 is `21bf751e539ab76ff09e143eee3a74789d7ff3afa3db4265bd2624dca78d616b`.

The four post-run source hashes matched both the lock and pre-run capture:

| File | SHA-256 |
|---|---|
| `index.html` | `83f313c11c722b9d8c985bf4c34896b94aebf8ff407715cdb65535837507eb89` |
| `styles.css` | `091df585fb6efee5ba3dc53a86f2759691bc5332fcdb92674e8784abb87feec1` |
| `app.js` | `dc4d6e6a5dba225d7f58418a9bbd56264c0fef69770e1e2cda7ae74de2358e96` |
| `catalog.json` | `df2c9a59ee7b8d6b9b2701db74ead3d2b724a35dc3cea62229800bdcaae2e625` |

Full post-run digest capture: `logs/post-run-hashes.sha256`. The lock and candidate inputs were not modified.

## Execution

Environment: Python 3.12.14, Python Playwright synchronous API, Chromium `/usr/bin/chromium` version `151.0.7922.173`. One local server was started only on `127.0.0.1:8766`, one browser harness invocation ran, and the server was stopped with Ctrl-C. The harness recorded nine requests, all to the loopback origin; there were zero console errors, page errors, or journey errors. No external network or business effect was used.

Actual commands are preserved in `logs/commands.md`; browser output is `logs/run-1.log`, raw structured output is `browser-results.json`, and server lifecycle/output is `logs/server.log`. This was the only v2 browser run. Both available harness corrections had already been used, so no further correction or rerun was made.

## Original acceptance mapping

| Acceptance case | Result | Observed evidence |
|---|---|---|
| `catalog` | Pass, 11/11 checks | Schema/version `1.0.1`; all three original variants and four locked source hashes; seven hashed source references with observation-only reuse; seven paired semantic token colors, all at least 4.5:1; layouts, states, motion, browser scope and limitations declared. |
| `review` | Pass, 12/12 checks | Three rows loaded; unmatched/clear/title filter worked; original R-041 “北侧展厅照明调整” selected; keyboard confirmation applied with focus handling; Escape/cancel returned focus; R-042/R-043 stayed pending; retryable read error retained rows and recovered. |
| `stock` | Pass, 6/6 checks | `12x` was rejected without losing input; busy state blocked duplicate submit; browser-local quantity 14 and note “首次实盘记录” persisted and restored after reload; explicit 18-vs-22 conflict retained quantity 22 and “保留的草稿” on cancel, then saved version 3 locally. |
| `reader` | Pass, 9/9 checks | Contents link targeted and focused the section; annotation “第一版批注” was stored and restored after reload; simulated save failure retained “重试后的第二版批注”, retry saved it; edit cancel preserved saved content; delete cancel preserved the annotation and keyboard confirmation removed it. |
| `access` | Partial, 34 pass / 2 fail | All 9 view/width combinations had no horizontal overflow; all 48 scanned rendered controls had names; reduced-motion information/transition/scroll checks passed for all three views; all 59 sampled rendered text contrast readings were at least 6.147:1. Visible keyboard focus passed in 7 of 9 view/width checks. Review and Stock each failed at 390px: the sampled active element was `BODY` with `outlineStyle: none`. |

The two failed observations are preserved verbatim in `browser-results.json` and `results.json`. They prevent acceptance under the original `access` case. The sample does not establish a general focus failure outside those two recorded states; the other seven sampled focus checks passed.

The catalog’s source-reported scope remains responsive web. Physical Android, screen-reader certification, user studies, global performance, backend persistence, and real approval, inventory, or document authority were not tested or claimed.

## Failure-driven harness corrections

The original validation allowance began at zero corrections; this retest used both available corrections, leaving zero. Each is retained separately with its predecessor/evidence and diff:

1. `logs/correction-1.md` / `logs/correction-1.diff`: v1 failures showed fixed waits did not observe actual keyboard completion or delayed localStorage state, and a stock conflict assertion expected copy not present in the rendered dialog. The harness moved to state-based waits, reported keyboard outcome separately, and matched the displayed conflict values.
2. `logs/correction-2.md` / `logs/correction-2.diff`: v1’s control scan included controls in collapsed state-example disclosures. The harness opens the disclosures before scanning and reads rendered controls only.

The v1 harness and failed outputs remain preserved under `../worker/`; these are harness corrections, not candidate source changes. The v2 run completed with no journey error and exposed the two access failures above. No additional harness correction was made.

## Screenshots and terminal record

These browser screenshots were captured and opened for visual pixel review:

- `screenshots/review-1280.png` — Review, 1280 × 900.
- `screenshots/stock-390.png` — Stock, 390 × 844.
- `screenshots/reader-320.png` — Reader, 320 × 800.

The original host job remains committed blocked. No new job, host reply, or C3 preflight was created for this retest. The independent terminal state is execution-complete with acceptance blocked by the two recorded 390px focus checks. See `results.json` and `evidence-manifest.json` for the structured result and artifact hashes.
