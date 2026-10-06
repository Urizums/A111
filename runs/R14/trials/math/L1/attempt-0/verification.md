# Verification and handoff

## Source and run checks performed

- Read the requested Level 1 request, common problem JSON, C9 lock, supplied Forge skill and its applicable modeling, workflow-design, source-evaluation, evaluation, frontend, continuation, and collaboration references.
- The request asks for one bounded offline real slice with numerical method, executable work, outputs, plot, paper, source checks and handoff. The C9 lock reports its repair limit already used by prior author/orchestration corrections; no corrective iteration was attempted here. This run used the initial construction and had zero new corrective attempts.
- `python -X utf8 runs/R14/trials/math/L1/solver.py` completed. It emitted week 9 predictions A=28, B=20.357143, C=30.678571; allocation A=28, B=2, C=30; objective 264.928571 CNY; and rolling-origin/naive MAEs recorded in `results.json`.
- The solver validates chronological weeks and finite nonnegative numeric demands and numeric nonnegative cost/penalty/cap inputs. The supplied malformed-cost boundary with A=`"two CNY"` is rejected; it is not silently converted or solved.
- Solver assertions check integer/nonnegative/cap constraints, stock, and objective recomputation. The finite feasible allocation space is exhaustively enumerated, so the minimum is exact under the supplied objective and constraints.
- The forecast check uses six expanding rolling origins (weeks 3–8), each fit only on earlier observations. Its MAE exceeds the last-value baseline at all stations in this sample.
- A PNG figure was rendered by the solver from observed and computed values. The paper reports units, values, method, source, and limits.

## Requirement evidence and status

| Requirement | Evidence | Status / limit |
|---|---|---|
| m1 usable workflow and actual slice | `workflow.md`, `solver.py`, this verification, outputs | Produced and self-checked; no independent acceptor |
| m2 forecasts from history, no-future validation, baseline, executable outputs | `solver.py`, `results.json` | Executed; six origins are descriptive and small |
| m3 integer allocation, stock/caps, recomputable objective, optimality evidence | `solver.py`, `results.json` | Feasible and objective recomputed; exact enumeration for this finite instance |
| m4 figure/paper trace values and units; restrained claims | `demand_forecast.png`, `paper.md` | Produced and internally traceable; no contest superiority claim |
| m5 source/main smoke and malformed rejection; distinct acceptance | run command and rejection/assertions above | Smoke/self-check performed; independent acceptance not performed |

## Handoff

Next user can rerun the command above. Before reuse, inspect new raw source and units, confirm decision-time availability, reassess whether linear trend is sensible, and rerun the chronological evaluation and allocation checks. For a real contest, independently inspect current official materials and human responsibilities. No network lookup was performed because this is explicitly offline practice.

Correction ledger: cumulative used **2/2** for the locked candidate scope (C9 lock records two prior author/orchestration corrections); this run added **0**. No fallback or corrective retry occurred. Model telemetry, authenticated model, tokens, and cost are unknown/null; the requested label is not provider telemetry. No independent acceptance or generalized quality conclusion is claimed.
