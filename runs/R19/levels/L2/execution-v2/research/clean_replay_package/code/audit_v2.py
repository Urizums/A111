"""Source XML reconciliation and independent geometry/metric path, same author context."""
from pathlib import Path
import csv,json,math,itertools,zipfile,xml.etree.ElementTree as ET,time,hashlib,collections,re
from validate import validate
R=Path(__file__).resolve().parents[1]
def rd(p):
 with Path(p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def metrics(folder,items):
 run=json.loads((folder/'run.json').read_text());vs=json.loads((folder/'vehicles.json').read_text());rows=rd(folder/'placements.csv');cfg=run['config']
 z=validate(rows,items,vs,run['full_inventory'],cfg.get('pressure',500),cfg.get('fragile_fixed',False));assert z['valid'],(folder,z['errors'][:5])
 assert len(z['vehicles'])==run['vehicle_count'];assert sum(a['cost_yuan'] for a in z['vehicles'])==run['cost_yuan']
 vv={v['type_id']:v for v in vs};u=sum(a['volume_mm3'] for a in z['vehicles'])/sum(math.prod(vv[a['vehicle_type']]['dims']) for a in z['vehicles']);w=sum(a['weight_kg'] for a in z['vehicles'])/sum(vv[a['vehicle_type']]['payload_kg'] for a in z['vehicles']);assert abs(u-run['volume_utilization'])<1e-12 and abs(w-run['weight_utilization'])<1e-12
 if cfg.get('fragile_floor'):assert all(float(a['z_mm'])==0 for a in rows if a['cargo_type']=='G3')
 return {'folder':folder.relative_to(R).as_posix(),'items':len(rows),'vehicles':len(z['vehicles']),'cost':run['cost_yuan'],'valid':True,'metrics_match':True}
if __name__=='__main__':
 start=time.perf_counter();items=rd(R/'data/items.csv');ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 with zipfile.ZipFile(R/'raw/附件1.docx') as f:x=ET.fromstring(f.read('word/document.xml'))
 rows=x.find('.//w:tbl',ns).findall('w:tr',ns);source=[]
 for row in rows[1:]:
  cells=[''.join(c.itertext()) for c in []] # XML text only, no normalizer import.
  cells=[''.join(n.text or '' for n in c.findall('.//w:t',ns)) for c in row.findall('w:tc',ns)]
  ds=[int(a)*10 for a in cells[2].split('×')];t={'type':cells[0],'category':cells[1],'dims':ds,'weight':float(cells[3]),'quantity':int(cells[4])};source.append(t)
  rr=[a for a in items if a['cargo_type']==t['type']];assert len(rr)==t['quantity']
  assert all(a['category']==t['category'] and float(a['weight_kg'])==t['weight'] and [float(a['canonical_'+k+'_mm']) for k in ['l','w','h']]==ds for a in rr)
 assert len(items)==len({a['item_id'] for a in items})==3000
 V=sum(math.prod(t['dims'])*t['quantity'] for t in source);M=sum(t['weight']*t['quantity'] for t in source)
 heights=[]
 for t in source:
  ps=[(0,1,2)] if t['category']=='定向件' else [(0,1,2),(1,0,2)] if t['category']=='易碎件' else itertools.permutations(range(3))
  heights.extend(t['dims'][p[2]] for p in ps)
 q=math.gcd(*heights);vs=json.loads((R/'data/vehicles.json').read_text());paras=[''.join(n.text or '' for n in p.findall('.//w:t',ns)) for p in x.findall('.//w:body/w:p',ns)]
 for j,o in enumerate([3,7]):
  assert vs[j]['dims']==[int(a)*10 for a in re.findall(r'(\d+)cm',paras[o])]
  assert vs[j]['payload_kg']==int(re.search(r'(\d+)kg',paras[o+1]).group(1))
  assert vs[j]['cost_yuan_per_trip']==int(re.search(r'(\d+)\s*元',paras[o+2]).group(1))
 cap=[v['dims'][0]*v['dims'][1]*(q*((v['dims'][2]-v['clearance_mm'])//q)) for v in vs]
 pairs=[(a,b) for a in range(51) for b in range(51) if a*cap[0]+b*cap[1]>=V and a*vs[0]['payload_kg']+b*vs[1]['payload_kg']>=M]
 bounds=[max(math.ceil(V/c),math.ceil(M/v['payload_kg'])) for c,v in zip(cap,vs)]+[min(a+b for a,b in pairs),min(a*450+b*700 for a,b in pairs)]
 assert bounds==[16,8,8,5350];checks=[]
 for folder in sorted((R/'results/final').glob('*/*')):
  if (folder/'run.json').exists():checks.append(metrics(folder,items))
 for p in sorted((R/'experiments').glob('*/run.json')):checks.append(metrics(p.parent,rd(p.parent/'items.csv')))
 # Source parameters independently reconstructed, without importing mutation program.
 exps=rd(R/'experiments/experiments.csv');mutation=[]
 for e in exps:
  d=R/'experiments'/e['case'];rr=rd(d/'items.csv');vv=json.loads((d/'vehicles.json').read_text());cfg=json.loads((d/'config.json').read_text());key=e['parameter'];factor=e['factor'];f=float(factor) if key!='interaction' else None
  for j,t in enumerate(source):
   expected=t['quantity'];scale=1.;weight=t['weight']
   if key=='quantity':expected=round(expected*f)
   if key=='dense_share':expected=round(expected*(f if t['type'] in ['G1','G2','G5'] else 2-f))
   if key=='cargo_size':scale=f
   if key=='cargo_weight':weight*=f
   sub=[a for a in rr if a['cargo_type']==t['type']];assert len(sub)==expected
   assert all(a['category']==t['category'] and [float(a['canonical_'+k+'_mm']) for k in ['l','w','h']]==[round(z*scale) for z in t['dims']] and abs(float(a['weight_kg'])-weight)<1e-9 for a in sub)
  expected_vs=json.loads((R/'data/vehicles.json').read_text());cf=500.;fixed=False;floor=False
  for j,v in enumerate(expected_vs):
   if key.startswith('vehicle_'):k={'vehicle_length':0,'vehicle_width':1,'vehicle_height':2}[key];v['dims'][k]=round(v['dims'][k]*f)
   if key=='payload':v['payload_kg']*=f
   if key=='clearance':v['clearance_mm']*=f
   if key=='cost_v1' and j==0 or key=='cost_v2' and j==1:v['cost_yuan_per_trip']*=f
   if key=='interaction':a,b=__import__('ast').literal_eval(factor);v['dims'][1]=round(v['dims'][1]*a);v['cost_yuan_per_trip']*=b if j==0 else 1
  assert vv==expected_vs
  if key=='pressure':cf*=f
  assert cfg['pressure']==cf and bool(cfg.get('fragile_fixed'))==(key=='fragile_fixed') and bool(cfg.get('fragile_floor'))==(key=='fragile_floor')
  mutation.append({'case':e['case'],'all_fields_match_source_mutation':True,'status':e['status']})
  if e['status']=='validated':run=json.loads((d/'run.json').read_text());assert int(e['vehicles'])==run['vehicle_count'] and float(e['cost_yuan'])==run['cost_yuan']
  else:assert (d/'failure.json').exists()
 # Recheck every actual saved single point against current candidate set.
 patterns=json.loads((R/'results/final/pattern_library.json').read_text());ts=json.loads((R/'data/types.json').read_text());singles=json.loads((R/'results/final/summary.json').read_text())['singles'];dominance=[]
 for r in singles:
  v=next(v for v in vs if v['type_id'] in r['scenario']);dom=[]
  for pat in patterns:
   if pat['vehicle_type']!=v['type_id']:continue
   u=sum(c*math.prod(t['dims']) for c,t in zip(pat['counts'],ts))/math.prod(v['dims']);w=sum(c*t['weight'] for c,t in zip(pat['counts'],ts))/v['payload_kg']
   if u>=r['volume_utilization']-1e-10 and w>=r['weight_utilization']-1e-10 and (u>r['volume_utilization']+1e-10 or w>r['weight_utilization']+1e-10):dom.append(pat['counts'])
  assert not dom;dominance.append({'scenario':r['scenario'],'not_dominated_by_library':True})
 # Exact-inventory known-fleet protection regression from observed bad incumbents.
 import main,blocks
 from guard_comparison import rows_to_fleet
 cd=R/'research/comparison/C_seed19'
 bad=rows_to_fleet(cd/'selected/q2_cost',main.typesfrom(main.readitems(R/'data/items.csv')))
 good=rows_to_fleet(cd/'selected/q2_vehicles',main.typesfrom(main.readitems(R/'data/items.csv')))
 cs=[t['quantity'] for t in source]
 assert main.best_known([bad,good],vs,cs,'cost')[1]==1
 v2good=rows_to_fleet(cd/'selected/q1_all_v2',main.typesfrom(main.readitems(R/'data/items.csv')))
 assert len(main.best_known([good,v2good],vs,cs,'vehicles')[0])==12
 # Recreate full template certificates for every parameter configuration; no new MILP.
 certificates=[]
 for e in exps:
  d=R/'experiments'/e['case'];cfg=json.loads((d/'config.json').read_text());rr=main.readitems(d/'items.csv');tt=main.typesfrom(rr);vv=json.loads((d/'vehicles.json').read_text());blocks.CACHE.clear();blocks.CERTIFICATES.clear()
  for v in vv:blocks.catalog(tt,v,cfg,main.orientations)
  certificates.append({'case':e['case'],'kind':'post-run deterministic template certification replay, not original telemetry','records':list(blocks.CERTIFICATES)})
 dump(R/'checks/parameter_block_certificates.json',certificates)
 out={'source_reconciliation':'raw DOCX XML independently parsed','source_rows':source,'total_volume_mm3':V,'total_mass_kg':M,'q_mm':q,'capacity_mm3':cap,'bounds':bounds,'all_outputs':checks,'parameter_input_mutations':mutation,'single_dominance':dominance,'guard_regression_pass':True,'seconds':time.perf_counter()-start,'independence':'author same context, separate parser/validator code; informed external rereview pending'};dump(R/'checks/source_result_audit.json',out)
 print(json.dumps({'runs':len(checks),'parameter_inputs':len(mutation),'bounds':bounds,'seconds':out['seconds']}))
