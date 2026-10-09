"""Actual neutral input audit; no prior workflow, fit, result or private truth read."""
import csv
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R23'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
lock=read(BASE/'source-lock.json')
for r in lock['files']:
    b=(ROOT/r['path']).read_bytes();assert len(b)==r['size_bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
inputs=read(ROOT/'runs/R21/input-lock.json')
identities=[]
for r in inputs['files']:
    if not r['path'].startswith(('runs/R21/inputs/raw/','runs/R21/inputs/reference/')):continue
    b=(ROOT/r['path']).read_bytes();assert len(b)==r['size_bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
    identities.append(r)
raw=ROOT/'runs/R21/inputs/raw'
decision=read(raw/'decision.json'); origin=datetime.fromisoformat(decision['origin'])
reports=rows(raw/'demand_reports.csv')
seen={};conflicts=[];asof={}
for r in reports:
    key=tuple(r[c] for c in ['service_date','store_id','item_id']); version=(*key,r['revision'])
    if version in seen and seen[version]!=r:conflicts.append(version)
    seen[version]=r
    if datetime.fromisoformat(r['available_at'])<=origin and r['service_date']<origin.date().isoformat():
        if key not in asof or int(r['revision'])>int(asof[key]['revision']):asof[key]=r
assert not conflicts
stores=rows(raw/'stores.csv'); items=rows(raw/'items.csv'); calendar=rows(raw/'calendar.csv')
dates=[]; d=datetime.fromisoformat(decision['future_begin']).date(); end=datetime.fromisoformat(decision['future_end']).date()
while d<=end:dates.append(d.isoformat());d+=timedelta(days=1)
assert len(dates)==decision['horizon_days']==42
calendar_by_date={r['service_date']:r for r in calendar}; assert all(d in calendar_by_date for d in dates)
audit=dict(scope='Root actual raw input audit; not a workflow, numerical experiment, independent reception or new blind case.',
    raw_identities=identities,raw_report_rows=len(reports),unique_versions=len(seen),asof_train_keys=len(asof),
    raw_history_last_service=max(r['service_date'] for r in reports),decision_origin=decision['origin'],
    delivery_dates=len(dates),stores=len(stores),items=len(items),required_future_keys=len(dates)*len(stores)*len(items),
    updates_during_delivery='none; fixed single-origin policy specified by neutral task',
    future_actuals_read=False,previous_design_results_read=False,model_fitted=False,
    designer_packet='runs/R23/brief/INPUTS.json; this audit and acceptance are withheld from designer.',
    actual_model=None,tokens=None,cost=None)
out=BASE/'audit/INPUT_AUDIT.json';out.parent.mkdir(exist_ok=True)
with out.open('x',encoding='utf-8') as f:json.dump(audit,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in audit.items() if k!='raw_identities'},ensure_ascii=False))
