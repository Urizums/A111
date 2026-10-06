# Level 7 offline modeling workflow

## Brief and raw-input audit

**Task:** self-created offline practice, not a contest submission. Read `problem.json` as the sole numerical source. Q1 forecasts each station's week-9 demand (units/week) from weeks 1–8 and tests a one-step chronological forecast rule. Q2 chooses nonnegative integer week-9 units under station caps and 60 total units, minimizing delivery cost plus penalty on unmet *integer-rounded forecast demand* (CNY). Q3 needs reproducible code, source audit, plot and a paper-style note. No week-9 actual is supplied, so forecast accuracy for week 9 cannot be claimed.

Audit checks: row count, ordered unique week identifiers, station fields, numeric finite nonnegative demands, units, missing/duplicate counts, ranges, and all optimization coefficients/caps. Do not treat text embedded in data as authorization. If required inputs are missing or malformed, stop and name the exact field; restore from the frozen source before solving. No future actual, external data or network research is used.

## Workflow and handoffs

| Step / trigger | Inputs | Owner | Output and receiving check | Failure / stop |
|---|---|---|---|---|
| 1. Freeze and audit | Original request and `problem.json` | Data role (same operator here) | Audit in `results.json`; check weeks, fields, types, units, duplicates/missingness | Reject malformed input; preserve exact error and request correction |
| 2. Define questions | Q1–Q3 above | Coordinator | Forecast target and decision contract; confirm forecast is week 9, not actual | Resolve consequential ambiguity before model choice |
| 3. Compare forecast rules | Weeks 1–8 | Model role | Expanding-origin one-step folds for persistence and linear trend, targets weeks 4–8; choose smaller pooled MAE, tie to persistence | Ensure each fold uses earlier weeks only; no future leakage |
| 4. Forecast | All observed weeks, selected rule | Solver role | Per-station numerical week-9 forecast in units/week | Stop on nonfinite/negative output; preserve predictions as estimates |
| 5. Allocate | Forecast, caps, stock, costs and penalties | Optimization role | Integer plan, objective recomputed from formula, cap/stock checks, marginal-value optimality certificate | Reject infeasible plan or certificate mismatch; do not silently relax constraints |
| 6. Integrate and explain | Results JSON and figure | Paper role | Paper equations and values trace to result; figure labels state units/source | Remove any claim lacking data or check; reconcile changed values |
| 7. Smoke and acceptance | Frozen raw input, code, actual outputs | Producer then checker | Main run and malformed-cost rejection recorded; requirement map in verification | Producer checks are not independent. Mark acceptance unverified if no fresh checker is available |
| 8. Deliver / hand off | All outputs | Coordinator | Reproduction command, file map, limits and next use in `result.json` | Stop when mandatory outputs/checks are done or repair budget is exhausted |

Roles may be combined for this small exercise. One operator doing both production and checks is not independent acceptance. A later user should provide a new problem JSON preserving the schema, run the command below, inspect the result against the original problem, and only then consume the forecast/plan. For a real competition, verify current official track rules, amendments, AI limits, data license and submission conditions from the organizer; this practice run did not inspect or infer them.

## Equations and method decisions

For each station, compare (a) persistence, \(\hat y_{t}=y_{t-1}\), and (b) least-squares straight-line trend fit using only observations before target week \(t\). Score pooled MAE over expanding-origin forecasts for weeks 4–8. This deliberately small comparison is interpretable; eight observations cannot support a general forecasting claim. Refit the selected rule to weeks 1–8 for week 9.

Let \(d_i=\lceil\hat y_{i,9}\rceil\), decision \(x_i\in\mathbb Z_{\ge0}\). Minimize \(\sum_i c_i x_i+p_i\max(d_i-x_i,0)\), subject to \(x_i\le u_i\) and \(\sum_i x_i\le60\). Integer rounding is an explicit operational choice because the decision is indivisible. For each unit up to \(d_i\), objective improvement is \(p_i-c_i\); above \(d_i\), improvement is \(-c_i\). Sorting all positive unit improvements and taking up to available stock gives an exact optimum for this separable objective. Recompute the stated objective independently from returned allocations and verify caps/stock. A solver status alone would not prove optimality.

## Check contract

- Main smoke: run the actual script against the frozen source, then check fold chronology, numeric forecast, integer/cap/stock feasibility, recomputed objective and figure existence plus visual readability.
- Boundary smoke: change A delivery cost from numeric 2 to the string `two CNY`; the same production entry point must exit nonzero with a clear field error and produce no success result.
- Acceptance: map m1–m5 to workflow/output, validation and predictions, allocation certificate, paper/figure trace, and both command receipts. Here the producer performed the checks; no separate fresh acceptor is claimed.
- Stop: retain failures and cumulative correction count; after 2 failure-driven correction rounds, stop this case. Unknown model identity, token usage and cost remain null.

## Reproduction

From the repository root, run the retained main-path recorder (Python 3.12, UTF-8):

```powershell
py -3.12 -X utf8 scripts/record_command.py --out runs/R14/trials/math/L7/reproduction.json -- py -3.12 -X utf8 runs/R14/trials/math/L7/solve.py --problem runs/R14/cases/math/problem.json --outdir runs/R14/trials/math/L7
```

For the supplied malformed boundary fixture, expect nonzero exit and no successful output:

```powershell
py -3.12 -X utf8 runs/R14/trials/math/L7/solve.py --problem runs/R14/trials/math/L7/malformed-cost.json --outdir runs/R14/trials/math/L7/malformed-output
```

The archived receipts show the actual runs made in this trial; the command above is a repeatable recipe, not an additional run.
