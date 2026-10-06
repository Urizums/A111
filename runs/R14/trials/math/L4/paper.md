# Eight-week community-station demand and allocation exercise

## Abstract

This offline practice exercise forecasts week-9 demand for three stations from eight weekly observations and allocates at most 60 units to minimize stated delivery cost plus the penalty for unmet predicted demand. A station-wise linear trend gives forecasts A=28.000, B=20.357, C=30.679 units/week. In five rolling-origin one-step folds, the trend MAE is 0.818 units/week versus 1.333 for the last-observation baseline. Because this comparison has only five origins, it is descriptive. Exhaustive enumeration of 24,076 feasible integer plans yields A=28, B=2, C=30 and objective 264.929 CNY. The result depends on the provided penalty rates and local trend assumption and is not a real contest result.

## Problem and method

The supplied data contain weeks 1–8 for stations A, B and C in units/week. Each series is complete, numeric and chronologically ordered. No actual week-9 demand is available. For each station, ordinary least squares estimates demand as a linear function of week, and the fitted line is extrapolated one week, with negative predictions floored at zero. This simple model reflects the short, generally increasing histories; it assumes equally spaced weeks and locally linear continuation.

To assess predictions without future leakage, each validation fit uses only weeks before the target and predicts targets 4 through 8. The same 15 station-origin errors are used for the last-observation baseline. MAE is the average absolute error in units/week. Trend MAE is 0.818 and baseline MAE is 1.333. The small number of origins, and the fact that station-fold errors share weeks, prevent a strong generalization claim.

For integer delivery `x_i`, forecast `d_i`, unit delivery cost `c_i`, and unmet-demand penalty `p_i`, minimize `Σ_i(c_i x_i + p_i max(d_i−x_i,0))`. Constraints are integer `0 ≤ x_i ≤ cap_i` and total delivery no greater than 60. This is a cost-minimization objective in CNY; available stock is an upper bound. We enumerate every feasible allocation in the cap-bounded domain and evaluate the stated piecewise objective directly, which establishes the minimum for this finite instance if the input and implementation are correct.

## Results and interpretation

The selected allocation uses all 60 units: 28 to A, 2 to B and 30 to C. Its recomputed cost is 56.000 CNY delivery to A, 2.000 delivery plus 110.143 unmet-demand penalty at B, and 90.000 delivery plus 6.786 unmet-demand penalty at C, totaling 264.929 CNY. Predicted unmet demand is 0 at A, 18.357 at B and 0.679 at C. Although C has the largest per-unit penalty, its 31st unit's marginal avoided penalty is only about 6.786 CNY under the fractional forecast, less than B's second unit's 6 CNY? (B's second unit reduces its unmet penalty by 6 CNY and costs 1 CNY, for a 5 CNY objective improvement; C's 31st unit improves by about 3.786 CNY net.) Thus the plan's B/C split follows the supplied objective, not an operational fairness rule.

The result is sensitive to the forecast and user-supplied penalties. No penalty sensitivity analysis or actual demand comparison was performed. The sample does not support a causal, population-wide or competition-performance conclusion. It does not establish contest rules, awards or a submission-ready analysis.

## Reproducibility

Run from the repository root: `python -X utf8 runs/R14/trials/math/L4/solve.py --input runs/R14/cases/math/problem.json --out runs/R14/trials/math/L4`. Computed values are in `results.json`; the plotted observed values, forecasts and chosen deliveries are in `forecast_allocation.png`. The command and malformed-cost rejection are retained under `receipts/`.
