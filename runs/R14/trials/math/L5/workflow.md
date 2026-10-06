# L5 offline modeling workflow — math-level-5

## Working brief

This is a self-created practice case, not an active contest submission. The source packet is `runs/R14/cases/math/problem.json`: eight chronological weekly demand rows for stations A, B, C, with week-9 forecasting followed by a capped integer allocation. Demand is in units/week; week-9 allocations are integer units; costs and shortage penalties are CNY/unit. All supplied data are treated as available at the end of week 8. The given costs and penalties are task parameters, not empirically calibrated values. No future week-9 actual is available.

The frozen implementation is `solve.py`; it reads the original problem JSON at runtime and writes `results.json` and `forecast_allocation.png`. Run from repository root:

```powershell
py -3.12 -X utf8 runs/R14/trials/math/L5/solve.py --problem runs/R14/cases/math/problem.json --out runs/R14/trials/math/L5/results.json --figure runs/R14/trials/math/L5/forecast_allocation.png
```

The same command was executed through `scripts/record_command.py`; receipts are retained alongside the outputs. Paths are explicit so a new case can be run by pointing `--problem`, `--out`, and `--figure` to its own frozen inputs and output folder.

## Questions and interfaces

| Question / trigger | Inputs and decision | Owner | Output and receiving check | Failure / stop |
| --- | --- | --- | --- | --- |
| Q1: week-9 forecast | Validate chronological weekly rows, station fields, finite nonnegative numeric demands, and units. Compare last-observation baseline with per-station least-squares linear trend using expanding-window one-step forecasts at weeks 4–8. Select lower pooled MAE (ties go to baseline), refit on weeks 1–8. | Data/model producer | `results.json.forecast`: method, three numerical forecasts, split origins, pooled and station MAE, signed errors. Receiver recomputes that each training slice ends before its target and checks counts/metrics from source rows. | Reject malformed/time-disordered input; retain error and ask for corrected source. No week-9 actual means realized forecast accuracy remains unknown. |
| Q2: week-9 allocation | Forecast vector, stock 60, station caps A30/B25/C35, delivery costs (2,1,3), unmet penalties (8,6,10). Choose integer `x_i`; minimize `sum(c_i*x_i + p_i*max(yhat_i-x_i,0))`; enforce `0<=x_i<=cap_i` and `sum(x_i)<=60`. | Optimization producer | `results.json.allocation`: integer vector, total, objective and per-station terms. Receiver checks integrality, caps, stock and recomputes the objective; exhaustive feasible-vector enumeration supplies a global optimum certificate for this small instance. | Stop if input values are invalid or no feasible vector exists. Preserve the failure; do not impute cost values or relax constraints silently. |
| Q3: integration and paper | Accepted source rows, forecast, allocation and plot data. | Coordinator/paper producer (same context as solver) | `paper.md` values must trace to `results.json`; plot axes distinguish demand/forecast rate from week-9 integer allocation. Reviewer checks paths, reproduction command, figure labels and consistency. | If a number cannot be traced, correct or qualify the paper; producer review is not independent acceptance. |
| Delivery gate | Original requirements plus code, raw JSON, results, figure, receipts and docs. | Coordinator; a separate acceptor would need a fresh context | `verification.md` records requirement-by-requirement evidence, status and limits. | No independent actor was used in this bounded run. Mark independent acceptance unavailable rather than claiming it. |

## Frozen checks and stop conditions

1. **Preflight:** confirm the named inputs exist and the locked Forge C9 documents match `C9-lock.json`; use only the supplied offline data and installed Python 3.12 scientific stack.
2. **Raw audit:** preserve the raw JSON; verify week sequence, field set, values, units, missing cells, duplicate weeks and per-station ranges. The supplied eight rows have no missing or repeated weeks and all demands are nonnegative integers.
3. **Forecast gate:** run both methods on the same 15 station-origin forecasts (five targets × three stations), always with earlier weeks only. Report the small sample and avoid claims of general predictive superiority.
4. **Optimization gate:** enumerate every feasible integer allocation, recompute the objective independently from allocation terms, verify caps and stock. Report the search space and next distinct objective as an auditable optimality check.
5. **End-to-end smoke:** execute the production CLI on the original file and inspect numerical outputs and the rendered PNG. Execute the same CLI on the specified malformed cost-unit variant; it must return nonzero with an input-rejection message and must not write a success result.
6. **Acceptance/delivery:** map each original requirement to source, artifact, and performed check. Self-checks are producer evidence only; independent acceptance requires a separate reviewer with raw input and actual outputs. Stop after mandatory deliverables and checks or after two failure-driven corrections, preserving every failure.

## Responsibility and handoff

One coordinator owns the source snapshot, method choice, integration and final limits. In this small instance the coordinator also performed data, modeling, coding and paper roles; those labels do not create independent verification. A subsequent user should receive the original problem JSON, this workflow, `solve.py`, exact command, results, plot, both good/bad input receipts, and the explicit open limitation that no week-9 outcome or independent acceptor exists. Any change to the problem, objective, parameter source, forecast selection rule or validation split must be recorded as a new scope/version and rerun through the same receiving checks.
