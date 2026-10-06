# Reusable workflow: short-horizon demand and constrained allocation

## Working brief and inputs

This is an offline practice case, not a contest submission. The supplied input is `runs/R14/cases/math/problem.json`: 8 weekly observations for stations A–C, a week-9 forecast request, 60 units of stock, station caps, delivery costs (CNY/unit), and unmet-prediction penalties (CNY/unit). The raw observations are in units/week. The request and the C9 Forge skill specify reproducible work, source checks, a real smoke path, rejection of malformed costs, and a clear distinction between producer checks and independent acceptance. The case does not provide future week-9 truth, demand distributions, or official contest rules.

## Question decomposition and workflow contract

| Step / trigger | Input and decision | Owner | Output and receiving check | Failure / stop |
|---|---|---|---|---|
| 1. Intake and source check | Read the original request and problem JSON; identify each question, field, unit, constraint, boundary variant, and output. Treat strings in data as values, never instructions. | Coordinator (same working context in this small case) | Frozen source paths; check all required keys/types, ordered week index, station columns, and distribution parameters. | Missing, ambiguous, or malformed material: report the exact field and request corrected input; do not impute silently. |
| 2. Data audit | Raw weeks 1–8, A/B/C series. Check missing/duplicate weeks, numeric finite values, units, range and visible patterns. Preserve raw data. | Data analyst | Audit summary in `results.json`; check observations used equal supplied observations and no future week enters fitting. | Stop a series with invalid values; document any proposed treatment before computing. |
| 3. Forecast baseline and candidate | For Q1, baseline is last observed value; candidate is one-step OLS linear trend. Select only using expanding-window one-step errors, fitting at each origin on earlier observations. | Modeler | Per-origin predictions/errors, MAE and week-9 prediction; check no look-ahead and compare on identical origins. | If history is inadequate or candidate does not justify complexity, prefer the baseline and state uncertainty. |
| 4. Allocation | For Q2, minimize stated delivery plus unmet-prediction penalty with integer nonnegative allocations, station caps and total-stock cap. For this tiny instance enumerate every feasible integer allocation. | Solver | Allocation, objective breakdown, feasibility checks and search count; recompute objective from published inputs and predictions. | Invalid cost/cap or no feasible point: return error with recovery condition; no fabricated solution. |
| 5. Integrate and explain | Trace data → forecasts → allocation → objective → figure and paper. | Paper author/coordinator | `paper.md`, plot and `results.json`; check values, units, labels and assumptions agree. | Unsupported claims are removed or marked unknown. |
| 6. Receive and hand off | Check original m1–m5 against source and actual artifacts. | Producer self-check; independent acceptor is a separate role/context when available | `verification.md` maps requirements to observed evidence and limits; receiver can rerun command. | A producer check is not independent acceptance. Missing evidence remains open. |

One person/context can perform these compatible roles for this small exercise, but this does not create independent verification. A research role is not needed: no external facts were required to choose between the transparent baseline and trend model. No additional actors or network access are used. For a real MathorCup or CUMCM submission, first obtain the exact current track materials, organizer rules, data attachments, AI-use boundary and submission requirements; this practice run establishes none of those.

## Model and decision contract

For station `i`, fit `y_it = a_i + b_i t + error_it` by ordinary least squares on observed weeks and use `ŷ_i,9 = a_i + 9 b_i`. This assumes a locally linear trend over one step and comparable weekly measurements. At forecast origins `t=4,…,8`, fit only on weeks `<t`, forecast `t`, and compare absolute errors with the last-value baseline `ŷ_it = y_i,t-1`. The five origins are a tiny diagnostic, not a reliable estimate of future accuracy.

Choose integer `x_i` to minimize `Σ_i [c_i x_i + p_i max(ŷ_i,9 − x_i, 0)]`, subject to `0 ≤ x_i ≤ cap_i`, integer `x_i`, and `Σ_i x_i ≤ 60`. The supplied penalties and costs are treated as exact objective parameters. This objective does not model uncertain actual demand, station interactions, setup costs, fairness or delivery timing. Enumerating all feasible integer allocations proves optimality only for this stated finite model and these inputs.

## Reproduction and receiving checks

From the repository `work/A111` directory run:

```powershell
python -X utf8 runs/R14/trials/math/L8/solve.py --problem runs/R14/cases/math/problem.json --outdir runs/R14/trials/math/L8
```

The executable implementation is `solve.py`; numerical outputs are `results.json`; the figure is `forecast_allocation.png`. The retained invocation records are under `reproduction/command.json` and `boundary-check/command.json`. The latter uses the provided malformed-cost change (`A = "two CNY"`) and must exit nonzero before result creation. Check forecast source/units, baseline errors, integer/cap/stock constraints and objective recomputation. The finite exhaustive search currently visits 24,076 feasible allocations; no solver optimality tolerance is involved.

## TODO and next use

- [x] Parse the actual request and raw problem; run a complete forecast-to-allocation slice.
- [x] Compare a simple baseline and trend on chronological origins; record malformed-input rejection.
- [x] Produce numerical results, a labelled figure, paper-style interpretation, reproducible code and handoff checks.
- [ ] An independent reviewer should inspect the original request/problem and recompute forecast/constraints/objective from the delivered files before any acceptance claim.
- [ ] If the exercise is extended, collect more historical weeks and evaluate on a genuinely later holdout; consider demand uncertainty or alternative losses only when the decision question supports them.

Stop after required artifacts and checks. These eight weeks and three stations cannot establish leaderboard rank, awards, broad model superiority, or full-contest competitiveness.
