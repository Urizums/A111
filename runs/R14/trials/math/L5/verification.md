# Verification record — math-level-5

## Input and frozen method

- Raw task: `runs/R14/cases/math/problem.json`; the solver records its SHA-256 in `results.json`.
- Request: `runs/R14/cases/math/L5/request.json`; original requirements m1–m5 were treated as acceptance assertions.
- Candidate: C9 lock and the eight listed Forge skill/reference files were read. Their observed SHA-256 values match the lock. Candidate source repairs are not this trial's repair budget.
- Scope: one synthetic offline case, no network, no other actors, no real contest submission.

## Requirement-to-evidence review

| Requirement | Evidence and performed check | Status / limit |
| --- | --- | --- |
| m1 usable workflow | `workflow.md` gives raw inputs, decisions, owner, concrete outputs, receiver checks, failures/stops, smoke and handoff. | Producer checked against request; no independent acceptance. |
| m2 forecast and validation | `solve.py` reads supplied rows; `results.json` contains week-9 predictions, baseline, expanding origins 4–8, 15 errors per method, MAE and signed errors. Code review confirms each slice ends before its target. | Executed successfully. Validation has only five origins and cannot establish future accuracy. |
| m3 integer allocation | Result records A28/B2/C30, 60 total, caps, per-station objective terms, total 264.928571 CNY, 24,076 feasible vectors enumerated, and next distinct gap 1 CNY. | Self-recomputed from recorded terms and constraints; enumeration establishes optimum for this finite model. Cost/penalty inputs are assumed. |
| m4 traceability and claims | `paper.md` values match `results.json`; generated PNG is visually inspected and labels demand/forecast rate separately from allocation units. Limits distinguish sample from contest evidence. | Figure visually legible at rendered size. No empirical week-9 comparison, awards or verified uncertainty claimed. |
| m5 source, smoke and malformed rejection | Main CLI receipt exits 0 and records numerical output. Malformed cost receipt exits 1 with `INPUT REJECTED`; neither result nor figure is produced for that invocation. `solve.py` source was inspected for schema/type/unit failure behavior. | Producer self-check only. This is not independent acceptance or exhaustive malformed-input testing. |

## Command observations

Commands were retained by the repository's existing `scripts/record_command.py`:

- `receipt-main.json`: first end-to-end CLI run; exit 0.
- `receipt-malformed.json`: bad-cost-unit CLI run; exit 1, error says `delivery_cost_per_unit.A must be finite and nonnegative`; no success result was emitted.
- `receipt-main-correction-1.json`: rerun after the first plot's y-axis wording did not distinguish demand rate from allocated units; exit 0.

Visual review found the first plot technically plotted correct values but its shared units/week y-axis could misstate the allocation units. That version is retained as `figure-attempt-1.png`. The source label was corrected and the rendered final `forecast_allocation.png` was inspected. This is one failure-driven correction in this trial. There were no other failed solver attempts. No additional correction round is authorized after the original limit of two; one remains unused.

## Independence and unresolved evidence

All checks above were performed by the artifact producer/coordinator in one context. No fresh independent acceptor was available or used, so independent acceptance remains unverified. The provided data do not include week-9 actuals, data provenance beyond the prompt, uncertainty calibration, or empirically justified costs and penalties. The requested model label is not provider telemetry; authenticated model, tokens and cost are unknown and remain null in `result.json`.
