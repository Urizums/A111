"""One-day baseline/feasible plan to exercise interfaces, not the original full solution."""
import csv
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median
from audit_raw import load, latest

OUT = Path('runs/R20/design/evidence')

def reject_bad_plan(rows, items, cap=1600, budget=6000):
    assert len({(r['service_date'], r['store_id'], r['item_id']) for r in rows}) == len(rows), 'duplicate key'
    money = Decimal(0)
    for r in rows:
        q = r['q_units']
        assert isinstance(q, int) and not isinstance(q, bool), 'non-integer or nonfinite quantity'
        assert 0 <= q <= int(items[r['item_id']]['daily_max_units']), 'quantity bound'
        money += Decimal(items[r['item_id']]['procurement_yuan']) * q
    assert sum(r['q_units'] for r in rows) <= cap, 'capacity'
    assert money <= Decimal(budget), 'budget'
    return int(sum(r['q_units'] for r in rows)), str(money)

def main():
    _, raw = load('demand_reports.csv')
    _, item_rows = load('items.csv')
    _, stores = load('stores.csv')
    _, calendar = load('calendar.csv')
    _, weather = load('weather.csv')
    _, promotions = load('promotions.csv')
    items = {r['item_id']: r for r in item_rows}
    origin = '2026-09-30T18:00:00'
    target = date(2026, 10, 1)
    visible = latest(raw, origin, ['service_date','store_id','item_id'], 'available_at', 'revision')
    histories = defaultdict(list)
    for (day, store, item), r in visible.items():
        parsed = date.fromisoformat(day)
        if target - timedelta(days=56) <= parsed < target and parsed.weekday() == target.weekday():
            histories[(store, item)].append((day, int(r['demand_units']), r['available_at'], r['revision']))
    predictions = []
    for store in stores:
        for item in item_rows:
            key = store['store_id'], item['item_id']
            values = histories[key]
            assert values, 'empty baseline history'
            predictions.append({'service_date': target.isoformat(), 'store_id': key[0], 'item_id': key[1],
                                'demand_point_units': median(v[1] for v in values),
                                'q_units': 0, 'history_rows': len(values),
                                'last_label_available_at': max(v[2] for v in values)})
    # Greedy positive marginal improvement per procurement yuan; feasible heuristic, no optimum claim.
    while True:
        units, money = reject_bad_plan(predictions, items)
        options = []
        for ix, r in enumerate(predictions):
            p = items[r['item_id']]
            q, d = r['q_units'], Decimal(str(r['demand_point_units']))
            c = Decimal(p['procurement_yuan'])
            if q >= int(p['daily_max_units']) or units + 1 > 1600 or Decimal(money) + c > 6000:
                continue
            a, b = Decimal(p['shortage_yuan']), Decimal(p['waste_yuan'])
            loss = lambda v: a * max(d-v,0) + b * max(v-d,0)
            gain = loss(q) - loss(q+1)
            if gain > 0:
                options.append((gain/c, gain, -ix, ix))
        if not options:
            break
        predictions[max(options)[-1]]['q_units'] += 1
    units, money = reject_bad_plan(predictions, items)
    keys = {(r['service_date'],r['store_id'],r['item_id']) for r in predictions}
    assert len(keys) == 96
    assert all(math.isfinite(r['demand_point_units']) and r['demand_point_units'] >= 0 for r in predictions)
    total_loss = sum(Decimal(items[r['item_id']]['shortage_yuan']) * max(Decimal(str(r['demand_point_units']))-r['q_units'],0)
                     + Decimal(items[r['item_id']]['waste_yuan']) * max(r['q_units']-Decimal(str(r['demand_point_units'])),0)
                     for r in predictions)
    with (OUT/'smoke-one-day.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(predictions[0])); writer.writeheader(); writer.writerows(predictions)
    reloaded=list(csv.DictReader((OUT/'smoke-one-day.csv').open(encoding='utf-8')))
    assert len(reloaded)==96
    failures=[]
    for name, value in [('negative',-1),('fraction',0.5),('nan',float('nan')),('cap',56)]:
        bad=[dict(r) for r in predictions]; bad[0]['q_units']=value
        try:
            reject_bad_plan(bad,items)
        except AssertionError as exc:
            failures.append({'case':name,'rejected':True,'reason':str(exc)})
        else:
            raise AssertionError('malformed plan falsely accepted')
    for name in ['capacity','budget']:
        bad=[dict(r) for r in predictions]
        for r in bad:
            r['q_units']=55 if name=='capacity' or r['item_id'] in ['K03','K07'] else 0
        try:
            reject_bad_plan(bad,items)
        except AssertionError as exc:
            failures.append({'case':name,'rejected':True,'reason':str(exc),
                             'total_units':sum(r['q_units'] for r in bad),
                             'procurement_yuan':str(sum(Decimal(items[r['item_id']]['procurement_yuan'])*r['q_units'] for r in bad))})
        else:
            raise AssertionError('resource violation falsely accepted')
    assert len([r for r in raw if r['service_date']=='2026-09-30' and r['available_at'] > origin])==96
    assert not any(k[0]=='2026-09-30' for k in visible)
    histories_audit=[]
    for day in ['2026-07-31','2026-08-14','2026-08-28','2026-09-11','2026-09-16']:
        t=day+'T18:00:00'; d0=date.fromisoformat(day)
        horizon={(d0+timedelta(days=h)).isoformat() for h in range(1,15)}
        forecasts=[r for r in weather if r['service_date'] in horizon and r['kind']=='forecast' and r['available_at']<=t]
        known_promo=[r for r in promotions if r['service_date'] in horizon and r['announced_at']<=t]
        train=latest(raw,t,['service_date','store_id','item_id'],'available_at','revision')
        all_latest=latest(raw,'9999',['service_date','store_id','item_id'],'available_at','revision')
        histories_audit.append({'origin':t,'weather_forecast_days':sorted(set(r['service_date'] for r in forecasts)),
                                'known_promotion_keys':len(known_promo),'expected_horizon_keys':1344,
                                'train_latest_labels_changed_later':sum(train[k]['demand_units']!=all_latest[k]['demand_units'] for k in train)})
    receipt={'scope':'One future date, simple point baseline; no model selection, interval calibration, held-out loss, optimality or full paper.',
             'origin':origin,'date':target.isoformat(),'rows':96,'total_q_units':units,'procurement_yuan':money,
             'capacity_slack_units':1600-units,'budget_slack_yuan':str(Decimal(6000)-Decimal(money)),
             'loss_at_point_baseline_yuan':str(total_loss),'loss_excludes_procurement':True,
             'bad_plan_receiving_checks':failures,
             'late_report_boundary':{'rejected_2026_09_30_rows':96,'included_2026_09_30_labels':0},
             'historical_availability':histories_audit,
             'calendar_holiday_dates':[r['service_date'] for r in calendar if r['holiday']=='1'],
             'training_holiday_keys':sum(k[0] in {r['service_date'] for r in calendar if r['holiday']=='1'} for k in visible),
             'weather_features_used':False,'promo_features_used':False,'independent_acceptance':False}
    (OUT/'smoke-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
