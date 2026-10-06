# Verification record

Input and source checks are producer-run checks; independent acceptance is pending.

| Gate | Evidence | Observation | Claim boundary |
|---|---|---|---|
| Frozen materials | `receipt-material-check.json` | All eight files listed in `runs/R14/candidate/C9-lock.json` match recorded byte sizes and SHA-256 hashes | Establishes the locked Forge package files were intact; does not independently endorse their content |
| Input audit | `solver.py` validation; successful default smoke | Eight rows have week plus A/B/C nonnegative numeric demand; distribution maps cover A/B/C; capacities are nonnegative integers | Only this supplied practice input |
| Source check | `receipt-source-check.json` | Python 3.12 byte-compilation completed successfully | Syntax check, not semantic acceptance |
| Main smoke | `receipt-smoke.json` | Default production CLI read the raw problem, wrote `results.json` and `demand_allocation.png`, reported A=28/B=2/C=30 and 264.928571 CNY | Producer self-check of one end-to-end case |
| Malformed rejection | `receipt-malformed.json` | Same CLI exited nonzero with `ValueError: delivery_cost_per_unit.A must be a nonnegative number`; no success outputs for this invocation | Correct rejection of the provided malformed-cost boundary |
| Numerical recomputation | `receipt-verification.json` | Forecasts match fresh recomputation; a separate exhaustive loop finds same allocation/objective; integrality/capacity/stock checks pass | Same producer context and inputs; not independent acceptance |
| Plot inspection | Actual rendered PNG inspected | Axes show week/demand units and allocated units; plot says supplied weeks 1–8 and distinguishes observations, forecasts and allocations | Visual inspection supports legibility and provenance labels only |

No corrective changes were made after an observed failure. The malformed case was an expected rejection test. A separate independent evaluator is still required before claiming acceptance.
