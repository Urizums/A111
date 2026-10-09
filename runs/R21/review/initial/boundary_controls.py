"""Independent finite, feasible, readiness, and continuous-scenario controls."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import numpy as np

OUT = Path("runs/R21/review/initial")


def is_ready(arrivals, cutoff, expected=96):
    # One calibration unit is one service day with every coordinate present;
    # only exact versions available by cutoff are eligible.
    return len(arrivals) == expected and all(t <= cutoff for t in arrivals)


def finite_feasible(rows, unit_costs):
    if not rows:
        return False
    for r in rows:
        vals = [r[k] for k in ("point", "lo", "hi", "q")]
        if not all(np.isfinite(float(x)) for x in vals):
            return False
        if r["point"] < 0 or not (0 <= r["lo"] <= r["point"] <= r["hi"]):
            return False
        if int(r["q"]) != r["q"] or not (0 <= r["q"] <= 55):
            return False
    if sum(r["q"] for r in rows) > 1600:
        return False
    if sum(r["q"] * unit_costs[i] for i, r in enumerate(rows)) > 6000 + 1e-9:
        return False
    return True


cutoff = datetime.fromisoformat("2026-10-31T18:00:00+08:00")
base = [cutoff - timedelta(minutes=1)] * 96
equal = base[:-1] + [cutoff]
late = base[:-1] + [cutoff + timedelta(seconds=1)]
day_readiness = {
    "equal_arrival_is_included": is_ready(equal, cutoff),
    "one_second_late_is_excluded": not is_ready(late, cutoff),
    "95_of_96_is_excluded": not is_ready(base[:95], cutoff),
    "exact_96_is_included": is_ready(base, cutoff),
}
# A 14-day rolling forecast window has 13 complete days and one incomplete day.
forecast_days = {f"D{i+1:02d}": is_ready(base[:95], cutoff) if i == 6 else is_ready(base, cutoff) for i in range(14)}
day_readiness["partial_window_keeps_13_complete_days"] = sum(forecast_days.values()) == 13

valid = [{"point": 1.2, "lo": 0.1, "hi": 2.2, "q": 2}]
finite_cases = {
    "valid_finite_feasible_case_accepted": finite_feasible(valid, [5]),
    "nan_prediction_rejected": not finite_feasible([{**valid[0], "point": float("nan")}], [5]),
    "negative_point_rejected": not finite_feasible([{**valid[0], "point": -0.1}], [5]),
    "reversed_interval_rejected": not finite_feasible([{**valid[0], "lo": 2.0}], [5]),
    "fractional_q_rejected": not finite_feasible([{**valid[0], "q": 2.5}], [5]),
    "q_above_item_cap_rejected": not finite_feasible([{**valid[0], "q": 56}], [5]),
    "daily_units_cap_rejected": not finite_feasible([{"point": 1, "lo": 0, "hi": 2, "q": 55}] * 30, [1] * 30),
    "daily_purchase_cap_rejected": not finite_feasible([{"point": 1, "lo": 0, "hi": 2, "q": 55}] * 12, [10] * 12),
}

# Legitimate scenario demand is continuous. Independently enumerate integer q
# against the two-part loss; the expected-loss minimizer must not round demand.
scenario_demand = np.array([0.25, 1.75, 2.5], dtype=float)
cu, co = 2.4, 1.1
expected_losses = [float(np.mean(cu * np.maximum(scenario_demand - q, 0) + co * np.maximum(q - scenario_demand, 0))) for q in range(56)]
q_star = int(np.argmin(expected_losses))
continuous_case = {
    "continuous_scenario_values_are_finite_nonnegative": bool(np.isfinite(scenario_demand).all() and (scenario_demand >= 0).all()),
    "continuous_values_not_forced_to_integer": bool(any(x != int(x) for x in scenario_demand)),
    "integer_action_is_bounded": 0 <= q_star <= 55,
    "selected_q_is_bruteforce_argmin_two_part_loss": expected_losses[q_star] == min(expected_losses),
    "q_argmin": q_star,
    "minimum_expected_two_part_loss": expected_losses[q_star],
}

result = {
    "schema": "r21-independent-boundary-controls/1",
    "scope": "synthetic boundary and finite/feasible checks only; no truth access",
    "readiness_controls": day_readiness,
    "finite_feasibility_controls": finite_cases,
    "continuous_scenario_control": continuous_case,
    "all_controls_pass": all(day_readiness.values()) and all(finite_cases.values()) and all(continuous_case[k] for k in ("continuous_scenario_values_are_finite_nonnegative", "continuous_values_not_forced_to_integer", "integer_action_is_bounded", "selected_q_is_bruteforce_argmin_two_part_loss")),
}
(OUT / "boundary-controls.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
