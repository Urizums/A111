# Forward calibration execution: frozen author contract

This bounded build-and-run task uses the original `inputs/request.md` and `inputs/PROBLEM.md`, their four raw files, and Forge C13 only. It delivers a reusable pure-Markdown workflow, all origin-specific residual tables and provenance, executable reproduction and a short Chinese scientific explanation. It is neither a full contest paper nor a model-performance/general-utility experiment. No external research is needed: the decision is availability bookkeeping on supplied synthetic data. Source reading is bounded by the coordinator packet; general AGENTS startup pointers are overridden by that narrower packet. No root/global metadata is changed.

## Decisions before computation

- Label policy: **latest available at each decision origin**, inclusive `available_at <= decision_origin`. No use of evaluation-cutoff labels for calibration. The supplied cutoff is preserved as context only.
- Fixed forecast: records must have arrived by their own `forecast_origin`, and that origin must be no later than the decision. Among eligible revisions select greatest `(available_at, revision)`; conflicting same-version payloads reject. This case has one fixed forecast origin. Multiple fixed origins require an explicit selector; the program rejects ambiguity.
- Coordinates: each date requires every unique coordinate in `series.csv`; a revision is the same coordinate, and identical retransmission is the same observation with multiple source lines.
- Residual: selected actual minus selected original forecast, units 件. Complete vector arrival is the maximum selected prediction/label arrival across required coordinates. Partial residuals are auditable but excluded from calibration vectors.
- Insufficient samples: publish the actual complete-vector count, never impute or silently include incomplete dates. No interval, uncertainty guarantee, or learned predictor is justified by this task.
- Source references: CSV line number includes header line; source hashes bind provenance to exact input bytes. All timestamps are offset-aware and this task uses UTC+08:00 / Asia/Shanghai.

## Frozen receiving checks

| Gate / purpose | Source requirement and input | Assertion and reject condition | Evidence / checker | Failure route and claim limit |
| --- | --- | --- | --- | --- |
| Preflight | Original attachments, input lock, C13 lock, recorder | Hashes match; required schemas are parsable; runtime exists | Recorded preflight command, author | Missing identity/capability stops dependent work; preparation alone proves no result |
| Smoke | Raw→producer→tables→Chinese-note consumer | First origin is computed from raw, exact-boundary label is retained, incomplete dates excluded; numerical table and provenance match raw | Recorded run and author receiving checker | Preserve failure; repair affected interface. Bounded smoke cannot establish every new dataset |
| Relevant rejection | Same-key conflicting label; consumer using a later revision | Parser rejects ambiguous observation; receiver rejects future version even if file is valid JSON | Real invalid fixture/command and mutated output/command, expected nonzero logs | Rejection success is an author check, not an independent verdict |
| Mandatory author checks | Both origins, all source records and published tables | Recompute source selection, residuals, vector set, arrival max, dedup, fixed forecast restrictions, consistency between JSON/CSV/note | Recorded source-bound checker, requirement map | A contradiction blocks author-complete status; no assertion weakened after failure |
| Reproduction | Raw input and shipped source | New absent output directory, run from different cwd, byte-identical deterministic results | Recorded clean run + comparison | Keep different invocation identities; rerun is not original execution |
| Delivery | Workflow, outputs, code, checks, history | Portable workflow decisions/roles/interfaces/branches, usable instructions, current paths/hashes/checkpoint | Author inspection + manifest | Independent acceptance belongs to coordinator's fresh context; author claim is self-checked only |

## Roles and handoffs

This single actor performs specification, data audit, production and author receiving checks. Those are distinct responsibilities, not independent actors. The coordinator owns any independent judgment. The workflow names roles to make future use transferable; it does not require delegation or specific models. Unknown model/tokens/cost are null. All writes, tests, generated fixtures, and receipts stay below `runs/R20/forward-case/production/`; code/tests are outside `calibration-flow/`.

## Scope, resources and stopping

No model/page quota or universal two-error stop applies. Retain failures and classify tool recovery, substantive correction and planned iteration separately. Continue a changed, supported action within authorization; stop an unchanged path with no new evidence, actual resource/permission boundary, user stop, or completion. Complete this original calibration delivery, checkpoint and stop writes. Do not invent a successor stage or submit/publish anything.
