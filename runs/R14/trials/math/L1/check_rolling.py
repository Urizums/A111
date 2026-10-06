import json
from pathlib import Path
import numpy as np
base = Path(__file__).resolve().parents[5]
raw = json.loads((base/'runs/R14/cases/math/problem.json').read_text(encoding='utf-8'))
reported = json.loads((Path(__file__).resolve().parent/'results.json').read_text(encoding='utf-8'))
targets = list(range(3,9))
errs = {s: [] for s in 'ABC'}
naive = {s: [] for s in 'ABC'}
for t in targets:
    train = [row for row in raw['data'] if row['week'] < t]
    assert len(train) == t-1 and train[-1]['week'] == t-1
    x = np.array([row['week'] for row in train], dtype=float)
    for s in 'ABC':
        y = np.array([row[s] for row in train], dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        forecast = slope*t + intercept
        actual = raw['data'][t-1][s]
        errs[s].append(abs(forecast-actual))
        naive[s].append(abs(train[-1][s]-actual))
mae = {s: float(np.mean(errs[s])) for s in 'ABC'}
naive_mae = {s: float(np.mean(naive[s])) for s in 'ABC'}
assert reported['validation']['targets'] == targets
for s in 'ABC':
    assert np.isclose(mae[s], reported['validation']['linear_trend_mae_units_per_week'][s])
    assert np.isclose(naive_mae[s], reported['validation']['naive_last_value_mae_units_per_week'][s])
print(json.dumps({'targets':targets,'for_each_target_fit_weeks':'1 through target-1','linear_trend_mae':mae,'naive_mae':naive_mae,'reported_values_match':True},ensure_ascii=False))
