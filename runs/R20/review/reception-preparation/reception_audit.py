import csv, json, math, hashlib
from collections import Counter, defaultdict
from datetime import datetime, date, time, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from statistics import median, mean
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[4]
RAW=ROOT/'runs/R20/inputs/raw'
FLOW=ROOT/'runs/R20/design/forge-freshfood-flow'
ALLOWED_DESIGN=['runs/R20/design/HANDOFF.md','runs/R20/design/forge-freshfood-flow/SKILL.md','runs/R20/design/forge-freshfood-flow/references/acceptance.md','runs/R20/design/forge-freshfood-flow/references/contracts.md','runs/R20/design/forge-freshfood-flow/references/paper-delivery.md','runs/R20/design/forge-freshfood-flow/references/research-decisions.md']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def dec(x):
    try: return Decimal(str(x))
    except (InvalidOperation,ValueError,TypeError): return Decimal('NaN')
def parse_dt(s,tz):
    d=datetime.fromisoformat(s.replace('Z','+00:00'))
    return d.replace(tzinfo=tz) if d.tzinfo is None else d.astimezone(tz)
def key(r): return (r.get('service_date',''),r.get('store_id',''),r.get('item_id',''))
def revnum(r):
    n=dec(r.get('revision',''))
    if not n.is_finite() or n!=n.to_integral_value(): raise ValueError('non-integer revision: '+str(r.get('revision')))
    return int(n)
def distinct_payload(rows):
    return {tuple((k,v) for k,v in r.items() if k!='available_at') for r in rows}
def choose_snapshot(rows, origin, tz):
    # Exact re-exports are excluded; key/version resolution is cutoff-specific.
    exact={tuple(sorted(r.items())) for r in rows}
    eligible=[r for r in rows if r.get('available_at') and parse_dt(r['available_at'],tz)<=origin]
    groups=defaultdict(list)
    for r in eligible: groups[key(r)].append(r)
    snap={}; conflicts=[]
    for k,rs in groups.items():
        high=max(revnum(r) for r in rs)
        top=[r for r in rs if revnum(r)==high]
        if len(distinct_payload(top))>1:
            conflicts.append(k); continue
        snap[k]=max(top,key=lambda r:parse_dt(r['available_at'],tz))
    return snap, len(rows)-len(exact), conflicts, len(eligible)

with (ROOT/'runs/R20/inputs/raw/decision.json').open(encoding='utf-8-sig') as f: decision=json.load(f)
tz=ZoneInfo(decision['timezone']); origin=parse_dt(decision['origin'],tz)
inputs={n:read_csv(RAW/n) for n in ['demand_reports.csv','weather.csv','promotions.csv','calendar.csv','items.csv','stores.csv']}
demand=inputs['demand_reports.csv']; weather=inputs['weather.csv']; promos=inputs['promotions.csv']; item_rows=inputs['items.csv']; stores=inputs['stores.csv']
items={r['item_id']:r for r in item_rows}; store_ids={r['store_id'] for r in stores}; item_ids=set(items)

# Verify the complete raw input lock and only the specifically authorized design bytes.
with (ROOT/'runs/R20/input-lock.json').open(encoding='utf-8') as f: ilock=json.load(f)
input_checks=[]
for ent in ilock['files']:
    p=ROOT/ent['path']; actual=sha(p)
    input_checks.append({'path':ent['path'],'expected':ent['sha256'],'actual':actual,'match':actual==ent['sha256']})
with (ROOT/'runs/R20/design-lock.json').open(encoding='utf-8') as f: dlock=json.load(f)
lock_entries={x['path']:x for x in dlock['files']}
design_checks=[]
for rel in ALLOWED_DESIGN:
    ent=lock_entries[rel]; p=ROOT/rel; actual=sha(p)
    design_checks.append({'path':rel,'expected':ent['sha256'],'actual':actual,'match':actual==ent['sha256'],'bytes':p.stat().st_size,'locked_bytes':ent['size_bytes']})

