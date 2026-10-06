# Independent prospective protocol review (v2)

## Scope and evidence

This review evaluates the revised protocol as a prospective documentation design against the supplied R10 request and minimal original records. It does not re-execute or regrade the R10 business case, inspect its deliverables, or claim historical acceptance, C8 behavioral validation, or measured improvement. SHA-256 and byte-size checks matched all six entries in `runs/R12/review/v2/frozen-lock.json`.

## Findings

The revised protocol resolves the two design gaps noted by the prior review. Under “判定与交接,” it explicitly requires material claims to distinguish direct observation, causal explanation, and future expectation, with source/check details for observations, assumptions and alternatives for inferences, and remaining verification for forecasts. It permits these labels to be embedded in the existing record, keeping the process lightweight. Under “缺项和中断,” it now explicitly says that a cumulative count above the limit must remain visible (example 3/2), cannot be capped or reset, and requires stopping further corrections while preserving drafts and receipts and recording counted attempts and where the boundary crossing was found. Uncertain chronology is to remain marked unknown; no ledger repair or rerun is allowed to fill a gap.

Those decisions fit the supplied records. The R10 request sets a two-correction budget and requires an offline, reusable weekly workflow, actual batch triage, source pointers, honest limitations, and no execution framework. The allowed native final return reports a cumulative 3/2, labels the batch draft unverified, names a known F3 wording error, and states that raw-input checking, a correction ledger, and a result file were not completed. These are directly observed claims about what that return says; they do not prove the underlying batch contents or quality. The revised protocol's above-limit and artifact-status rules give a suitable way to preserve such a result without converting it into acceptance.

The original command receipt records argv, cwd, begin/end, and exit code 0, but lacks an explicit state field and captures a very large inherited environment, including identity/configuration detail despite redacting some values. The terminal transcription identifies itself as a transcription of the same actual call, binds to the receipt by path and SHA-256, adds `state=finished`, and says the original remains unchanged. The protocol correctly requires queue start records to contain the terminal state while also saying finished describes the command only, and it advises using existing receipts, minimizing collected environment data, preserving source lineage, and not treating command success as business completion. This is a strong fit for the observed evidence gap and excess capture.

The compact evaluation table offers adequate source traceability through requirement, source location, actual artifact/receipt, inspection, and limitation. The protocol also clearly separates coordination/record integration from independent business verification and requires the final recipient to inspect the actual artifact. I found no actionable remaining design defect in the allowed evidence set.

## Recommendation

**Adopt for prospective documentation and evaluation work.** The revisions make claim provenance and over-limit repair handling explicit without adding a product runtime or bespoke recording framework. Apply it only under each case's own frozen requirements and budget. This recommendation is limited to protocol design; it does not replace or change R10's historical outcome and does not establish C8 behavior or measured improvement.

## Limits and case boundary

Only the v2 request, revised protocol/lock, R10 request, first command receipt, its terminal transcription, and native final return were inspected. The raw feedback packet, C8 skill, business outputs, and other repository conclusions were outside the allowed set. Item-level triage quality and the complete chronology of the R10 correction count therefore remain unverified.

The v2 request records the case-wide cumulative correction count as 2/2. The coordinator's supplied accounting identifies two prior source/orchestration corrections: a rejected corrective patch construction that made no mutation, followed by a recovery/source-revision attempt. I did not inspect their records, so I report those as request-supplied accounting rather than independent observations. My internal review correction count is 0/2. No repair or rerun was attempted in this review. Model telemetry, token use, and cost were unavailable and are not inferred.
