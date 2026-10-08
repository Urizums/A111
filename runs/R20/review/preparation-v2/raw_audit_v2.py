import csv, json, hashlib
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, date, timezone, timedelta
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / 'runs' / 'R20' / 'inputs' / 'raw'
def read(name):
    with (RAW / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def parse_dt(s, default_tz=timezone(timedelta(hours=8))):
    if not s: return None
    dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
    return dt.replace(tzinfo=default_tz) if dt.tzinfo is None else dt
rows={n:read(n) for n in ['demand_reports.csv','weather.csv','promotions.csv','calendar.csv','items.csv','stores.csv']}
demand=rows['demand_reports.csv']; weather=rows['weather.csv']; promos=rows['promotions.csv']
with (RAW/'decision.json').open(encoding='utf-8-sig') as f: decision=json.load(f)
decision_tz=ZoneInfo(decision['timezone'])
cutoff=parse_dt(decision['origin'], decision_tz)

def key(r): return tuple(r.get(k,'') for k in ('service_date','store_id','item_id'))
def feature_eligible_demand(r, at):
    return bool(r.get('available_at')) and parse_dt(r['available_at']) <= at

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Source identities and counts.
out={'decision_json':decision,'decision_cutoff_used':cutoff.isoformat(),'tables':{},'independent_controls':{}}
with (ROOT/'runs/R20/input-lock.json').open(encoding='utf-8') as f: input_lock=json.load(f)
with (ROOT/'runs/R20/evaluation-lock.json').open(encoding='utf-8') as f: evaluation_lock=json.load(f)
input_lock_checks=[]
for item in input_lock['files']:
    actual=digest(ROOT/item['path'])
    input_lock_checks.append({'path':item['path'],'expected_sha256':item['sha256'],'actual_sha256':actual,'match':actual==item['sha256']})
acceptance_lock_item=next(x for x in evaluation_lock['files'] if x['path']=='runs/R20/evaluation/ACCEPTANCE.md')
acceptance_actual=digest(ROOT/acceptance_lock_item['path'])
out['lock_checks']={'input_files':input_lock_checks,'all_input_hashes_match':all(x['match'] for x in input_lock_checks),'acceptance_path':acceptance_lock_item['path'],'acceptance_expected_sha256':acceptance_lock_item['sha256'],'acceptance_actual_sha256':acceptance_actual,'acceptance_hash_matches':acceptance_actual==acceptance_lock_item['sha256'],'holdout_truth_opened':False}
for name, data in rows.items():
    out['tables'][name]={'rows':len(data),'columns':list(data[0]) if data else [],'sha256':digest(RAW/name)}
# Demand revision and exact duplication controls.
exact=Counter(tuple(sorted(r.items())) for r in demand)
key_revs=defaultdict(set); key_rows=defaultdict(list)
for r in demand:
    key_revs[key(r)].add(r.get('revision',''))
    key_rows[key(r)].append(r)
arrivals=[parse_dt(r['available_at']) for r in demand if r.get('available_at')]
future=[r for r in demand if parse_dt(r.get('available_at','')) and parse_dt(r['available_at']) > cutoff]
late_label=[r for r in future if date.fromisoformat(r['service_date']) < cutoff.date()]
settlement_nonempty=sum(bool(r.get('settlement_yuan','').strip()) for r in demand)
# Find a real same-key earlier available version and later revision, with one on each side of cutoff where possible.
pair=None
control_cutoff=cutoff-timedelta(days=30)
for k, rs in key_rows.items():
    before=sorted((r for r in rs if parse_dt(r.get('available_at','')) and parse_dt(r['available_at'])<=control_cutoff),key=lambda r:(parse_dt(r['available_at']),r.get('revision','')))
    after=sorted((r for r in rs if parse_dt(r.get('available_at','')) and parse_dt(r['available_at'])>control_cutoff),key=lambda r:(parse_dt(r['available_at']),r.get('revision','')))
    if before and after and before[-1].get('revision') != after[0].get('revision'):
        pair={'key':k,'eligible_record':before[-1],'ineligible_record':after[0]}; break
out['demand']={'rows':len(demand),'distinct_keys':len(key_revs),'keys_with_multiple_revisions':sum(len(v)>1 for v in key_revs.values()),'exact_duplicate_excess_rows':sum(n-1 for n in exact.values() if n>1),'available_at_min':min(arrivals).isoformat() if arrivals else None,'available_at_max':max(arrivals).isoformat() if arrivals else None,'records_after_decision_cutoff':len(future),'late_arriving_labels_for_past_service_dates':len(late_label),'nonempty_settlement_values':settlement_nonempty,'legal_illegal_pair':pair}
# Weather timing: same-day forecast/observed availability and actual sample at cutoff.
wtypes=Counter(r.get('record_type') or r.get('kind') or r.get('type') for r in weather)
w_future=[r for r in weather if r.get('available_at') and parse_dt(r['available_at'])>cutoff]
weather_pair=None
cross_zone_control=None
def weather_source_key(r):
    return (r.get('service_date',''), r.get('zone_id',''))
def is_weather_kind(r, expected):
    return (r.get('kind') or '').lower()==expected
for r in weather:
    if is_weather_kind(r,'forecast') and r.get('available_at') and parse_dt(r['available_at'])<=cutoff:
        same_key=[x for x in weather if weather_source_key(x)==weather_source_key(r) and is_weather_kind(x,'observed') and x.get('available_at') and parse_dt(x['available_at'])>cutoff]
        other_zone=[x for x in weather if x.get('service_date')==r.get('service_date') and x.get('zone_id')!=r.get('zone_id') and is_weather_kind(x,'observed') and x.get('available_at') and parse_dt(x['available_at'])>cutoff]
        if same_key and other_zone:
            weather_pair={'forecast':r,'observed_after_cutoff':same_key[0]}
            cross_zone_control={'forecast_key':weather_source_key(r),'same_date_other_zone_key':weather_source_key(other_zone[0]),'same_zone_match':weather_source_key(r)==weather_source_key(same_key[0]),'cross_zone_candidate_rejected':weather_source_key(r)!=weather_source_key(other_zone[0]),'same_zone_observed':same_key[0],'other_zone_observed':other_zone[0]}
            break
out['weather']={'rows':len(weather),'type_counts':dict(wtypes),'records_after_cutoff':len(w_future),'forecast_observed_pair':weather_pair,'cross_zone_control':cross_zone_control}
# Promotions announced by cutoff versus later announcements.
p_future=[r for r in promos if r.get('announced_at') and parse_dt(r['announced_at'])>cutoff]
out['promotions']={'rows':len(promos),'records_announced_after_cutoff':len(p_future),'columns':list(promos[0]) if promos else []}
out['independent_controls']={'historical_pair_cutoff':control_cutoff.isoformat(),'demand_eligible_sample_passes':bool(pair and feature_eligible_demand(pair['eligible_record'],control_cutoff)),'demand_late_sample_rejected':bool(pair and not feature_eligible_demand(pair['ineligible_record'],control_cutoff)),'settlement_field_present_and_forbidden_as_feature':bool(settlement_nonempty and 'settlement_yuan' not in {'demand_units','available_at','revision'}),'weather_forecast_observed_pair_found':bool(weather_pair),'weather_cross_zone_mismatch_rejected':bool(cross_zone_control and cross_zone_control['cross_zone_candidate_rejected']),'decision_origin_read_from_json':decision.get('origin')==cutoff.replace(tzinfo=None).isoformat(),'promotion_late_count':len(p_future),'formal_acceptance_status':'UNVERIFIED; preparation-only; no frozen production workflow/results received'}
print(json.dumps(out,ensure_ascii=False,indent=2))

