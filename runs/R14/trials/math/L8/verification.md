# Verification and handoff record

## Source and execution evidence

The original request and common problem were read from the paths in the request. The C9 lock was read and its supplied skill/reference hashes were checked against the lock: all eight listed skill/reference entries matched. The lock reports C9 historical `repairs_used=2` of `repair_limit=2`, with `candidate_source_repairs=0` and `author_orchestration_corrections=2`. These are candidate-author history counters, not this L8 case's correction count.

Original main-path and boundary outputs were observed in the working session but were not retained as complete command receipts at the time. The new retained records are `reproduction/command.json` and `boundary-check/command.json`, made with the supplied `scripts/record_command.py`; they record the invocations performed for this handoff. The main reproduction finished with exit code 0. The malformed variant changed A's cost to the supplied string `"two CNY"`; the program rejected it with exit code 2 and a finite-numeric-value error, before writing result output in the boundary-check output directory. The earlier unrecorded outputs are not represented as original receipts.

## Requirement-to-evidence map

| Requirement | Evidence and performed check | Status / limit |
|---|---|---|
| m1: usable workflow, inputs, decisions, owners, handoffs, smoke, acceptance/stop and deliverables | `workflow.md` names the raw problem, Q1/Q2 chain, roles, interfaces, checks, failures, stop rules and open independent review. Main raw-to-result run and malformed boundary run have command records. | Workflow and bounded smoke delivered. Independent acceptance is not performed. |
| m2: history-derived prediction, no-future validation, baseline or justified method, code and numeric output | `solve.py` fits full observed history for week 9; origins 4–8 fit only earlier rows. `results.json` includes per-origin values and MAEs; `reproduction/command.json` records successful execution. | Producer-level source/command check only. Five origins are too few for a robust accuracy claim. |
| m3: integer allocation, raw stock/caps/nonnegative constraints, recomputable objective and suitable optimality evidence | `results.json` contains integer A=28/B=2/C=30, stock/cap checks, objective terms and exhaustive enumeration count 24,076. Solver code enumerates feasible allocations and recomputes the objective. | Exact enumeration supports optimality for this stated instance/objective. No independent recomputation by another actor. |
| m4: figure/paper trace computed values/units; no invented awards/rules/verified uncertainty/superiority | `forecast_allocation.png` and `paper.md` use the result values, label demand units/week, allocation units and objective CNY, identify the supplied input, and bound claims to this practice case. | Plot was opened and visually inspected at original resolution: axes/legend/title are readable; the two panels show history/forecasts and demand/allocation. This visual check establishes appearance only, not numerical correctness. |
| m5: actual source check/main smoke and malformed rejection retained; self-check separate from independent acceptance; preserve failures/budget | Lock hash comparison, executable main reproduction and malformed rejection records are retained. Current case history has no failure-driven correction. | Main original session receipt was unavailable; later rerun receipt is preserved distinctly. No independent acceptance. Candidate-history author budget was already 2/2 before this case. |

## State and limits

Artifacts are produced and producer-checked, not independently accepted. No failure-driven correction was needed in this case; case budget is 0/2. The malformed input rejection is an expected boundary check, not a failed attempt. No other failed attempt is recorded. Candidate C9's author-history budget remains 2/2 as reported by its lock and was not reset or altered. Requested model label was `gpt-6-luna`, but authenticated model identity, tokens and cost are unknown. This one small offline case supports no award, ranking, causal-level comparison, or general superiority claim.

## Next receiver action

An independent receiver should use the original request and problem, run the documented command, inspect `results.json` and recompute at least the chronological forecast errors, integer feasibility, and objective. Reject if future rows enter an origin's fit, if any allocation violates a cap/stock/integrality condition, or if the recomputed objective differs. The current producer's checks do not substitute for that review.
