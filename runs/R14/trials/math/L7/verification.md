# Verification record

| Requirement | Evidence/check | Outcome and limit |
|---|---|---|
| m1 workflow/useful handoff | `workflow.md` defines question contracts, data checks, role ownership, handoffs, receiving checks, failure routes and stop conditions | Producer-authored workflow; usable bounded offline practice method |
| m2 predictions/no-future validation | `results.json`; main command record(s); expanding-origin weeks 4–8 with pooled errors and selected linear trend | Each fold uses only earlier observations; forecast values computed from source. No week-9 actual exists |
| m3 integer allocation/optimality | `results.json` contains plan, constraints, recomputed objective and separable marginal-value certificate | 60 integer units, caps satisfied, CNY 270; exact optimum conditional on rounded forecasts/input coefficients |
| m4 figure/paper traceability | `demand_forecast.png` opened and visually inspected after legend fix; `paper.md` values cross-check against `results.json` | Figure is legible and identifies week-9 forecast crosses; tiny synthetic task cannot support broad claims |
| m5 main smoke and malformed rejection | `main-smoke.json`, `main-rerun-01.json`, `main-rerun-02.json`; `malformed-smoke.json` and `malformed-rerun-02.json` | Main entry point completed. Malformed string cost was rejected, exit 1, and names `delivery_cost_per_unit`; second repair intended to improve message did not apply, so traceback remains. No malformed result was emitted |

## Cross-checks performed by producer

- Source and outputs were read directly; output audit reports 8 ordered weeks, 0 missing cells and 0 duplicate week IDs.
- Forecast folds include weeks 4–8, 3 stations each (15 forecast comparisons per method). Week-9 estimates are computed from all eight source weeks.
- Allocation is nonnegative integer; A=28≤30, B=1≤25, C=31≤35, sum=60≤60.
- Objective was recomputed from input coefficients and rounded forecast demands: 56+121+93=270 CNY.
- Marginal gains are C=7, A=6, B=5 CNY/unit through demand; 80 positive units compete for 60 slots. The selected set is top-ranked; tie at the cutoff still attains the same optimum.
- The actual PNG was visually checked after the first repair: observed series and forecast X markers are distinguishable and units are labeled.
- The malformed-cost variant sets A cost to `two CNY`; the production script exits nonzero and refuses numerical solving. Recovery condition: restore a finite nonnegative numeric cost in the source schema and rerun.

This is self-checking by one producer context, not independent acceptance. C9's author diagnostics or other cases were not used. No claim of an independent checker, verified week-9 accuracy, award likelihood, contest-rule compliance, or general Level superiority is made. A fresh acceptor should recompute the objective and inspect the actual script/result against the frozen problem before operational reuse.

## Attempts and budget

- Failure 1: visual review found forecast crosses had no legend entry. Correction 1 added the legend and the figure was regenerated and inspected.
- Failure 2: a proposed CLI error-message correction did not apply; the malformed rerun still showed a traceback. Correction budget is now exhausted at 2/2. The boundary is nevertheless rejected with a nonzero code and the offending field named. Stop this case here; do not substitute another implementation or actor.
