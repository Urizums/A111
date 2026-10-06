# Independent prospective protocol review

## Scope and evidence

This review evaluates the proposed protocol as a documentation design against the supplied R10 request and the minimal records named by the R12 request. It does not re-execute or regrade the R10 business case, inspect its deliverables, or claim historical acceptance, C8 behavioral validation, or measured improvement. SHA-256 and byte-size checks matched all six files in `runs/R12/review/frozen-lock.json`.

## Findings

The protocol makes several sound, concrete decisions. It preserves original requirements, candidate/input identity, and frozen correction limits; assigns business production and evidence retention distinct responsibilities; says a command's finished state is not business completion; prefers existing receipts over a new recording framework; distinguishes one invocation from multiple records; and requires unresolved state when terminal status cannot be established. It also explicitly treats the final recipient's inspection of the actual artifact as necessary. These provisions fit the small R10 team and the R10 request's offline, no-runtime, reusable-workflow scope.

The supplied original records demonstrate why the receipt guidance matters. `runs/R10/validation/independent/evidence/first-command.json` records actual argv, cwd, begin/end, and exit code 0, but its environment capture is very large and includes identity/configuration detail despite redacting some values. The protocol's advice to avoid complete environment capture and its caveat that redaction cannot guarantee safety are directly relevant. `runs/R10/resumption/first-command-terminal.json` is a transcription of that same invocation, bound to the original receipt by SHA-256, and adds `state=finished`; it correctly says it is not a new execution and leaves the original record unchanged. The R10 final return reports 3/2 corrections and an unverified draft with a known wording error, no raw-input check, no correction ledger, and no result file. These facts show the importance of preserving over-limit failures and truthful artifact status; they do not establish the underlying business result.

Two protocol changes are needed before unqualified adoption:

1. **Require explicit claim provenance.** The protocol asks for separate reporting of observed business correctness, performance, and generalization, and says conclusions must be tied to checks. It never directly requires authors to label each material statement as directly observed, inferred, or a future-effect claim. In particular, causal and prospective claims can still be folded into a conclusion without a required evidence/assumption marker. Add a compact claim-status field (for example, `observed`, `inferred`, `forecast`) and require source/check plus assumptions for inferred and forecast claims. This addresses R12 r1 without requiring a special framework.
2. **Make over-limit handling explicit.** The protocol says all case-related failure-driven corrections count, and that work stops at the frozen boundary. The supplied final return states 3/2, so it shows an overrun can appear in the record. The protocol should state that a count above the limit remains above-limit, is never normalized to the limit, and triggers stop/preserve/report; also require the ledger to identify the counted attempts and whether the boundary was crossed before detection. This makes the existing preservation principle actionable when the observed count exceeds the budget.

Traceability is adequate in principle: the table asks for original requirement, source location, artifact/receipt, inspection and verdict, and limitation. The transcription record's source path and hash exemplify a useful binding. A small wording improvement would require stable paths/identifiers for every cited source and distinguish a source record from a transcription; this is a usability refinement, not a blocker.

## Recommendation

**Conditional adoption for prospective documentation use**, after the two changes above. The protocol is proportionate and intentionally avoids product runtime or bespoke evidence machinery; its existing-receipt approach is sufficient for the supplied evidence shape. Adoption should remain limited to documentation and evaluation procedure. This review does not establish R10 business acceptance, C8 behavior, or an improvement in outcomes. No historical case should be reopened or relabeled on the strength of this design review.

## Limits

Only the R12 request, frozen protocol/lock, R10 request, first command receipt, its terminal transcription, and the native final return were inspected. The raw feedback packet, C8 skill, business outputs, and other repository conclusions were outside the allowed review set. I cannot verify item-level triage, actual correction chronology beyond the returned count, or whether any other receipt/artifact changes these observations. Model identity telemetry, token usage, and cost were unavailable; none is inferred from a requested model label or workspace metadata.
