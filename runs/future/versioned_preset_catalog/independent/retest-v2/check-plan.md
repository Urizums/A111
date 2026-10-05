# Frozen independent v2 retest plan

Frozen from the original immutable `acceptance.json` / `catalog-validation-brief.md` and my own v1 report/results, before inspecting candidate v2 implementation. This is the same three-variant catalog acceptance, not a new sample or job.

## Scope and evidence boundaries

- Target only `/workspace/A111/runs/future/versioned_preset_catalog/candidate/v2/` and `/workspace/A111/runs/future/versioned_preset_catalog/candidate-v2-lock.json`.
- Compare v2 against the original acceptance IDs `catalog`, `review`, `stock`, `reader`, and `access` and the same original task data (R-041 review item; stock starting at 12, invalid `12x`, local draft 14, conflict sample 18 vs draft 22; annotation create/edit/error/retry/delete).
- Use Chromium at `/usr/bin/chromium` with Python Playwright at CSS viewport widths 1280, 390, and 320, including keyboard operation and reduced motion. Only serve the candidate from a loopback-bound local HTTP server; stop it after the run. Record console/page errors and all requests.
- Keep v1's `worker/` tree untouched. Write all retest-v2 outputs only in this directory. Do not inspect Root diagnostics, tests, repair notes, sibling research/reports, state, or expected outputs; do not modify candidate files.
- Retain localStorage before and after reload, dialog return/focus behavior, screenshots opened for pixel review, the exact original candidate sources and hashes, and every command and run result.

## Acceptance checks

1. **Catalog:** version/schema and all three task/platform variants; source hashes and reuse declarations; semantic token pairs and contrast; per-variant layouts/states; motion; explicit browser/platform support and limitations.
2. **Review:** filter, empty state, clear, select R-041, cancel then confirm, unrelated rows remain, Escape closes, focus returns. Record keyboard activation separately from mouse activation so one cannot be mistaken for the other.
3. **Stock:** reject invalid input without loss; verify the busy/duplicate guard; persist to actual browser localStorage and reload; trigger the explicit conflict sample; retain the draft on cancel; resolve and wait for the final saved localStorage version/status before reporting success.
4. **Reader:** use contents links; create and edit a local annotation; persist and reload; cancel editing; cancel and confirm deletion; exercise simulated retryable failure and confirm the draft survives and retries successfully.
5. **Responsive/access:** all three views at all three widths with no horizontal overflow; visible keyboard focus; verify names for controls actually rendered/reachable (including state-sample controls after opening their details); measure key rendered text contrast at 4.5:1 or higher; reduced motion retains information, removes the optional transition, and avoids smooth scrolling.
6. **Visual/runtime:** retain and open the target-width screenshots; preserve actual console and page errors; record candidate lock hash and source hashes before/after.

## Failure and correction ledger

The v1 task used one browser run and zero failure-driven harness corrections. The original acceptance budget was two corrections; both remain available for this v2 retest. A failure-driven correction must be preserved as its own version/change note, with the exact preceding harness and error saved before any subsequent run. Count each code/evidence-serialization change separately. Stop at a third failure; do not reset evidence, patch candidate sources, or run beyond the remaining budget.
