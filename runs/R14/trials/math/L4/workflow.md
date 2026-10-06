# Offline demand forecasting and integer allocation workflow

## Frozen brief and source check

This is a self-created offline practice case, not a live MathorCup problem or submission. The request targets MathorCup big-data preparation, but this case contains only eight observations at three stations. Input identities (SHA-256): `request.json` `8fe5ca72224784f28f53855c43704171cacbeb34b8d5327d15c248bd619bad61`; `problem.json` `e6bac9fd20c5609f55757e39546b7d3e28865dd6af333086e8930b6cf0b36f39`; `C9-lock.json` `239cf5fde33dafca7926ce669055024b0c81c55f6200342630f7427b64be81b4`. All eight files named by that lock were SHA-256 checked against their declarations. The skill and references were read as the method source. Their instructions were applied as follows: map outputs back to requirements, freeze the bounded evidence gates, preserve actual failures and correction count, and distinguish producer self-check from independent acceptance. No outside sources or network were used.

The lock records two earlier author orchestration corrections and zero source repairs for its prior scope. Those historical counts concern another domain and do not provide repair credit here. This new case uses its own original maximum of two failure-driven correction rounds; none were needed or consumed.

### Questions and interface

| Question | Input and units | Output / decision | Receiving check |
| --- | --- | --- | --- |
| Q1 forecast | Weeks 1–8, station demand in units/week | Three real-valued week-9 forecasts | Recompute from raw history; rolling-origin folds use past rows only; compare MAE to last-observation baseline |
| Q2 allocate | Forecasts, station caps, 60 available units; CNY/unit costs and unmet-demand penalties | Integer `x_i` by station | Check integer/nonnegative/caps/total; independently recompute objective; exhaustive bounded enumeration verifies minimum |
| Q3 deliver | Frozen JSON and this workflow | Solver, results, plot, paper and checks | Reproduce with recorded command; plot inspected visually; malformed cost rejected |

The observations are ordered, complete and numeric, with shared units as stated in the raw problem. No missing values or duplicates occur in the eight supplied weeks. These are the complete available data; no external provenance or real demand population is supplied. Station order is A, B, C. No data repair or future demand is used. Forecasting is descriptive prediction, not causal analysis.

## Executable blueprint and ownership

One operator may perform every role on this small slice; role labels do not create independent checks. The coordinator owns the frozen brief and integration. A data/model producer audits the JSON and computes forecasts; a solver computes the allocation; a paper producer uses only accepted `results.json`; a receiving checker recomputes the material assertions from source and outputs. In this run the same context authored and self-checked the artifacts, so independent acceptance is unavailable.

| Step / trigger | Raw inputs | Decision or operation | Owner | Output and next consumer | Receiving check | Failure / stop |
| --- | --- | --- | --- | --- | --- | --- |
| Preflight | Frozen request, problem, lock and C9 Forge files | Check source identities, field types, units, chronological order, resource boundary | Coordinator/data | Audited problem passed to model | Exact source hash; complete and numeric columns; no silent coercion | Stop numerical solve on malformed values; preserve error and request corrected source |
| Forecast | Valid rows 1–8 | Fit station-wise OLS against week number; extrapolate one step, floor at zero | Model producer | Week-9 forecast in units/week | Recompute; no future data; compare against rolling-origin and last-value baseline | If trend unsuitable or validation worse, report comparison and prefer baseline/qualify forecast |
| Validate prediction | Raw history only | Refit on weeks 1…t−1, predict t for t=4…8 | Receiving checker | Fold-level predictions/errors | Check target rows excluded; calculate MAE on identical origins/stations | Preserve folds; small sample limits claims |
| Allocate | Forecast, caps, total, costs and penalties | Minimize `Σ(c_i x_i + p_i max(d_i−x_i,0))` over bounded integer triples | Solver producer | Week-9 integer plan and objective in CNY | Recompute each term, all constraints, enumerate every feasible tuple | Stop if infeasible, objective mismatch or no optimality evidence |
| Plot and paper | Accepted results and raw source | Trace units/provenance and discuss limits | Paper producer | PNG and short paper | Verify plotted inputs match JSON and inspect actual rendered image | Correct the asset before delivery; no claims from appearance alone |
| Smoke / delivery | Real input plus controlled malformed variant | Run main entry end-to-end and malformed rejection | Operator/checker | Receipts, verification and result manifest | Exit status and numerical assertions; error explains rejection | Retain failures; maximum two cumulative failure-driven corrections, then stop |

The executable is `solve.py`; reproduce from the repository root with `python -X utf8 runs/R14/trials/math/L4/solve.py --input runs/R14/cases/math/problem.json --out runs/R14/trials/math/L4`. Outputs are overwritten by this deterministic offline run. It uses NumPy for least squares and Matplotlib for the figure; the allocation oracle uses Python enumeration, not an unverified optimizer status.

## Modeling choices

For station `i`, observed demand is `y_it` and integer week index is `t`. Fit `y_it = α_i + β_i t + ε_it` by ordinary least squares on all eight observations, then set `d_i,9 = max(0, α̂_i + 9 β̂_i)`. This one-step trend is interpretable and parsimonious for the smooth short histories. Its local linearity and equally spaced weeks are assumptions, not established facts. The feasible baseline is the previous observed demand. On identical rolling-origin forecasts for targets 4–8, evaluate mean absolute error in units/week. Only five forecast origins (15 station-origin errors) exist; even if trend MAE is lower, that is descriptive and not a reliable general superiority claim.

Choose integer deliveries `x_i` to minimize

`J(x) = Σ_i [ c_i x_i + p_i max(d_i,9 − x_i, 0) ]`

subject to `x_i ∈ Z`, `0 ≤ x_i ≤ cap_i`, and `Σ_i x_i ≤ 60`. The 60-unit bound may be left unused because it is an upper bound, not an equality. `c_i` and `p_i` are CNY/unit. Forecast demand may be fractional; deliveries remain integers. The code enumerates all triples within station caps, retains those under total stock, evaluates the original piecewise objective directly, and takes the minimum. This is a complete finite optimality certificate for this small domain, contingent on the code/input/objective being as specified. It does not validate the supplied penalty rates as operationally correct.

## Gates and handoff

The Q1 gate is the actual prediction plus no-look-ahead folds and a same-origin baseline. The Q2 gate is feasibility plus objective recomputation and complete enumeration. The Q3 gate requires the executable reproduction, actual chart visual inspection, paper-to-result trace, source audit and malformed-input rejection. The producer's checks establish only self-checked status. A fresh independent acceptor would need the original problem/request, `solve.py`, raw results, receipts and figure, and should recompute all folds and objective, inspect every feasibility condition and reject any silent malformed input. No such actor ran here; independent acceptance remains open.

Handoff: read `verification.md`, then `results.json` and `paper.md`; rerun the command above for reproduction. `result.json` is the machine-readable state and limits record. This workflow only demonstrates one bounded synthetic practice slice. It establishes no current contest rules, eligibility, award probability or competition-level performance.