# Source data identity and interval coverage.
unique_keys=Counter(key(r) for r in demand)
revision_counts=defaultdict(set)
for r in demand: revision_counts[key(r)].add(r['revision'])
avail=[parse_dt(r['available_at'],tz) for r in demand if r.get('available_at')]
weather_kinds=Counter(r['kind'] for r in weather)
weather_dates=defaultdict(set)
for r in weather: weather_dates[(r['service_date'],r['zone_id'])].add(r['kind'])
future_dates=[(date.fromisoformat(decision['future_begin'])+timedelta(days=i)).isoformat() for i in range((date.fromisoformat(decision['future_end'])-date.fromisoformat(decision['future_begin'])).days+1)]
expected={(d,s,k) for d in future_dates for s in store_ids for k in item_ids}

# Real latest available revision pair controls at a derived historical origin.
control_origin=origin-timedelta(days=30)
bykey=defaultdict(list)
for r in demand: bykey[key(r)].append(r)
rev_pair=None
for k,rs in bykey.items():
    before=[r for r in rs if parse_dt(r['available_at'],tz)<=control_origin]
    after=[r for r in rs if parse_dt(r['available_at'],tz)>control_origin]
    if before and after and max(revnum(x) for x in after)>max(revnum(x) for x in before):
        snap,_,_,_=choose_snapshot(rs,control_origin,tz)
        if k in snap:
            rev_pair={'key':k,'selected_at_origin':snap[k],'later_revision':min(after,key=lambda x:revnum(x))}
            break
control_snapshot=choose_snapshot(demand,control_origin,tz)[0]
selected_control=control_snapshot.get(rev_pair['key']) if rev_pair else None
late_revision_excluded=bool(rev_pair and selected_control and revnum(selected_control)<revnum(rev_pair['later_revision']))

# Build a deliberately simple weekday-median baseline for independent method/control only.
# Each origin is 14 consecutive dates and each feature snapshot is cutoff-specific.
latest_label_cutoff=max(avail)
final_labels,dup_excess,final_conflicts,_=choose_snapshot(demand,latest_label_cutoff,tz)

def hist_value(r):
    v=dec(r.get('demand_units'))
    if not v.is_finite() or v<0: return None
    return v

def forecast_one(snap, store, item, target_day, cutoff):
    vals=[]
    for (d,s,k),r in snap.items():
        dd=date.fromisoformat(d)
        if s==store and k==item and dd<cutoff.date() and dd.weekday()==target_day.weekday():
            v=hist_value(r)
            if v is not None: vals.append((dd,v))
    vals.sort(reverse=True)
    if vals: return max(Decimal(0),Decimal(str(median([float(v) for _,v in vals[:8]]))))
    # Explicit fallback uses only cutoff-visible 56-day same-series history.
    allvals=[]
    for (d,s,k),r in snap.items():
        dd=date.fromisoformat(d)
        if s==store and k==item and cutoff.date()-timedelta(days=56)<=dd<cutoff.date():
            v=hist_value(r)
            if v is not None: allvals.append(v)
    if allvals: return Decimal(str(median([float(v) for v in allvals])))
    return Decimal(0)

