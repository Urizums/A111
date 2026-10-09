"""Root Decimal consumer cross-check; independent reception remains a separate actor."""
import base64
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
SCI=BASE/'execution/science-v1'
D=Decimal
checks=0
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def eq(a,b,where,tol=D('0.00000002')):
    global checks
    assert abs(D(str(a))-D(str(b)))<=tol,(where,a,b)
    checks+=1
lock=read(BASE/'execution-lock.json')
for r in lock['files']:
    b=(ROOT/r['path']).read_bytes()
    assert len(b)==r['size_bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],r['path']
items={r['item_id']:r for r in rows(ROOT/'runs/R21/inputs/raw/items.csv')}
reports=rows(ROOT/'runs/R21/inputs/raw/demand_reports.csv')
mature={}
for i,r in enumerate(reports,2):
    if r['available_at']>'2026-11-04T18:00:00':continue
    key=tuple(r[k] for k in ['service_date','store_id','item_id'])
    if key not in mature or int(r['revision'])>int(mature[key]['revision']):mature[key]=dict(r,raw_row=i)
z=rows(SCI/'results/keys.csv');assert len(z)==24192
seen=set(); grouped=defaultdict(list)
for r in z:
    key=tuple(r[k] for k in ['service_date','store_id','item_id'])
    ident=(r['origin'],r['method_id'],*key);assert ident not in seen;seen.add(ident)
    label=mature[key]; assert int(r['actual_revision'])==int(label['revision']) and int(r['actual_raw_row'])==label['raw_row']
    eq(r['actual'],label['demand_units'],(ident,'raw mature label'),D(0))
    p,y,lo,hi,q=[D(r[k]) for k in ['point','actual','lower90','upper90','q_units']]
    assert all(v.is_finite() for v in [p,y,lo,hi,q]) and min(p,y,lo,hi,q)>=0 and lo<=hi
    assert q==q.to_integral_value() and q<=D(items[r['item_id']]['daily_max_units'])
    cost,a,b=[D(items[r['item_id']][k]) for k in ['procurement_yuan','shortage_yuan','waste_yuan']]
    calc=dict(abs_error=abs(p-y),sq_error=(p-y)**2,shortage_yuan=max(y-q,D(0))*a,
        waste_yuan=max(q-y,D(0))*b,procurement_yuan=q*cost,
        interval_score=hi-lo+20*max(lo-y,D(0))+20*max(y-hi,D(0)))
    for k,v in calc.items():eq(r[k],v,(ident,k))
    assert (r['covered']=='True')==(lo<=y<=hi)
    for k in ['point','actual','lower90','upper90','q_units',*calc]:r[k]=D(r[k])
    grouped[(r['origin'],r['method_id'])].append(r)
def metric(g):
    if not g:return None
    n=D(len(g));days=D(len({r['service_date'] for r in g}))
    mean=lambda fn:sum((fn(r) for r in g),D(0))/n
    return dict(mae=mean(lambda r:abs(r['point']-r['actual'])),
        rmse=mean(lambda r:(r['point']-r['actual'])**2).sqrt(),
        bias=mean(lambda r:r['point']-r['actual']),
        coverage=mean(lambda r:D(r['lower90']<=r['actual']<=r['upper90'])),
        below=mean(lambda r:D(r['actual']<r['lower90'])),above=mean(lambda r:D(r['actual']>r['upper90'])),
        width=mean(lambda r:r['upper90']-r['lower90']),interval_score=mean(lambda r:r['interval_score']),
        shortage_per_day=sum((r['shortage_yuan'] for r in g),D(0))/days,
        waste_per_day=sum((r['waste_yuan'] for r in g),D(0))/days,
        loss_per_day=sum((r['shortage_yuan']+r['waste_yuan'] for r in g),D(0))/days,
        procurement_per_day=sum((r['procurement_yuan'] for r in g),D(0))/days,
        q_per_day=sum((r['q_units'] for r in g),D(0))/days)
def check_groups(path,columns):
    global checks
    nonempty=empty=0
    for report in rows(path):
        g=grouped[(report['origin'],report['method_id'])]
        g=[r for r in g if all(str(r[c])==report[c] for c in columns)]
        assert int(report['rows'])==len(g) and int(report['days'])==len({r['service_date'] for r in g})
        m=metric(g)
        if m:
            assert report['status']=='estimated';nonempty+=1
            for k,v in m.items():eq(report[k],v,(path.name,report['origin'],report['method_id'],columns,k))
        else:
            assert report['status']=='not_estimable' and all(report[k]=='' for k in metric(z[:1]));empty+=1
        checks+=2
    return dict(file=path.relative_to(ROOT).as_posix(),estimated=nonempty,not_estimable=empty)
specs=dict(overall=[],stage=['stage'],band=['band'],activity=['holiday'],activity_stage=['holiday','stage'],
    activity_band=['holiday','band'],activity_horizon=['holiday','horizon'],store=['store_id'],item=['item_id'],horizon=['horizon'])
with localcontext() as context:
    context.prec=40
    tables=[check_groups(SCI/f'results/group_{name}.csv',cols) for name,cols in specs.items()]
    tables.append(check_groups(SCI/'results/daily.csv',['service_date']))
    for r in rows(SCI/'results/combined_first_two.csv'):
        g=[s for s in z if s['method_id']==r['method_id'] and s['origin'] in ['2026-07-22T18:00:00','2026-09-02T18:00:00']]
        assert len({s['service_date'] for s in g})==84 and len(g)==8064
        for k,v in metric(g).items():eq(r[k],v,('combined_first_two',k))
    daily={}
    for identity,g in grouped.items():
        for day in {r['service_date'] for r in g}:
            h=[r for r in g if r['service_date']==day];assert len(h)==96
            units=sum((r['q_units'] for r in h),D(0));cost=sum((r['procurement_yuan'] for r in h),D(0))
            assert units<=1600 and cost<=6000
            daily[(*identity,day)]=metric(h)
    for r in rows(SCI/'results/paired_daily.csv'):
        a=daily[(r['origin'],'shared_ridge10',r['service_date'])];b=daily[(r['origin'],'weekly_mean56',r['service_date'])]
        eq(r['loss_W_minus_R'],b['loss_per_day']-a['loss_per_day'],'paired_loss')
        eq(r['score_W_minus_R'],b['interval_score']-a['interval_score'],'paired_score')
freeze=read(BASE/'execution/prospective-freeze.json')
first=read(BASE/'execution/receipts/0007-first-science-v1.json')
assert freeze['actual_frozen_at_utc']<first['begin']['utc']
receipt_checks=[]
for p in sorted((BASE/'execution/receipts').glob('*.json')):
    r=read(p);assert r['state']=='finished' and type(r['exit_code'])==int
    for k in ['stdout','stderr']:assert base64.b64decode(r[k+'_base64']).decode('utf-8',errors='replace')==r[k]
    assert datetime.fromisoformat(r['begin']['utc'])<=datetime.fromisoformat(r['end']['utc'])
    receipt_checks.append(dict(path=p.relative_to(ROOT).as_posix(),exit_code=r['exit_code']))
result=dict(scope='Root cross-check of frozen raw labels, per-key arithmetic, predefined aggregation, resources and actual receipts; not independent acceptance.',
    source_lock=hashlib.sha256((BASE/'execution-lock.json').read_bytes()).hexdigest(),keys=len(z),
    arithmetic_comparisons=checks,group_tables=tables,daily_resource_rows=len(daily),paired_dates=126,
    freeze_before_first_fit=True,receipts=receipt_checks,model=None,tokens=None,cost=None)
target=BASE/'final/root-metrics.json';target.parent.mkdir(exist_ok=True)
with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
