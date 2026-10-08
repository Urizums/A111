import sys,json
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[4]
CODE=ROOT/'runs/R20/execution/code'
sys.path.insert(0,str(CODE))
import run as production
RAW=ROOT/'runs/R20/inputs/raw'; OUT=ROOT/'runs/R20/review/initial/production_controls'
OUT.mkdir(parents=True,exist_ok=True)
data=production.Data(RAW,OUT)
origin=data.decision['origin']
# Authentic revision pair from the source, selected via the frozen production snapshot method.
control_origin='2026-08-31T18:00:00'
snap=data.snapshot(control_origin)
pair=('2026-08-29','S01','K06')
selected=snap[(snap.service_date==pair[0])&(snap.store_id==pair[1])&(snap.item_id==pair[2])].iloc[0]
allrows=data.tables['demand_reports']
later=allrows[(allrows.service_date==pair[0])&(allrows.store_id==pair[1])&(allrows.item_id==pair[2])&(allrows.revision==2)].iloc[0]
assert int(selected.revision)==1 and int(selected.demand_units)==25 and int(later.demand_units)==27
assert selected.available_at<=production.ts(control_origin) and later.available_at>production.ts(control_origin)
# Authentic weather feature path: same-date/zone forecast available at origin; later observed value stays out.
train=data.snapshot(origin)
grid=data.grid(['2026-09-30'])
feat=data.features(grid,origin,train)
weather_row=feat[(feat.service_date=='2026-09-30')&(feat.store_id=='S01')].iloc[0]
weather_table=data.tables['weather']
zone=weather_row.zone_id
wf=weather_table[(weather_table.service_date=='2026-09-30')&(weather_table.zone_id==zone)&(weather_table.kind=='forecast')].iloc[0]
wo=weather_table[(weather_table.service_date=='2026-09-30')&(weather_table.zone_id==zone)&(weather_table.kind=='observed')].iloc[0]
assert weather_row.weather_available_at<=production.ts(origin)
assert wo.available_at>production.ts(origin)
assert float(weather_row.rain_mm)==float(wf.rain_mm) and (pd.isna(wo.rain_mm) or float(weather_row.rain_mm)!=float(wo.rain_mm))
assert 'settlement_yuan' not in feat.columns
# Finite/nonnegative source-number rejection through actual production audit function (in-memory only).
origval=data.tables['demand_reports'].loc[0,'demand_units']
data.tables['demand_reports'].loc[0,'demand_units']=np.nan
numeric_rejected=False
try:
    data.audit()
except AssertionError:
    numeric_rejected=True
finally:
    data.tables['demand_reports'].loc[0,'demand_units']=origval
assert numeric_rejected
# Production q consumer accepts every delivered day and rejects actual illegal numerical controls.
qtable=pd.read_csv(ROOT/'runs/R20/execution/delivery/results/future_replenishment.csv')
accepted_days=0
for d,rows in qtable.groupby('service_date'):
    qmap={(r.store_id,r.item_id):int(r.q_units) for r in rows.itertuples()}
    q=np.array([qmap[x] for x in data.pairs],dtype=int)
    production.verify_q(q,data,1600,6000);accepted_days+=1
assert accepted_days==14
illegal_results={}
for name,mutate in [('fraction',lambda a:a.astype(float)),('negative',lambda a:a.copy()),('nan',lambda a:a.astype(float))]:
    base=np.zeros(96,dtype=int); bad=mutate(base)
    if name=='fraction':bad[0]=.5
    if name=='negative':bad[0]=-1
    if name=='nan':bad[0]=np.nan
    try:production.verify_q(bad,data,1600,6000)
    except AssertionError:illegal_results[name]='rejected'
    else:illegal_results[name]='ACCEPTED'
assert all(v=='rejected' for v in illegal_results.values())
out={'scope':'actual frozen production functions; no production source or raw file modified','late_revision_control':{'origin':control_origin,'key':pair,'selected_revision':int(selected.revision),'selected_units':int(selected.demand_units),'selected_available_at':selected.available_at.isoformat(),'later_revision':int(later.revision),'later_units':int(later.demand_units),'later_available_at':later.available_at.isoformat(),'legal_selected_and_late_rejected':True},'weather_control':{'key':[weather_row.service_date,zone],'feature_rain_mm':float(weather_row.rain_mm),'forecast_rain_mm':float(wf.rain_mm),'forecast_available_at':wf.available_at.isoformat(),'observed_rain_mm':None if pd.isna(wo.rain_mm) else float(wo.rain_mm),'observed_available_at':wo.available_at.isoformat(),'forecast_included_observed_excluded':True,'settlement_feature_column_present':False},'numeric_control':{'nan_demand_rejected_by_production_audit':numeric_rejected,'mutated_memory_restored':True},'q_control':{'delivered_days_accepted':accepted_days,'illegal_q_results':illegal_results},'formal_verdict':'not determined by this control alone'}
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
