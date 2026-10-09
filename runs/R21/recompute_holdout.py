"""Root's Decimal cross-check, executable only after the independent g5 lock."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'runs/R21'

def read(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))

def rows(rel):
    with (ROOT / rel).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def key(r):
    return tuple(r[c] for c in ['service_date', 'store_id', 'item_id'])

for rel in ['runs/R21/input-lock.json', 'runs/R21/evaluation-lock.json',
            'runs/R21/execution-lock.json', 'runs/R21/review/initial-lock.json',
            'runs/R21/review/holdout-lock.json']:
    for entry in read(rel)['files']:
        b = (ROOT / entry['path']).read_bytes()
        assert (len(b), hashlib.sha256(b).hexdigest()) == (entry['size_bytes'], entry['sha256'])

truth_rows = rows('runs/R21/evaluation/holdout_truth.csv')
truth = {key(r): D(r['demand_units']) for r in truth_rows}
assert len(truth) == len(truth_rows) == 4032
assert all(v.is_finite() and v >= 0 and v == v.to_integral_value() for v in truth.values())
items = {r['item_id']: r for r in rows('runs/R21/inputs/raw/items.csv')}
calendar = {r['service_date']: r for r in rows('runs/R21/inputs/raw/calendar.csv')}
decision = read('runs/R21/inputs/raw/decision.json')
output = []
daily = {}
for route in ['shared_ridge10', 'weekly_mean56']:
    prefix = 'runs/R21/execution/science-v1/future/' + route + '/'
    predictions = rows(prefix + 'predictions.csv')
    plans = rows(prefix + 'replenishment.csv')
    pmap, qmap = {key(r): r for r in predictions}, {key(r): r for r in plans}
    assert len(pmap) == len(predictions) == len(qmap) == len(plans) == 4032
    assert set(pmap) == set(qmap) == set(truth)
    groups, resources = defaultdict(list), defaultdict(lambda: [D(0), D(0)])
    for k, y in truth.items():
        p, qr, item = pmap[k], qmap[k], items[k[2]]
        assert p['method_id'] == qr['method_id'] == route
        point, lo, hi, q = [D(v) for v in [p['demand_point_units'], p['lower90_units'], p['upper90_units'], qr['q_units']]]
        assert all(v.is_finite() for v in [point, lo, hi, q])
        assert D(0) <= lo <= point <= hi and D(p['interval_level']) == D('.9')
        assert q == q.to_integral_value() and D(0) <= q <= D(item['daily_max_units'])
        error, width = point-y, hi-lo
        shortage = D(item['shortage_yuan']) * max(y-q, D(0))
        waste = D(item['waste_yuan']) * max(q-y, D(0))
        procurement = q * D(item['procurement_yuan'])
        score = width + D(20) * (max(lo-y, D(0)) + max(y-hi, D(0)))
        horizon = (date.fromisoformat(k[0])-date.fromisoformat(decision['future_begin'])).days+1
        assert 1 <= horizon <= 42
        band = f'{((horizon-1)//7)*7+1}-{((horizon-1)//7+1)*7}'
        activity = calendar[k[0]]['holiday']
        metrics = dict(error=error, abs_error=abs(error), squared_error=error*error,
                       covered=D(lo <= y <= hi), below=D(y < lo), above=D(y > hi),
                       width=width, interval_score=score, shortage=shortage, waste=waste,
                       loss=shortage+waste, procurement=procurement, q=q)
        for dimension, group in [('overall','all'), ('date',k[0]), ('activity',activity),
                                 ('horizon_band',band), ('activity_horizon',activity+'|'+band),
                                 ('store',k[1]), ('item',k[2])]:
            groups[(dimension,group)].append((k[0],metrics))
        resources[k[0]][0] += q
        resources[k[0]][1] += procurement
    assert len(resources) == 42
    assert all(q <= D(decision['capacity_units_per_day']) and cost <= D(decision['procurement_budget_yuan_per_day']) for q,cost in resources.values())
    for (dimension,group), values in sorted(groups.items()):
        n = D(len(values))
        sums = {metric: sum((v[1][metric] for v in values),D(0)) for metric in values[0][1]}
        result = dict(route=route, dimension=dimension, group=group, keys=len(values),
                      dates=len({v[0] for v in values}),
                      mean={m:str(v/n) for m,v in sums.items()},
                      rmse=str((sums['squared_error']/n).sqrt()), total={m:str(v) for m,v in sums.items()})
        output.append(result)
        if dimension == 'date':
            daily[(route,group)] = sums
differences = [dict(date=ds, loss_W_minus_R=str(daily[('weekly_mean56',ds)]['loss']-daily[('shared_ridge10',ds)]['loss']),
                    interval_score_W_minus_R=str(daily[('weekly_mean56',ds)]['interval_score']-daily[('shared_ridge10',ds)]['interval_score']))
               for ds in sorted(resources)]
destination = BASE / 'final/root-decimal-holdout.json'
destination.parent.mkdir(exist_ok=True)
with destination.open('x',encoding='utf-8') as f:
    json.dump(dict(schema='r21-post-independent-decimal-check/1', groups=output, daily_differences=differences,
                   scope='Root post-reception check; exact declared CSV decimals, descriptive only. Not independent acceptance or tuning.'), f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps(dict(routes=2, groups=len(output), dates=42, future_keys_per_route=4032, resources_valid=True)))
