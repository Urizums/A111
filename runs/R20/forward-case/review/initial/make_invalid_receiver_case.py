import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source-results',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);a=p.parse_args()
if a.dest.exists(): raise SystemExit('destination must be absent')
shutil.copytree(a.source_results,a.dest)
f=a.dest/'results.json'; data=json.loads(f.read_text(encoding='utf-8'))
first, later=data['origins'][0],data['origins'][1]
c=next(x for x in first['coordinates'] if x['target_date']=='2026-05-01' and x['series_id']=='A')
future=next(x for x in later['coordinates'] if x['target_date']==c['target_date'] and x['series_id']==c['series_id'])
c['label']=future['label']; c['residual_units']='3'; c['coordinate_available_at']=future['label']['available_at']
day=next(x for x in first['days'] if x['target_date']=='2026-05-01'); day['vector_available_at']=future['label']['available_at']
vec=next(x for x in first['calibration_vectors'] if x['target_date']=='2026-05-01'); vec['residual_units'][0]='3'; vec['vector_available_at']=future['label']['available_at']
f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created a derived output that selects the 2026-05-05 label revision at the 2026-05-03 decision origin; original output untouched.')
