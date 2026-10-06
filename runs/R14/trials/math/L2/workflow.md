# Frozen workflow — Math Level 2 offline slice

## Scope and inputs

Input is `runs/R14/cases/math/problem.json` (weeks 1–8 demand for A/B/C; units/week, week 9 decision); outputs are this trial's `results.json`, `demand_allocation.png`, and this paper. This is a self-created practice case, not contest work. The frozen method uses per-station OLS linear trend extrapolated one week and an expanding-origin evaluation over weeks 4–8. It allocates integer units to minimize the supplied delivery plus unmet-forecast penalty objective under caps and total stock. Forecast targets remain fractional; allocation is integral.

## Roles, handoffs, and gates

| Step / trigger | Input and owner | Operation and output | Receiving check / failure route |
|---|---|---|---|
| Freeze / start | Coordinator; request, problem, C9 lock and Forge documents | Preserve input identity, output boundary, requested model versus unknown actual telemetry, and correction counters | Check required assertions m1–m5 and locked material hashes; stop on mismatch |
| Audit / frozen input | Data role | Check station/week schema, nonnegative numeric observations, units, caps, costs and penalties | Solver rejects malformed types/schema; correct source only with explicit documented fix, otherwise stop |
| Forecast / audit passes | Model role | Refit OLS using only observations available at each origin; save week 9 predictions and five chronological holdout errors per station | Compare to last-observation baseline; reject future leakage, absent numeric outputs or inconsistent origin counts |
| Allocate / forecasts received | Optimization role | Enumerate all feasible integer triples, calculate stated objective and retain minimum | Recompute objective and integer/cap/stock constraints; exhaustive enumeration supports global optimum for this small finite case |
| Integrate / numerical outputs received | Coordinator | Build figure and paper only from result JSON | Trace units, values, assumptions, constraints and limitations across artifacts |
| Smoke / integrated command ready | Producer self-check | Run solver from raw input; then submit malformed cost through same CLI and require nonzero exit | A successful solver exit and local assertions are producer evidence only; preserve rejection receipt and errors |
| Delivery / smoke complete | Coordinator | Deliver reproducible artifacts and handoff | Independent acceptance is pending and must recompute from raw input; do not treat self-check as acceptance |

## Reproduction

From repository root (Python 3.12, numpy/matplotlib installed):

`python -X utf8 runs/R14/trials/math/L2/solver.py`

For alternate inputs, pass `--input path`; default result and figure paths are in this directory. The same entrypoint validates malformed inputs before fitting/optimization.

## Stop and acceptance

Stop if input schema or numeric types fail, any constraint is infeasible, the exact search or independent objective recomputation disagrees, a required artifact is missing, or the two correction rounds are exhausted. Acceptance requires a fresh reviewer to verify frozen source hashes, reproduce predictions and chronological errors without future observations, check the complete finite feasible allocation domain/objective and confirm the paper/plot values against results. This run's producer self-check does not establish independent acceptance.
