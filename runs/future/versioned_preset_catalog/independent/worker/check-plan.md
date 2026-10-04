# Frozen independent validation plan

Frozen before candidate implementation inspection, from `acceptance.json` and the original validation brief.

## Scope and evidence rules

- Target only `/workspace/A111/runs/future/versioned_preset_catalog/candidate/v1/` and its `candidate-lock.json`.
- Treat this as a local browser interaction example. No real approvals, inventory/document authority, physical Android, screen-reader certification, global performance, or user-study claims.
- Run only Chromium at `/usr/bin/chromium` with Python Playwright. A scoped loopback-only server may serve the candidate and must be stopped at the end. No external network or delegation.
- Preserve the initial sources and hashes. Do not modify candidate/source files. Capture browser observations, console and page errors, screenshots and localStorage evidence.
- Maximum two failure-driven corrections to the independent harness, each separately retained with the original failed harness, command, error and repair recorded before any rerun. At a third failure, stop without patching or rerunning.

## Checks

1. **Catalog integrity:** inspect catalog version and all three task/platform variants; verify source hashes, paired semantic tokens, reuse scope, states, motion definitions, and explicit supported browser scope against the candidate sources and lock.
2. **Review journey:** exercise filtering, empty state, clearing, selection of the original review record, cancel and confirm decision; verify unrelated rows remain; use Escape and verify keyboard focus returns to the triggering control.
3. **Stock journey:** submit an invalid count and confirm input remains; trigger busy state and verify duplicate submission is prevented; verify actual browser `localStorage` persistence after reload; open the explicit conflict sample and verify the draft is preserved through cancel and resolution.
4. **Reader journey:** navigate table of contents; create and edit an annotation and verify actual local persistence; cancel and delete only after confirmation; trigger the simulated retryable error and verify draft preservation.
5. **Responsive/access checks:** at CSS viewport widths 1280, 390, and 320 px, verify no horizontal page overflow and reachable labeled controls, visible keyboard focus, key rendered text contrast at least 4.5:1, and reduced-motion mode without information loss.
6. **Visual/browser evidence:** use live UI observations and inspect opened screenshots/pixels for the key screens at the target widths. Record browser console and page errors throughout.

## Run/repair discipline

- Before each run, preserve the exact harness used. If a run fails due to the independent harness, archive that original harness and record its exact command and error before making one separately counted correction.
- Do not rerun after the third failure; do not clear or replace evidence files.
- Save final `report.md`, `results.json`, and the required host reply only under the assigned `worker/` directory. Include exact hashes and captured host preflight, keeping draft/preflight separate from semantic acceptance.
