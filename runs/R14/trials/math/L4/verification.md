# Verification record

## Source and data audit

- Read the frozen request, original problem, C9 lock and all eight files named by the lock under `candidate/C9/forge-agent-flow/`. The lock's declared hashes were checked against the named flow files; the skill hash matches `b83a327e1a8813b7972dffac47541b7e168eb5e7e8b7dfe3bb9ef9b836a7a4e8`. The source files were not modified.
- Original problem identity: SHA-256 `e6bac9fd20c5609f55757e39546b7d3e28865dd6af333086e8930b6cf0b36f39`. The input has eight unique increasing weeks and three complete nonnegative numeric station series, in the supplied units. No imputation, correction, or future week was introduced.
- Scope: the supplied exercise is self-created offline practice, not a real contest prompt. No external rules or research were consulted.

## Per-requirement checks

| Requirement | Evidence and observed check | State and limit |
| --- | --- | --- |
| m1 usable workflow | `workflow.md` supplies source/interface, owners, handoffs, receiving assertions, failure routes, stop budget and deliverables | Self-checked; no independent acceptance |
| m2 forecasts and validation | `results.json` has week-9 predictions, 5 rolling origins (15 station-fold rows), trend MAE 0.818095 and last-value MAE 1.333333 units/week; main command produced these from the raw file | No future rows exist; validation is a tiny descriptive backtest, not proof of predictive superiority |
| m3 integer allocation and optimum | Allocation is A=28, B=2, C=30, total=60; respects caps 30/25/35; objective terms sum to 264.928571 CNY. The code exhaustively evaluated all 24,076 feasible triples in the cap domain | Finite exhaustive optimum conditional on the specified inputs/code; penalty appropriateness is unverified |
| m4 figure/paper trace | Figure uses week-8 source values, week-9 fitted values and selected allocation from the same solver run; opened and visually inspected. `paper.md` values agree with `results.json` within displayed rounding | Render inspected at one size; no actual week-9 outcome or empirical external result |
| m5 source/main/malformed and truthful status | Source audit and `receipts/main-smoke.json` exit 0; controlled malformed cost produced `ValueError: delivery_cost_per_unit[A] must be finite and nonnegative numeric`, retained in `receipts/malformed-smoke.json` with exit 1 | Malformed-input path is a successful rejection. It does not establish independent acceptance or broader parser coverage |

## Gate status

Preflight: performed for the specified local materials and Python 3.12 environment. Main smoke: performed end-to-end from the raw problem JSON through numerical results and figure; numerical/constraint evidence is directly inspectable in outputs. Boundary smoke: malformed currency text was rejected before producing the requested solve output. Delivery consistency: paper and figure were checked against computed results, and the actual figure was viewed. Producer self-check is complete. Independent acceptance was not performed because no separate acceptor was available; the findings remain self-checked rather than independently accepted.

## Failure and correction ledger

No solver, workflow, or artifact correction was required; cumulative failure-driven corrections used: 0 of the original limit 2. The malformed-cost command exits nonzero by design and is the expected rejection observation, not a corrective failure. No additional candidates, actors or retries were used. If a later independent checker finds a mandatory defect, record the exact evidence and count a correction against the same two-round budget; at exhaustion stop this case without replacing its inputs or verdict.

## Unknowns

Authenticated model identity: unknown/null; `gpt-6-luna` is only the requested model label. Token use, cost and provider timing: unknown/null. Independent acceptance: unavailable. Current MathorCup big-data rules, contest eligibility, allowed AI use, awards, rank and general competition performance: not evaluated. No uncertainty interval, residual inferential model, sensitivity study, or week-9 observed validation is available in this bounded slice.
