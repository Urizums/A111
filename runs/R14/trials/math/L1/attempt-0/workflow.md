# Reusable offline modeling workflow

## Working brief

Use for a supplied, bounded modeling problem. Preserve the original prompt and raw input; record their paths and SHA-256 before analysis. Separate prediction, optimization, and reporting questions; write units, decision-time information, constraints, objective, and acceptance evidence before selecting a method. Here this is an eight-week, three-station self-created practice case, not a contest submission.

| Step / trigger | Inputs | Decision or operation | Owner | Output / receiving check | Failure / stop |
|---|---|---|---|---|---|
| Intake | Request, problem JSON, supplied rules/materials | Check completeness, types, units, chronology, provenance, malformed variants | Coordinator/data checker | Source identity and input audit; fields and units match schema | Preserve failure; request corrected source if a required value is unusable |
| Formulate | Audited raw values and question | Classify prediction/optimization; define variables, units, assumptions and metric | Modeler | Equations and time-availability boundary; another reader can map every symbol to input | Stop affected calculation if objective, unit, or constraint is ambiguous |
| Forecast | Observations available at each decision origin | Fit interpretable baseline; compare using expanding chronological origins and naive baseline | Forecast owner | Predictions plus origin-by-origin errors; verify no target/future data enters fit | Mark forecast unsupported if temporal leakage or unusable data is found |
| Allocate | Accepted prediction, stock, caps, costs and penalties | Solve integer objective; verify feasibility and recompute objective; enumerate small cases when practical | Solver owner | Executable code and result JSON; independent arithmetic/constraint check | Reject infeasible or unrecomputable output; retain failed run |
| Communicate | Checked numbers and provenance | Plot with units/source; write paper from result file | Writer | Every paper/figure value traces to result JSON and raw source | Remove unsupported interpretation; do not invent rules, citations, or awards |
| Receive / hand off | Original requirements and all actual artifacts | Check requirements, rerun command, malformed-input rejection, paper/figure consistency | Coordinator; independent acceptor only if separately assigned | Verification record, open gaps, next action | Label unchecked work; stop at budget or material boundary |

## Decisions for this case

- Prediction: separate ordinary least-squares line for each station, demand (units/week) against week number, extrapolated to week 9. The fit sees weeks 1–8; no week 9 actual demand exists or is used.
- Validation: for targets 3–8, refit on all earlier weeks only; compare mean absolute error with last-observation forecast. This is a small descriptive backtest.
- Allocation: minimize `Σ[c_i x_i + p_i max(d̂_i − x_i, 0)]`, with integer `0 ≤ x_i ≤ cap_i`, and `Σx_i ≤ 60`. Enumerate feasible triples to establish the exact minimum for these inputs and this objective.
- Ownership: one coordinator integrates; data/model/solver/writer/checker are workflow responsibilities, not additional actors. No independent acceptance is claimed.
- Stop/accept: stop on malformed required values, missing units/objective, infeasibility, or exhausted correction budget. Accept a bounded run only after raw-source inspection, rerun, temporal check, feasibility/objective recomputation, boundary rejection, and paper/plot traceability. A completed command alone is not acceptance.
- Handoff: pass raw input identity, code, reproduction command, outputs, assumptions, performed checks, failed attempts/budget, unknowns, and next action to the next user. For real contest use, first inspect the current official edition, track-specific rules, AI-use terms, corrections, and submission requirements; this offline exercise does not establish them.

Reproduce from the workspace root with `python -X utf8 runs/R14/trials/math/L1/solver.py` (numpy and matplotlib required). Outputs are written alongside the code.
