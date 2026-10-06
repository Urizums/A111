# Verification record — L6

## Input and source checks

- Read the frozen case request, `problem.json`, C9 lock and the locked Forge skill/reference documents. The C9 lock reports its two author/orchestration corrections as already used; this trial did not edit C9 or spend its budget.
- The supplied raw data have 8 rows, 3 stations, weeks 1–8, 0 missing cells and 0 duplicate weeks. Demand ranges: A 20–27, B 15–20, C 23–30 units/week. Raw data were not imputed or altered for fitting.
- Forecast validation targets weeks 4–8; each fit uses only previous weeks. Pooled errors are MAE/RMSE 0.818/1.051 for OLS trend and 1.333/1.461 for last observation, based on 15 station-origin forecasts.

## Gate observations

| Requirement | Check performed | Outcome / limitation |
| --- | --- | --- |
| m1 workflow and actual deliverables | This operating workflow states inputs, roles, outputs, handoffs, checks, failure paths, smoke and stop conditions | Produced; no independent usability review |
| m2 forecasts from history and no-future validation | Executed solver on original `problem.json`; rolling-origin logic in `solve.py`; results retain each prediction | Producer self-check passes for this bounded input; no independent source/code audit |
| m3 integer allocation and optimality evidence | MILP status optimal; x=(28,2,30), total 60; caps respected; recomputed objective 264.928571; exhaustive enumeration of 24,076 feasible allocations agrees | Producer self-check passes for this instance; no separate acceptor |
| m4 traceability and truthful limits | Paper values copied from `results.json`; plot generated from same raw data/results; paper discloses no external research and no general claims | Figure opened. Forecast marker meanings were not in legend; visual receiving check incomplete. Paper is not a competition submission |
| m5 source, smoke, malformed rejection, budget | Valid and malformed CLI commands retained in `smoke-*-command-final.json`; malformed cost returns rejected/exit 2. One implementation defect was corrected. A second plot-label correction command was attempted from the wrong working directory and made no change | Budget 2/2 reached; stop further correction/rerun. That failed command is preserved in `result.json`; command receipts capture the production smoke executions |

## Acceptance status

Producer smoke is evidence of execution, not independent acceptance. No fresh reviewer checked the requirements. Valid CLI receipt is exit 0; malformed CLI receipt is exit 2 with `cost for A must be finite numeric`. The first attempted valid run failed on an undefined `cost` name and was fixed by using the defined cost mapping; this failure remains counted. The legend correction attempt failed because it ran from the repository parent directory rather than the `work/A111` checkout, so no source write occurred. The repair budget is exhausted at 2/2; do not recast the missing chart check as a pass.
