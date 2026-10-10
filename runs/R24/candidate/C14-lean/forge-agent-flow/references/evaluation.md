# Evaluate the claim that matters

Use this reference when a workflow makes a consequential claim, needs a substantive smoke test or will be reviewed by another actor. The check should be as specific as the result: a simple extraction needs source comparison, a numerical model needs numerical checks and a UI needs interaction in its actual permitted runtime.

Before an implementation is judged, agree on the original required outcome and what observation would make it fail. This can be a sentence for simple tasks or a fuller acceptance contract for complex ones. Avoid turning a reviewer preference, more elaborate modeling or additional styling into an invented mandatory gate.

## A small test should still be real

A useful smoke test travels from real input through the central operation to something the user or next consumer can inspect. Where a claim depends on a boundary, exercise it: loading on a floor is not evidence for transmitted stacked load; a valid-input-only test is not evidence that malformed data is rejected. Smoke covers that path only. It does not establish all original requirements, broad reliability or production performance.

For numerical work, check sources, units and the original objective or hard constraints; use a baseline or independent recomputation where appropriate. Do not silently accept NaN or infinity as a valid finite value, and do not allow an output label to redefine the original source. For UI work, compilation and screenshots can support a static claim, but a functional claim requires actual browser or platform interactions, state and error handling. For research synthesis, check original passages and the reach of the stated conclusion.

When a critical number is repeated across CSV, chart, narrative and PDF, compare the computation, units, rounding and the final visible representation. A direct check may be enough; extensive registries and automatic cross-format tests are justified only when repeated complex output makes them valuable.

## Give independent reviewers enough, but not the answer

Producers supply real artifacts and may self-check. Where independent review is part of the claim, the reviewer must be a genuinely separate context with original requirements, legitimate raw sources and access to the produced artifact, but without expected answers, author diagnoses or previous verdicts. Account for whatever the host actually forwards, including logs, command arguments and summaries; directory boundaries alone do not establish independence. If separation is impossible or unknown, label the verdict informed or independence unverified.

Ask reviewers to identify which requirement was tested, what actual observation supports or contradicts it, and the scope of their conclusion. A reviewer should be able to reject an error using evidence, not merely endorse a polished report. For consequential reviewer reliability, optional controlled valid/defective pairs can expose false acceptance and false rejection; do not make this a standard extra stage for trivial tasks.

## Preserve the meaning of the result

Keep the distinction between planned, produced, self-checked, accepted and delivered. An exit code, CI pass or author's declaration does not establish substantive acceptance. Missing checks remain unverified rather than silently successful.

When a check fails, retain the original case and verdict. Repair the implicated behavior, source interpretation, interface or check, then rerun the relevant assertion; any later informed fix must not be described as the first blind success. Respect fixed experimental conditions and actual resource limits, but do not generalize one trial's repair quota to all future work. See [iteration and recovery](iteration-and-recovery.md).

Evidence supports observations under stated conditions, not unlimited causal or performance claims. Do not infer unknown provider identity, token expense, timing or broad competition performance from labels, file size or eloquent explanation.
