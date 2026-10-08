"""Design evidence only: audit every raw row; never train or publish production results."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path('runs/R20')
RAW = BASE / 'inputs/raw'
OUT = BASE / 'design/evidence/audit.json'

def load(name):
    with (RAW / name).open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def latest(rows, origin, key, clock, revision=None):
    groups = defaultdict(list)
    for r in rows:
        if r[clock] <= origin:
            groups[tuple(r[k] for k in key)].append(r)
    # For this audit only. Conflicting same revision is separately surfaced.
    return {k: max(v, key=lambda r: (int(r[revision]) if revision else r[clock], r[clock]))
            for k, v in groups.items()}

def main():
    locks = {}
    for name in ['runs/R20/input-lock.json', 'runs/R19/final/candidate/C12-lock.json']:
        lock = json.loads(Path(name).read_text(encoding='utf-8'))
        checks = []
        for entry in lock['files']:
            p = Path(entry['path'])
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            checks.append({'path': entry['path'], 'bytes_match': p.stat().st_size == entry['size_bytes'],
                           'hash_match': digest == entry['sha256'], 'actual_sha256': digest})
        locks[name] = checks
    data = {}
    summaries = {}
    for p in sorted(RAW.glob('*.csv')):
        cols, rows = load(p.name)
        data[p.name] = rows
        summaries[p.name] = {'headers': cols, 'rows': len(rows),
                            'exact_duplicate_rows': len(rows) - len(set(tuple(r[c] for c in cols) for r in rows)),
                            'empty_by_field': {c: sum(r[c] == '' for r in rows) for c in cols},
                            'dates': [min(r['service_date'] for r in rows), max(r['service_date'] for r in rows)]
                                     if 'service_date' in cols else None}
    decision = json.loads((RAW / 'decision.json').read_text(encoding='utf-8'))
    origin = decision['origin']
    demand = data['demand_reports.csv']
    keys = ['service_date', 'store_id', 'item_id']
    unique = {tuple(r.items()): r for r in demand}.values()
    by_rev = defaultdict(set)
    by_key = defaultdict(list)
    for r in unique:
        k = tuple(r[c] for c in keys)
        by_rev[k + (r['revision'],)].add((r['available_at'], r['demand_units'], r['settlement_yuan']))
        by_key[k].append(r)
    visible = latest(unique, origin, keys, 'available_at', 'revision')
    all_final = latest(unique, '9999', keys, 'available_at', 'revision')
    changed = [k for k in visible if visible[k]['demand_units'] != all_final[k]['demand_units']]
    after = [r for r in demand if r['available_at'] > origin]
    train_dates = Counter(k[0] for k in visible)
    demand_values = [int(r['demand_units']) for r in unique]
    promo = data['promotions.csv']
    promo_visible = latest(promo, origin, keys, 'announced_at')
    future_promo = [r for r in promo if decision['future_begin'] <= r['service_date'] <= decision['future_end']]
    weather = data['weather.csv']
    fw = [r for r in weather if decision['future_begin'] <= r['service_date'] <= decision['future_end']]
    future_forecasts = [r for r in fw if r['kind'] == 'forecast' and r['available_at'] <= origin]
    records = {
        'lock_checks': locks, 'tables': summaries, 'decision': decision,
        'demand': {'unique_keys': len(by_key), 'visible_latest_keys': len(visible),
                   'revision_counts': dict(Counter(r['revision'] for r in unique)),
                   'same_key_revision_conflicts': sum(len(v) > 1 for v in by_rev.values()),
                   'after_origin_rows': len(after), 'after_origin_examples': after[:4],
                   'visible_vs_later_latest_changed_labels': len(changed),
                   'changed_examples': [{'key': k, 'visible': visible[k], 'later': all_final[k]} for k in changed[:4]],
                   'visible_date_key_counts': dict(sorted(train_dates.items())),
                   'demand_range': [min(demand_values), max(demand_values)],
                   'negative_values': sum(v < 0 for v in demand_values)},
        'promotions': {'visible_latest_keys': len(promo_visible), 'future_rows': len(future_promo),
                       'future_after_origin_rows': sum(r['announced_at'] > origin for r in future_promo),
                       'future_after_origin_examples': [r for r in future_promo if r['announced_at'] > origin][:4],
                       'future_visible_keys': sum(decision['future_begin'] <= k[0] <= decision['future_end'] for k in promo_visible)},
        'weather': {'kind_counts': dict(Counter(r['kind'] for r in weather)),
                    'future_forecast_available_rows': len(future_forecasts),
                    'future_forecast_issue_times': sorted(set(r['available_at'] for r in future_forecasts)),
                    'future_observed_rows': sum(r['kind'] == 'observed' for r in fw),
                    'future_forecast_blank_rain': sum(r['rain_mm'] == '' for r in future_forecasts)},
        'calendar': {'holiday_counts': dict(Counter(r['holiday'] for r in data['calendar.csv'])),
                     'weekday_mismatch': sum(datetime.fromisoformat(r['service_date']).weekday() != int(r['weekday_monday_zero']) for r in data['calendar.csv'])},
        'scope': 'All raw rows parsed; source identity and availability audit, not forecasting acceptance.'}
    assert all(c['hash_match'] and c['bytes_match'] for v in locks.values() for c in v)
    assert records['demand']['same_key_revision_conflicts'] == 0
    assert records['calendar']['weekday_mismatch'] == 0
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(records, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