origins=[origin-timedelta(days=n) for n in (120,90,60,30)]
backtests=[]; all_pred=[]
for cut in origins:
    snap,duplicates,conflicts,eligible_n=choose_snapshot(demand,cut,tz)
    targets=[(cut.date()+timedelta(days=i)).isoformat() for i in range(1,15)]
    rows=[]; missing_truth=0
    for d in targets:
        td=date.fromisoformat(d)
        for s in sorted(store_ids):
            for it in sorted(item_ids):
                k=(d,s,it); truthrow=final_labels.get(k)
                if not truthrow or hist_value(truthrow) is None:
                    missing_truth+=1; continue
                y=hist_value(truthrow); pred=forecast_one(snap,s,it,td,cut)
                # Cost/source-value checks are made before the loss aggregation.
                c=dec(items[it]['procurement_yuan']); a=dec(items[it]['shortage_yuan']); b=dec(items[it]['waste_yuan'])
                q=max(0,int(pred.quantize(Decimal('1'),rounding=ROUND_HALF_UP)))
                loss=a*max(y-Decimal(q),Decimal(0))+b*max(Decimal(q)-y,Decimal(0))
                rows.append({'date':d,'store':s,'item':it,'pred':pred,'truth':y,'q':q,'loss':loss,'procurement':c*q})
    if rows:
        errors=[float(x['pred']-x['truth']) for x in rows]
        abs_errors=[abs(e) for e in errors]
        sum_y=sum(float(x['truth']) for x in rows)
        bt={'origin':cut.isoformat(),'target_start':targets[0],'target_end':targets[-1],'input_snapshot_keys':len(snap),'snapshot_rows_eligible':eligible_n,'snapshot_exact_duplicate_excess':duplicates,'snapshot_conflicts':len(conflicts),'evaluated_rows':len(rows),'missing_truth_rows':missing_truth,'mae':mean(abs_errors),'rmse':math.sqrt(mean([e*e for e in errors])),'wape':sum(abs_errors)/sum_y if sum_y else None,'mean_bias_forecast_minus_actual':mean(errors),'naive_round_prediction_history_loss_yuan':str(sum(x['loss'] for x in rows)),'naive_round_prediction_procurement_yuan_unconstrained':str(sum(x['procurement'] for x in rows)),'loss_by_shortage_waste_recomputed_from_raw':True}
        backtests.append(bt); all_pred.extend(rows)

# Validate the future delivery contract and resource/cost source values.
price={it:dec(r['procurement_yuan']) for it,r in items.items()}
shortage={it:dec(r['shortage_yuan']) for it,r in items.items()}
waste={it:dec(r['waste_yuan']) for it,r in items.items()}
maxqty={it:int(dec(r['daily_max_units'])) for it,r in items.items()}
for it in items:
    assert all(v.is_finite() and v>=0 for v in (price[it],shortage[it],waste[it]))
    assert maxqty[it]>=0

def validate_plan(plan):
    issues=[]; seen=Counter(); totals=defaultdict(lambda:[0,Decimal(0)])
    for r in plan:
        k=key(r); seen[k]+=1
        if k not in expected: issues.append('unexpected_key:'+str(k)); continue
        qv=dec(r.get('q_units'))
        if not qv.is_finite(): issues.append('nonfinite_q:'+str(k)); continue
        if qv<0: issues.append('negative_q:'+str(k))
        if qv!=qv.to_integral_value(): issues.append('noninteger_q:'+str(k))
        if qv.is_finite() and qv>=0 and qv==qv.to_integral_value():
            q=int(qv)
            if q>maxqty[k[2]]: issues.append('item_max:'+str(k))
            day=totals[k[0]]; day[0]+=q; day[1]+=price[k[2]]*q
    for k,n in seen.items():
        if n>1: issues.append('duplicate_key:'+str(k))
    missing=expected-set(seen)
    if missing: issues.append('missing_keys:'+str(len(missing)))
    for d,(units,cost) in totals.items():
        if units>int(dec(decision['capacity_units_per_day'])): issues.append('capacity:'+d+':'+str(units))
        if cost>dec(decision['procurement_budget_yuan_per_day']): issues.append('budget:'+d+':'+str(cost))
    return issues

