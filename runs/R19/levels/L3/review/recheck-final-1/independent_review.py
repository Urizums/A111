import csv,json,math,time,itertools,copy,sys
from pathlib import Path
from collections import Counter
import independent_checker as ic
H=Path(__file__).resolve().parent;R=H.parents[5];E=R/'runs/R19/levels/L3/execution'
BASE=ic.source_catalog();tasks=['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']
def read_rows(p):
 raw=list(csv.DictReader((p/'placements.csv').open(encoding='utf-8-sig')));rows=[]
 for r in raw:
  row={k:r[k] for k in ['item_id','cargo_type','vehicle_id','vehicle_type']}
  row.update({k:float(r[k+'_cm']) for k in ['x','y','z','dx','dy','dz']});rows.append(row)
 return raw,rows
def catalogue(data):
 kinds={'standard':'标准件','fragile':'易碎件','directional':'定向件'}
 return ({r['cargo_type']:{'kind':kinds[r['category']],'dims':tuple(r[a+'_cm'] for a in ['l','w','h']),'mass':r['weight_kg'],'count':r['quantity']} for r in data['cargo']},
         {r['vehicle_type']:{'dims':tuple(r[a+'_cm'] for a in ['l','w','h']),'payload':r['capacity_kg'],'cost':r['cost_yuan']} for r in data['vehicles']})
