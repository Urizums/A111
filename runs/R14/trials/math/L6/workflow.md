# L6 offline modeling workflow

**Scope.** Practice-only case `offline-demand-allocation-01`; raw source `runs/R14/cases/math/problem.json`. This offline slice did not search the web or retrieve papers, organizer rules, public code, or external data. It cannot support claims about MathorCup/CUMCM rules, awards, rank, or general performance. Before a real contest, a human must identify the exact edition/track and verify its official rules, AI-use disclosure, corrections, and submission requirements from organizer sources.

## Problem contract

- Q1: use weeks 1–8, observed demand in units/week, to forecast week 9 for A/B/C. Compare a last-observation baseline with a per-station OLS linear trend using rolling one-step origins; train only on earlier weeks.
- Q2: choose integer deliveries `x_i` for week 9. Minimize `sum_i(c_i*x_i + p_i*max(f_i-x_i,0))`, with `0 <= x_i <= cap_i` and `sum x_i <= stock`. `f_i` is the computed forecast; CNY/unit costs and penalties come from raw input.
- Q3: deliver this method, executable code, result, sourced figure, paper-style interpretation, source audit, and a receiving record.

## Reusable handoff

| Step / trigger | Input and owner | Operation and output | Receiving check / failure route |
| --- | --- | --- | --- |
| Freeze case | Coordinator: original request, problem and attachments | Record IDs, units, question dependencies, permissions and output directory | Reject if required source/attachment is missing or task is real-contest submission without rule review; ask human for missing consequential facts |
| Audit data | Data analyst: raw files unchanged | Validate schema, types, units, missingness, duplicates, ranges, time order and decision-time availability; write audit | Recompute counts/ranges from raw input; stop on malformed or ambiguous units, retain raw data |
| Abstract | Modeler: accepted audit + each question | Define target, features available at forecast time, variables, assumptions, objective/constraints and metric | Check equations against question; distinguish prediction, optimization and causal claims |
| Forecast | Forecast owner: accepted time series | Fit simple baseline and justified candidate; chronological rolling-origin validation; emit forecasts, per-origin predictions and errors | Recompute split boundaries and metrics; reject future leakage, hardcoded outputs or unsupported superiority |
| Allocate | Solver: forecasts + costs/caps/stock | Solve integer constrained objective; emit allocations, slacks and objective components | Check bounds/integrality, stock, independently recompute objective; use exact enumeration or valid bound on small instances; reject solver failure/infeasibility |
| Explain | Paper/figure owner: received numeric result | Plot sourced observations/forecasts with units; explain outcomes and limits | Trace each displayed number to result and input; inspect rendered figure; do not convert self-check into independent acceptance |
| Smoke and deliver | Coordinator: actual code + raw and malformed input | Run production CLI on raw file and malformed variant; retain commands/status/stdout; deliver workflow, code, results, plot, paper and verification | Valid run must produce numeric result; malformed required field must reject; inspect receipts and artifacts; preserve failures and cumulative repair budget |

One person may perform multiple roles in this small case; role labels do not imply independent review. For an independent acceptance claim, use a fresh reviewer with original requirements and raw input. No independent reviewer was used here.

## Executable method and stop rules

From repository root, run:

```powershell
python -X utf8 runs/R14/trials/math/L6/solve.py runs/R14/cases/math/problem.json --out runs/R14/trials/math/L6
```

The program audits input, performs rolling-origin prediction checks and OLS week-9 forecasts, solves the piecewise linear allocation with SciPy MILP, and compares it with exhaustive enumeration of all feasible integer allocations for this bounded instance. A nonnumeric cost is rejected by the same CLI with exit code 2. Do not coerce malformed fields or silently replace missing values. If required raw inputs or solver capabilities are absent, record the blocker and stop. The current case used 2/2 failure-driven corrections; any further source/orchestration/fallback correction requires a new authorized case/version and cannot erase this record.

## Evidence gates

- **Smoke:** valid raw problem passes from CLI to `results.json` and figure; verify forecast metrics, allocation feasibility and objective. Malformed cost must be rejected by that CLI. Evidence: command receipts in this directory.
- **Acceptance:** check each original assertion against input and actual artifacts; separately check figure labels/legend and paper traceability. Current producer smoke is not independent acceptance. The final chart-legibility receiving check remains incomplete because its forecast legend correction was not applied after the repair budget was reached.
- **Stop:** stop on malformed critical inputs, infeasibility, numerical mismatch, unavailable requirements, or exhausted 2-round repair budget; preserve exact failed commands and distinguish unresolved checks from passes.