def zero_plan(day): return [{'service_date':d,'store_id':s,'item_id':it,'q_units':0} for d in future_dates for s in sorted(store_ids) for it in sorted(item_ids)]
base_plan=zero_plan(future_dates[0])
controls={'zero_plan_accepted':len(validate_plan(base_plan))==0,'zero_plan_errors':validate_plan(base_plan)}
controls['missing_key_rejected']=any(x.startswith('missing_keys:') for x in validate_plan(base_plan[:-1]))
dup=base_plan+[dict(base_plan[0])]
controls['duplicate_key_rejected']=any(x.startswith('duplicate_key:') for x in validate_plan(dup))
frac=[dict(x) for x in base_plan]; frac[0]['q_units']=Decimal('0.5')
controls['fractional_q_rejected']=any(x.startswith('noninteger_q:') for x in validate_plan(frac))
neg=[dict(x) for x in base_plan]; neg[0]['q_units']=-1
controls['negative_q_rejected']=any(x.startswith('negative_q:') for x in validate_plan(neg))
capbad=[dict(x) for x in base_plan]; capbad[0]['q_units']=maxqty[capbad[0]['item_id']]+1
controls['item_max_rejected']=any(x.startswith('item_max:') for x in validate_plan(capbad))

def fill_day(day, order, target, budget=None):
    plan=[{'service_date':day,'store_id':s,'item_id':it,'q_units':0} for s in sorted(store_ids) for it in sorted(item_ids)]
    ix={(r['store_id'],r['item_id']):r for r in plan}; units=0; cost=Decimal(0)
    for s,it in order:
        r=ix[(s,it)]; room=maxqty[it]; c=price[it]
        while room and units<target and (budget is None or cost<=budget):
            r['q_units']+=1; room-=1; units+=1; cost+=c
            if budget is not None and cost>budget: break
        if units>=target or (budget is not None and cost>budget): break
    return plan,units,cost

day=future_dates[0]
low_order=sorted(((s,it) for s in store_ids for it in item_ids),key=lambda z:(price[z[1]],z))
capplan,capunits,capcost=fill_day(day,low_order,int(decision['capacity_units_per_day'])+1)
cap_all=zero_plan(future_dates[1:]) if False else []
# Validator expects full horizon; replace first day rows with the targeted daily plan.
capall=[r for r in base_plan if r['service_date']!=day]+capplan
controls['capacity_control_generated']=(capunits>int(decision['capacity_units_per_day']) and capcost<=dec(decision['procurement_budget_yuan_per_day']))
controls['capacity_excess_rejected']=controls['capacity_control_generated'] and any(x.startswith('capacity:') for x in validate_plan(capall))
high_order=sorted(((s,it) for s in store_ids for it in item_ids),key=lambda z:(-price[z[1]],z))
budgetplan,bunits,bcost=fill_day(day,high_order,1600,dec(decision['procurement_budget_yuan_per_day']))
budgetall=[r for r in base_plan if r['service_date']!=day]+budgetplan
controls['budget_control_generated']=(bcost>dec(decision['procurement_budget_yuan_per_day']) and bunits<=int(decision['capacity_units_per_day']))
controls['budget_excess_rejected']=controls['budget_control_generated'] and any(x.startswith('budget:') for x in validate_plan(budgetall))

# Delivery output format checks: required source-key columns and numeric fields, generated independent controls only.
forecast_schema=['service_date','store_id','item_id','demand_point_units']
q_schema=['service_date','store_id','item_id','q_units']
controls['required_output_columns']={'forecast':forecast_schema,'replenishment':q_schema,'expected_rows_each':len(expected),'unique_key_columns':['service_date','store_id','item_id']}

