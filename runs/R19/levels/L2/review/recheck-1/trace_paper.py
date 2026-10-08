from pathlib import Path
import json,math,collections,hashlib,datetime
from audit_independent import a,O,E,B,ITEMS,VS,bound
from run_calls import dump
A=json.loads((O/'independent-audit.json').read_text());text=(E/'paper/paper.md').read_text(encoding='utf-8');tables=[];cur=[]
for line in text.splitlines()+['']:
 if line.startswith('|'):
  cells=[c.strip() for c in line.strip('|').split('|')]
  if not all(set(c)<=set('-: ') for c in cells):cur.append(cells)
 elif cur:tables.append(cur);cur=[]
assert len(tables)==7
final={Path(x['folder']).name:x for x in A['layouts'] if x['tag']=='frozen' and '/selected/' in x['folder'].replace('\\','/')}
singles={Path(x['folder']).name:x for x in A['layouts'] if x['tag']=='frozen' and '/single/' in x['folder'].replace('\\','/')}
expected=[]
expected.append([[t,{'standard':'标准件','fragile':'易碎件','directional':'定向件'}[i['category']],'×'.join(str(int(n)) for n in i['dims']),str(float(i['weight'])),str(i['count']),f"{i['weight']/(math.prod(i['dims'])/1e9):.2f}"] for t,i in a.CAT.items()])
expected.append([['single_'+name,','.join(str(x['counts'].get(t,0)) for t in a.CAT),f"{x['metrics']['volume_utilization']*100:.2f}",f"{x['metrics']['weight_utilization']*100:.2f}",'True'] for name,x in sorted(singles.items())])
labels={'q1_all_v1':'仅车型1','q1_all_v2':'仅车型2','q2_vehicles':'混合最少车','q2_cost':'混合最低成本'}
er=[]
for name,label in labels.items():
 x=final[name];m=x['metrics'];lb=x['independent_relaxation']['lower_bound'];ub=m['cost_yuan'] if name=='q2_cost' else m['vehicle_count'];er.append([label,str(m['vehicle_count']),str(int(m['cost_yuan'])),f"{m['volume_utilization']*100:.2f}",f"{m['weight_utilization']*100:.2f}",str(lb),f"{(ub-lb)/ub*100:.2f}"])
expected.append(er)
cost=final['q2_cost'];expected.append([[vid,mtype,str(sum(m['counts'].values()))]+[str(m['counts'].get(t,0)) for t in a.CAT]+[f"{m['volume_utilization']*100:.1f}",f"{m['weight_utilization']*100:.1f}"] for vid,m in cost['per_vehicle'].items() for mtype in [next(r['vehicle_type'] for r in a.readcsv(E/'results/final/selected/q2_cost/placements.csv') if r['vehicle_id']==vid)]])
comp=json.loads((E/'research/comparison/guarded_summary.json').read_text());by={r['case']:r for r in A['guard_choices']};er=[]
for r in comp:
 z=by[r['case']];choices={c['scenario']:c['independent_best_key'] for c in z['checks']};n=len(json.loads((E/'research/comparison'/r['case']/'pattern_library.json').read_text()));er.append([r['method'],str(r['seed']),str(n),str(choices['q1_all_v1'][0]),str(choices['q1_all_v2'][0]),str(choices['q2_vehicles'][0]),str(choices['q2_cost'][1]),str(int(choices['q2_cost'][0])),f"{z['raw_actual_seconds']+z['guard_seconds_from_summary']:.2f}"])
expected.append(er)
csv=a.readcsv(E/'experiments/experiments.csv');by={x.get('case',x.get('tag')):x for x in A['parameters']};er=[]
for r in csv:
 x=by[r['case']];m=x.get('metrics');er.append([r['parameter'],r['factor'],r['status'],str(m['vehicle_count']) if m else '-',str(m['cost_yuan']) if m else '-',f"{float(r['seconds']):.2f}"])
expected.append(er)
coords=[r for r in a.readcsv(E/'results/final/selected/q2_cost/placements.csv') if r['vehicle_id']=='T008'][:12]
expected.append([[r['item_id'],r['cargo_type'],r['x_mm'],r['y_mm'],r['z_mm'],r['orientation_id'],'×'.join(r[k] for k in ('dx_mm','dy_mm','dz_mm'))] for r in coords])
rows=[]
def eq(x,y):
 if x==y:return True
 try:return abs(float(x)-float(y))<1e-8
 except ValueError:return False
for ix,(table,exp) in enumerate(zip(tables,expected)):
 assert len(table)-1==len(exp),(ix,len(table),len(exp))
 for j,(got,want) in enumerate(zip(table[1:],exp)):rows.append({'table':ix+1,'row':j+1,'observed':got,'independent_expected':want,'matches':len(got)==len(want) and all(eq(g,w) for g,w in zip(got,want))})
figs=[{'name':p.name,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'regenerated_sha256':hashlib.sha256((O/'delivery_staged/figures'/p.name).read_bytes()).hexdigest(),'byte_match':p.read_bytes()==(O/'delivery_staged/figures'/p.name).read_bytes()} for p in sorted((E/'figures').glob('*.png'))]
costs={method:[r['q2_cost_cost'] for r in comp if r['method']==method] for method in ('A','B','C')};delta=[b-c for b,c in zip(costs['B'],costs['C'])]
stats={'B_to_C_paired_savings_yuan':delta,'mean_savings_yuan':sum(delta)/3,'mean_pair_percent':sum((b-c)/b*100 for b,c in zip(costs['B'],costs['C']))/3,'B_mean_seconds':sum(r['total_outer_seconds'] for r in comp if r['method']=='B')/3,'C_mean_seconds':sum(r['total_outer_seconds'] for r in comp if r['method']=='C')/3,'pressure_kg_m2':cost['max_pressure'],'minclear_mm':cost['min_clearance_mm'],'density_quantized_load_upper':{k:187.5*v['dims'][0]*v['dims'][1]*50*math.floor((v['dims'][2]-v['clearance'])/50)/1e9/v['payload'] for k,v in VS.items()}}
dump(O/'paper-numeric-audit.json',{'source':'7 actual frozen manuscript tables compared against reviewer raw/geometry/candidate-pool arithmetic; historical elapsed times only bookkeeping not host-authenticated','table_rows':rows,'all_table_rows_match':all(x['matches'] for x in rows),'figures':figs,'all7_figures_byte_equal':all(x['byte_match'] for x in figs),'independent_stats':stats,'limits':['recorded research time is preserved original observation, not independently observable retrospective host telemetry','generated figures consume checked frozen records; separate fresh outcomes/variation in replay-audit'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'rows':len(rows),'mismatches':[r for r in rows if not r['matches']],'figures_equal':sum(x['byte_match'] for x in figs),'stats':stats},ensure_ascii=False))
