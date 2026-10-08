import argparse, csv, json, hashlib
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
RAW=ROOT/'runs/R20/inputs/raw'
def dec(x):
    try:return Decimal(str(x))
    except (InvalidOperation,ValueError,TypeError):return Decimal('NaN')
def load_csv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        return reader.fieldnames or [],list(reader)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
with (RAW/'decision.json').open(encoding='utf-8-sig') as f: decision=json.load(f)
with (RAW/'stores.csv').open(encoding='utf-8-sig',newline='') as f: stores=list(csv.DictReader(f))
with (RAW/'items.csv').open(encoding='utf-8-sig',newline='') as f: item_rows=list(csv.DictReader(f))
store_ids={r['store_id'] for r in stores}; item_by_id={r['item_id']:r for r in item_rows}; item_ids=set(item_by_id)
start=date.fromisoformat(decision['future_begin']); end=date.fromisoformat(decision['future_end'])
dates=[(start+timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
expected={(d,s,k) for d in dates for s in store_ids for k in item_ids}
capacity=int(decision['capacity_units_per_day']); budget=dec(decision['procurement_budget_yuan_per_day'])
def kt(r):return (r.get('service_date',''),r.get('store_id',''),r.get('item_id',''))
def shape_errors(rows, fields, label):
    errors=[]
    if not rows: errors.append(label+':empty')
    if rows:
        for col in fields:
            if col not in rows[0]:errors.append(label+':missing_column:'+col)
    return errors
def key_errors(rows,label):
    errors=[]; counts=Counter(kt(r) for r in rows)
    for k,n in counts.items():
        if k not in expected: errors.append(label+':unexpected_key:'+repr(k))
        if n>1: errors.append(label+':duplicate_key:'+repr(k))
    missing=expected-set(counts)
    if missing:errors.append(label+':missing_keys:'+str(len(missing)))
    return errors
def validate_forecast(rows):
    errors=shape_errors(rows,['service_date','store_id','item_id','demand_point_units'],'forecast')
    if errors:return errors
    errors.extend(key_errors(rows,'forecast'))
    for r in rows:
        v=dec(r['demand_point_units'])
        if not v.is_finite():errors.append('forecast:nonfinite:'+repr(kt(r)))
        elif v<0:errors.append('forecast:negative:'+repr(kt(r)))
    return errors
def validate_replenishment(rows):
    errors=shape_errors(rows,['service_date','store_id','item_id','q_units'],'replenishment')
    if errors:return errors
    errors.extend(key_errors(rows,'replenishment'))
    daily=defaultdict(lambda:[0,Decimal(0)])
    for r in rows:
        k=kt(r); v=dec(r['q_units'])
        if not v.is_finite():errors.append('replenishment:nonfinite:'+repr(k));continue
        if v<0:errors.append('replenishment:negative:'+repr(k));continue
        if v!=v.to_integral_value():errors.append('replenishment:noninteger:'+repr(k));continue
        q=int(v); it=k[2]
        if it not in item_by_id:continue
        maxq=int(dec(item_by_id[it]['daily_max_units']))
        if q>maxq:errors.append('replenishment:item_max:'+repr(k))
        cost=dec(item_by_id[it]['procurement_yuan'])
        if not cost.is_finite() or cost<0:errors.append('source:invalid_procurement_cost:'+it);continue
        daily[k[0]][0]+=q;daily[k[0]][1]+=cost*q
    for d,(units,cost) in daily.items():
        if units>capacity:errors.append('replenishment:capacity:'+d+':'+str(units))
        if cost>budget:errors.append('replenishment:budget:'+d+':'+str(cost))
    return errors

def zero_plan():return [{'service_date':d,'store_id':s,'item_id':it,'q_units':0} for d in dates for s in sorted(store_ids) for it in sorted(item_ids)]
def fixture_controls():
    base=zero_plan(); results={'all_zero_valid':not validate_replenishment(base)}
    results['missing_key_rejected']=any(x.startswith('replenishment:missing_keys') for x in validate_replenishment(base[:-1]))
    results['duplicate_key_rejected']=any(x.startswith('replenishment:duplicate_key') for x in validate_replenishment(base+[dict(base[0])]))
    bad=[dict(r) for r in base];bad[0]['q_units']='0.5';results['fraction_rejected']=any(x.startswith('replenishment:noninteger') for x in validate_replenishment(bad))
    bad=[dict(r) for r in base];bad[0]['q_units']='-1';results['negative_rejected']=any(x.startswith('replenishment:negative') for x in validate_replenishment(bad))
    bad=[dict(r) for r in base];bad[0]['q_units']=int(dec(item_by_id[bad[0]['item_id']]['daily_max_units']))+1;results['per_item_max_rejected']=any(x.startswith('replenishment:item_max') for x in validate_replenishment(bad))
    day=dates[0]
    def targeted(order,target,budget_cap=None):
        rows=[r for r in base if r['service_date']!=day]+[{'service_date':day,'store_id':s,'item_id':it,'q_units':0} for s in sorted(store_ids) for it in sorted(item_ids)]
        ix={(r['store_id'],r['item_id']):r for r in rows if r['service_date']==day};units=0;cost=Decimal(0)
        for s,it in order:
            r=ix[(s,it)];c=dec(item_by_id[it]['procurement_yuan']);room=int(dec(item_by_id[it]['daily_max_units']))
            while room>0 and units<target and (budget_cap is None or cost<=budget_cap):
                r['q_units']+=1;room-=1;units+=1;cost+=c
                if budget_cap is not None and cost>budget_cap:break
            if units>=target or (budget_cap is not None and cost>budget_cap):break
        return rows,units,cost
    byunit=sorted(((s,it) for s in store_ids for it in item_ids),key=lambda z:(dec(item_by_id[z[1]]['procurement_yuan']),z))
    capplan,cu,cc=targeted(byunit,capacity+1)
    results['capacity_control_constructed']=cu>capacity and cc<=budget
    results['capacity_excess_rejected']=results['capacity_control_constructed'] and any(x.startswith('replenishment:capacity') for x in validate_replenishment(capplan))
    bycost=sorted(((s,it) for s in store_ids for it in item_ids),key=lambda z:(-dec(item_by_id[z[1]]['procurement_yuan']),z))
    bp,bu,bc=targeted(bycost,capacity,budget)
    results['budget_control_constructed']=bc>budget and bu<=capacity
    results['budget_excess_rejected']=results['budget_control_constructed'] and any(x.startswith('replenishment:budget') for x in validate_replenishment(bp))
    badforecast=[{'service_date':d,'store_id':s,'item_id':it,'demand_point_units':0} for d,s,it in expected]
    results['forecast_full_key_valid']=not validate_forecast(badforecast)
    results['forecast_nan_rejected']=any(x.startswith('forecast:nonfinite') for x in validate_forecast([dict(badforecast[0],demand_point_units='NaN')]+badforecast[1:]))
    return results

def main():
    ap=argparse.ArgumentParser(description='Independent R20 future table format and raw-constraint checker')
    ap.add_argument('--forecast');ap.add_argument('--replenishment');ap.add_argument('--self-check',action='store_true')
    a=ap.parse_args();out={'expected_rows':len(expected),'key_columns':['service_date','store_id','item_id'],'raw_cost_source':'runs/R20/inputs/raw/items.csv'}
    if a.forecast:
        names,rows=load_csv(a.forecast);errs=validate_forecast(rows)
        out['forecast']={'path':str(Path(a.forecast).resolve()),'sha256':sha(a.forecast),'rows':len(rows),'columns':names,'errors':errs,'valid':not errs}
    if a.replenishment:
        names,rows=load_csv(a.replenishment);errs=validate_replenishment(rows)
        out['replenishment']={'path':str(Path(a.replenishment).resolve()),'sha256':sha(a.replenishment),'rows':len(rows),'columns':names,'errors':errs,'valid':not errs}
    if a.self_check:out['self_check_controls']=fixture_controls()
    if not (a.forecast or a.replenishment or a.self_check):ap.error('provide --self-check or delivery file paths')
    out['formal_status']='unverified until frozen author outputs are supplied and independently checked'
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
    if any(not v for v in out.get('self_check_controls',{}).values()):return 2
    if any(not out[k]['valid'] for k in ('forecast','replenishment') if k in out):return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