# Cross-day / cross-zone and availability coverage summary.
future_weather=[r for r in weather if r['service_date'] in future_dates and r['kind']=='forecast' and parse_dt(r['available_at'],tz)<=origin]
future_promos=[r for r in promos if r['service_date'] in future_dates and parse_dt(r['announced_at'],tz)<=origin]
late_promos=[r for r in promos if r['service_date'] in future_dates and parse_dt(r['announced_at'],tz)>origin]
weather_day_zone=Counter((r['service_date'],r['zone_id']) for r in future_weather)
weather_test=None
for f in weather:
    if f['kind']=='forecast' and parse_dt(f['available_at'],tz)<=origin:
        match=next((x for x in weather if x['kind']=='observed' and (x['service_date'],x['zone_id'])==(f['service_date'],f['zone_id']) and parse_dt(x['available_at'],tz)>origin),None)
        cross=next((x for x in weather if x['kind']=='observed' and x['service_date']==f['service_date'] and x['zone_id']!=f['zone_id'] and parse_dt(x['available_at'],tz)>origin),None)
        if match and cross:
            weather_test={'forecast_key':[f['service_date'],f['zone_id']],'legal_observed_later_key':[match['service_date'],match['zone_id']],'cross_zone_candidate_key':[cross['service_date'],cross['zone_id']],'forecast_available_by_origin':parse_dt(f['available_at'],tz)<=origin,'observed_arrived_after_origin':parse_dt(match['available_at'],tz)>origin,'legal_pair_equal':(f['service_date'],f['zone_id'])==(match['service_date'],match['zone_id']),'cross_zone_rejected':(f['service_date'],f['zone_id'])!=(cross['service_date'],cross['zone_id'])}; break

out={
 'scope':'independent reception preparation only; no author results read; all formal d1-d5 unverified',
 'decision':{'origin':origin.isoformat(),'timezone':decision['timezone'],'future_dates':[future_dates[0],future_dates[-1]],'expected_keys':len(expected),'capacity_units_per_day':decision['capacity_units_per_day'],'budget_yuan_per_day':decision['procurement_budget_yuan_per_day']},
 'lock_checks':{'input_all_match':all(x['match'] for x in input_checks),'inputs':input_checks,'authorized_design_docs_match':all(x['match'] and x['bytes']==x['locked_bytes'] for x in design_checks),'authorized_design_docs':design_checks,'other_design_lock_entries_read_or_hashed':False},
 'source_counts':{'demand_rows':len(demand),'demand_keys':len(unique_keys),'keys_with_multiple_revision_ids':sum(len(v)>1 for v in revision_counts.values()),'exact_duplicate_excess_rows':dup_excess,'same_revision_content_conflicts_at_final_label_cutoff':len(final_conflicts),'demand_available_min':min(avail).isoformat(),'demand_available_max':max(avail).isoformat(),'weather_rows':len(weather),'weather_kind_counts':dict(weather_kinds),'promotion_rows':len(promos),'item_rows':len(items),'store_rows':len(stores)},
 'historical_revision_control':{'derived_cutoff':control_origin.isoformat(),'sample':rev_pair,'legal_version_selected':bool(rev_pair and parse_dt(rev_pair['selected_at_origin']['available_at'],tz)<=control_origin),'late_higher_revision_excluded_from_snapshot':late_revision_excluded},
 'historical_baseline':{'method':'median of up to 8 latest same-weekday demand labels visible at each historical origin; fallback to 56-day same-series median; otherwise zero','evaluation_label_cutoff':latest_label_cutoff.isoformat(),'origins':backtests,'scope_note':'baseline is an independently prepared comparator/control, not a claim about author quality or a prescribed method'},
 'availability_coverage':{'future_weather_forecast_rows_known_at_origin':len(future_weather),'future_date_zone_pairs_known':len(weather_day_zone),'all_future_date_zone_pairs_expected':len(future_dates)*len({r['zone_id'] for r in stores}),'future_forecasts_missing_rain':sum(not r.get('rain_mm','').strip() for r in future_weather),'future_promotion_rows_known_at_origin':len(future_promos),'future_promotion_rows_late_or_unknown':len(late_promos),'cross_day_cross_zone_boundary_control':weather_test,'late_arriving_label_pair_found':bool(rev_pair)},
 'independent_decision_controls':controls,
 'cost_formula':{'loss':'shortage_yuan*max(actual-q,0)+waste_yuan*max(q-actual,0)','procurement':'procurement_yuan*q; budget constraint only; not included in loss','source_costs_valid_finite_nonnegative':all(v.is_finite() and v>=0 for d in (price,shortage,waste) for v in d.values())},
 'future_truth_opened':False
}
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
