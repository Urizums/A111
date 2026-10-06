# Verification and handoff — corrective attempt 1

## Original state and preserved failure

All six original deliverables were copied unchanged into `attempt-0/` before editing. Their original `result.json` and `verification.md` retain the prior budget wording. The initial solver run had completed successfully; the defect below was discovered during a later review of its validation code.

The earlier candidate-lock hash check had no durable command receipt. The submitted inline command attempted to load `runs/R14/candidate/C9-lock.json` and compare each listed SHA-256. The tool returned a Python `SyntaxError` on line 1 (`closing parenthesis ')' does not match opening parenthesis '['`); the returned diagnostic was truncated by the tool. It was not retried. This failed check does not establish whether the locked hashes match.

## Corrective change and checks

The first execution incorrectly hardcoded week 9 inside `forecasts(data)`. Rolling-origin validation called it with weeks 1 through target−1 but therefore predicted week 9 for every fold, then compared that value with actual weeks 3–8. That invalidated the reported backtest MAEs.

`forecasts(data, target_week)` now predicts the explicit target. The final fit requests week 9; each validation fold requests its actual target week. The solver was executed through the repository's existing command recorder:

- `attempt-1-main.json`: `python -X utf8 runs/R14/trials/math/L1/solver.py` completed with exit code 0. It reports week 9 forecasts A=28, B=20.357143, C=30.678571 and unchanged allocation A=28, B=2, C=30, objective 264.928571 CNY.
- `check_rolling.py` independently loads the raw problem and result, builds each training set by `week < target`, forecasts that explicit target, recomputes both MAE series, and checks them against `results.json`. Its recorded run `attempt-1-check.json` completed with exit code 0. It verified target weeks 3–8 and the updated values: trend MAE A≈0, B=1.414286, C=1.630952 units/week; last-value MAE A=1, B=1.333333, C=1.666667.
- The malformed input is written as `malformed-cost-input.json` and passed to the same production `load_and_validate` function used for the real input. That entry point rejects A's string cost `"two CNY"`; no optimization is run on the malformed input.
- The main run also rechecks allocation integrality, nonnegativity, station caps, total stock and objective recomputation; exhaustive enumeration still establishes the exact minimum for the stated instance and objective.

The paper MAE table and interpretation were updated. The week 9 figure and allocation objective did not change. No independent acceptance was performed; this is producer-side correction and checking only.

## Requirement status and handoff

| Requirement | Evidence | Status / limit |
|---|---|---|
| m1 workflow and real bounded slice | `workflow.md`, code, outputs | Produced; independent acceptance absent |
| m2 forecasts, no-future validation, baseline and executable outputs | `solver.py`, `results.json`, `check_rolling.py`, receipts | Corrected target-specific folds and independently recomputed; six origins only |
| m3 integer allocation, constraints, objective and optimality | `solver.py`, `results.json`, main receipt | Feasible; objective recomputed; exhaustive finite enumeration |
| m4 traceable plot/paper and restrained conclusions | `demand_forecast.png`, `paper.md` | Values/units trace to computed result; no contest outcome claims |
| m5 actual source/main smoke and malformed rejection | main/check receipts; malformed path through `load_and_validate` | Performed; no independent acceptor |

From the workspace root rerun with `python -X utf8 runs/R14/trials/math/L1/solver.py`. Before reusing the workflow, inspect each new raw source, units and decision-time availability. The six observations per station cannot establish general forecast performance; no week 9 actuals or current contest rules were checked.

Budget accounting is split by domain: candidate-author/orchestration corrections remain **2/2** per the C9 lock; this case began at **0/2** and now has **1/2** corrective attempt. The earlier failed hash-check command/diagnostic remains documented above and was not rerun. No second corrective attempt has been used. Requested model label: `gpt-6-luna`; authenticated model, tokens and cost remain unknown/null.
