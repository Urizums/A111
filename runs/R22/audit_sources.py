"""Inspect available 42-day historical evidence; no fitting or future truth."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runs/R22/audit'
TZ = timezone(timedelta(hours=8))

def read_csv(rel):
    with (ROOT / rel).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def at(text):
    t = datetime.fromisoformat(text)
    return t.replace(tzinfo=TZ) if t.tzinfo is None else t

def k(r):
    return tuple(r[n] for n in ['service_date', 'store_id', 'item_id'])

for rel in ['runs/R21/input-lock.json', 'runs/R21/execution-lock.json']:
    for entry in json.loads((ROOT / rel).read_text(encoding='utf-8'))['files']:
        b = (ROOT / entry['path']).read_bytes()
        assert (len(b), hashlib.sha256(b).hexdigest()) == (entry['size_bytes'], entry['sha256'])

raw = 'runs/R21/inputs/raw/'
reports = read_csv(raw+'demand_reports.csv')
unique = {tuple(sorted(r.items())): r for r in reports}
reports = list(unique.values())
by_key = defaultdict(list)
for r in reports:
    by_key[k(r)].append(r)
assert len(by_key) == 17664
for versions in by_key.values():
    assert len({r['revision'] for r in versions}) == len(versions)

def visible(cutoff, exclude_date=None):
    result = {}
    for key, versions in by_key.items():
        eligible = [r for r in versions if at(r['available_at']) <= cutoff and
                    (exclude_date is None or r['service_date'] < exclude_date)]
        if eligible:
            result[key] = max(eligible, key=lambda r: int(r['revision']))
    return result

mature = visible(at('2026-11-04T18:00:00'))
assert len(mature) == 17664
calendar = {r['service_date']: r for r in read_csv(raw+'calendar.csv')}
promotions = read_csv(raw+'promotions.csv')
weather = read_csv(raw+'weather.csv')
stores = [r['store_id'] for r in read_csv(raw+'stores.csv')]
items = [r['item_id'] for r in read_csv(raw+'items.csv')]
residuals = read_csv('runs/R21/execution/science-v1/uncertainty/residual_coordinates_all.csv')
windows = []
for origin_day in ['2026-07-22', '2026-09-02', '2026-09-19']:
    origin = at(origin_day+'T18:00:00')
    train = visible(origin, origin_day)
    targets = [(date.fromisoformat(origin_day)+timedelta(days=i)).isoformat() for i in range(1,43)]
    keys = {(d,s,i) for d in targets for s in stores for i in items}
    assert len(keys) == 4032 and keys <= set(mature)
    training_days = Counter(key[0] for key in train)
    assert all(count == 96 for count in training_days.values())
    eligible_days = {}
    for route in ['shared_ridge10', 'weekly_mean56']:
        grouped = defaultdict(list)
        for r in residuals:
            if r['method_id'] == route and at(r['source_origin']) < origin:
                grouped[r['service_date']].append(r)
        ready = []
        for day, rr in grouped.items():
            assert len(rr) == len({k(r) for r in rr}) == 96
            if all(at(mature[k(r)]['available_at']) <= origin and
                   r['revision'] == mature[k(r)]['revision'] and
                   at(r['available_at']) == at(mature[k(r)]['available_at']) for r in rr):
                ready.append(day)
        eligible_days[route] = sorted(ready)
    assert eligible_days['shared_ridge10'] == eligible_days['weekly_mean56']
    cells = []
    for band in range(6):
        ds = targets[band*7:(band+1)*7]
        for activity in ['0','1']:
            dates = [d for d in ds if calendar[d]['holiday'] == activity]
            cells.append(dict(horizon_band=f'{band*7+1}-{band*7+7}', activity=activity,
                              dates=len(dates), keys=len(dates)*96, observed=bool(dates)))
    known_promo = {k(r) for r in promotions if k(r) in keys and at(r['announced_at']) <= origin}
    known_weather = {(r['service_date'],r['zone_id']) for r in weather if
                     r['service_date'] in targets and r['kind'] == 'forecast' and at(r['available_at']) <= origin}
    windows.append(dict(origin=origin.isoformat(), target_begin=targets[0], target_end=targets[-1],
                        dates=42, keys=4032, train_keys=len(train), train_days=len(training_days),
                        mature_label_keys=len(keys & set(mature)),
                        mature_versions_not_yet_available_at_origin=sum(at(mature[key]['available_at'])>origin for key in keys),
                        residual_days=len(eligible_days['shared_ridge10']), residual_day_ids=eligible_days['shared_ridge10'],
                        known_target_promotion_keys=len(known_promo), known_target_weather_region_dates=len(known_weather),
                        activity_dates=sum(calendar[d]['holiday']=='1' for d in targets), cells=cells))
overlap=[]
for a in range(3):
    for b in range(a+1,3):
        begin=max(windows[a]['target_begin'],windows[b]['target_begin'])
        end=min(windows[a]['target_end'],windows[b]['target_end'])
        days=max((date.fromisoformat(end)-date.fromisoformat(begin)).days+1,0)
        overlap.append(dict(origins=[windows[a]['origin'],windows[b]['origin']], shared_dates=days))
outside_targets = [(date(2026,9,20)+timedelta(days=i)).isoformat() for i in range(1,43)]
outside_keys = {(d,s,i) for d in outside_targets for s in stores for i in items}
unavailable = outside_keys-set(mature)
assert len(unavailable) == 96 and {key[0] for key in unavailable} == {'2026-11-01'}
OUT.mkdir(parents=True,exist_ok=True)
with (OUT/'source-availability.json').open('x',encoding='utf-8') as f:
    json.dump(dict(schema='r22-horizon-evidence-audit/1', windows=windows, overlap=overlap,
                   boundary_control=dict(origin='2026-09-20T18:00:00+08:00', missing_historical_keys=96,
                                         missing_date='2026-11-01', complete_window_rejected=True),
                   source='R21 historical raw only; no future truth, fitting or loss-based window selection',
                   limits='Available historical labels do not prove 42-step performance; sparse activity cells and overlapping dates must remain explicit.',
                   model=None,tokens=None,cost=None),f,ensure_ascii=False,indent=2)
    f.write('\n')
print(json.dumps(dict(windows=3, target_keys_per_window=4032, fitting=False, future_truth_read=False,
                      residual_days=[w['residual_days'] for w in windows], overlap=overlap)))