def review(p,task,scenario=False):
 t=time.perf_counter();raw,rows=read_rows(p);cfg=json.loads((p/'config.json').read_text(encoding='utf-8'))
 src=BASE if not scenario else catalogue(cfg['instance']);ic.source_catalog=lambda:src
 out=ic.check(rows,full_batch=not task.startswith('Q1-S'),fragile_rotation='upright' if cfg.get('fragile_upright') else 'six',fragile_support='single',
              gap_cm=cfg.get('gap',3),pressure_limit=cfg.get('pressure',500),own_mass=cfg.get('own_mass',False))
 errors=[];groups={}
 for original,row in zip(raw,rows):
  c=src[0][row['cargo_type']];o=original['orientation']
  if sorted(o)!=list('xyz') or tuple(c['dims']['xyz'.index(a)] for a in o)!=tuple(row[k] for k in ['dx','dy','dz']):errors.append({'code':'orientation_mapping','item':row['item_id']})
  if c['kind']=='定向件' and o!='xyz':errors.append({'code':'directional_axis_map','item':row['item_id']})
  if original['task_id']!=task:errors.append({'code':'task_row_identity','item':row['item_id']})
  groups.setdefault(row['vehicle_id'],[]).append((original,row))
  if cfg.get('fragile_floor') and c['kind']=='易碎件' and row['z']>1e-7:errors.append({'code':'fragile_floor','item':row['item_id']})
 allowed={'Q1-S1':{'T1'},'Q1-S2':{'T2'},'Q1-F1':{'T1'},'Q1-F2':{'T2'},'Q2-N':{'T1','T2'},'Q2-C':{'T1','T2'}}[task]
 if any(v['vehicle_type'] not in allowed for v in out['vehicles']):errors.append({'code':'task_vehicle_type'})
 if task.startswith('Q1-S') and out['N']!=1:errors.append({'code':'single_task_N'})
 for typ,c in src[0].items():
  got={r['item_id'] for r in rows if r['cargo_type']==typ}
  expected={f'{typ}-{i:04d}' for i in range(1,len(got)+1)}
  if got!=expected:errors.append({'code':'canonical_item_range','cargo_type':typ})
 min_gap=float('inf');support_relations=0;pairs=0
 for vid,rs in groups.items():
  v=src[1][rs[0][1]['vehicle_type']];pairs+=len(rs)*(len(rs)-1)//2
  for orig,a in rs:
   min_gap=min(min_gap,v['dims'][2]-a['z']-a['dz'])
   if abs(a['z'])<=1e-7:
    if orig['support_ids']:errors.append({'code':'floor_support_trace','item':a['item_id']})
   else:
    supporters=[b for _,b in rs if b['item_id']!=a['item_id'] and abs(b['z']+b['dz']-a['z'])<=1e-7 and b['x']<=a['x']+1e-7 and b['y']<=a['y']+1e-7 and b['x']+b['dx']>=a['x']+a['dx']-1e-7 and b['y']+b['dy']>=a['y']+a['dy']-1e-7]
    support_relations+=len(supporters)
    if len(supporters)!=1 or orig['support_ids']!=supporters[0]['item_id']:errors.append({'code':'single_support_trace','item':a['item_id']})
 V=sum(v['volume_cm3'] for v in out['vehicles'])/1e6;W=sum(v['mass_kg'] for v in out['vehicles'])
 out.update(volume_m3=V,weight_kg=W,n1=sum(v['vehicle_type']=='T1' for v in out['vehicles']),n2=sum(v['vehicle_type']=='T2' for v in out['vehicles']),
            Uv=V/(sum(math.prod(src[1][v['vehicle_type']]['dims']) for v in out['vehicles'])/1e6),
            Uw=W/sum(src[1][v['vehicle_type']]['payload'] for v in out['vehicles']),min_top_gap_cm=min_gap,pair_count=pairs,support_relations=support_relations)
 declared=json.loads((p/'metrics.json').read_text(encoding='utf-8'));delta={k:out[k]-declared[k] for k in ['N','n1','n2','C','Uv','Uw','volume_m3','weight_kg']}
 if any(abs(v)>1e-8 for v in delta.values()):errors.append({'code':'metric_delta','delta':delta})
 if dict(Counter(r['cargo_type'] for r in rows))!=declared['loaded_counts']:errors.append({'code':'declared_counts'})
 for v in out['vehicles']:
  author=next(x for x in declared['vehicles'] if x['vehicle_id']==v['vehicle_id'])
  for a,b in [('mass_kg','weight_kg'),('Uv','Uv'),('Uw','Uw')]:
   if abs(v[a]-author[b])>1e-8:errors.append({'code':'vehicle_metric','vehicle':v['vehicle_id'],'field':a})
  if abs(v['volume_cm3']/1e6-author['volume_m3'])>1e-8:errors.append({'code':'vehicle_volume','vehicle':v['vehicle_id']})
 out['adapter_errors']=errors;out['independent_pass_under_declared_model']=out['valid_under_declared_model'] and not errors
 out['metric_deltas']=delta;out['elapsed_seconds']=time.perf_counter()-t;out['source']='direct original raw' if not scenario else 'explicit declared scenario checked against direct raw transformations separately'
 return out
def main():
 selected=[];fresh=[]
 for task in tasks:
  a=review(E/f'plans/{task}/selected',task);b=review(H/f'replay_raw/{task}',task)
  for label,value in [('selected',a),('fresh',b)]:
   dest=H/'numeric';dest.mkdir(exist_ok=True);(dest/f'{label}-{task}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
  selected.append({'task':task,**{k:a[k] for k in ['independent_pass_under_declared_model','N','n1','n2','C','Uv','Uw','volume_m3','weight_kg','counts','min_top_gap_cm','pair_count','elapsed_seconds']},'max_pressure':max(v['max_pressure_kg_m2'] for v in a['vehicles'])})
  fresh.append({'task':task,'pass':b['independent_pass_under_declared_model'],'metric_deltas':b['metric_deltas']})
 result={'selected':selected,'fresh':fresh,'all_selected_pass':all(x['independent_pass_under_declared_model'] for x in selected),'all_fresh_pass':all(x['pass'] for x in fresh),'claims_scope':'declared single-support static model, not global optimization or road safety'}
 (H/'numeric-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));assert result['all_selected_pass'] and result['all_fresh_pass']
if __name__=='__main__':main()
