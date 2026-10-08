from pathlib import Path
import sys,json,math,copy,collections,datetime,time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from types import SimpleNamespace
from audit_independent import a,O,E,B,ITEMS,VS,CFG,pat,bound,physical_fleet,fleet_key
from run_calls import dump
sys.path.insert(0,str(O/'zip_staged/code'))
import main,blocks
types=[{'cargo_type':t,'category':{'standard':'标准件','fragile':'易碎件','directional':'定向件'}[i['category']],'dims':list(map(int,i['dims'])),'weight':i['weight'],'count':i['count']} for t,i in a.CAT.items()]
vs=[{'type_id':k,'dims':list(map(int,v['dims'])),'payload_kg':v['payload'],'cost_yuan_per_trip':v['cost'],'clearance_mm':v['clearance']} for k,v in VS.items()]
config={'seed':19,'starts':22,'time_limit':45,'pressure':500,'geometry':'C','platforms':True}
st=time.perf_counter();cert=[];chosen=None
for v in vs:
 ps=blocks.catalog(types,v,config,main.orientations)
 checks=[pat({'vehicle_type':v['type_id'],**p}) for p in ps]
 cert.append({'vehicle_type':v['type_id'],'count':len(ps),'all_reviewer_valid':all(p['valid'] and p['reported_counts_match'] for p in checks),'invalid':[p for p in checks if not p['valid']]})
 if chosen is None:chosen=next({'vehicle_type':v['type_id'],**p} for p in ps if p['tag']=='protected_directional')

lookup={i['cargo']:i for i in ITEMS.values()}
def target_check(p,alter=None):
 its=[];rows=[];mine={};placements=[]
 for ix,q in enumerate(p['placements']):
  i=lookup[q['cargo_type']];iid=str(ix);it={'item_id':iid,'cargo_type':i['cargo'],'category':{'standard':'标准件','fragile':'易碎件','directional':'定向件'}[i['category']],'canonical_l_mm':i['dims'][0],'canonical_w_mm':i['dims'][1],'canonical_h_mm':i['dims'][2],'weight_kg':i['weight']};its.append(it);r={'vehicle_id':'T','vehicle_type':p['vehicle_type'],'item_id':iid,**q};rows.append(r)
 if alter:alter(its,rows)
 for i,r in zip(its,rows):
  mine[i['item_id']]={'dims':[i[k] for k in ('canonical_l_mm','canonical_w_mm','canonical_h_mm')],'weight':i['weight_kg'],'category':lookup[i['cargo_type']]['category'],'cargo':i['cargo_type']};placements.append({'item_id':i['item_id'],'vehicle_id':'T','xyz':[r[k] for k in ('x_mm','y_mm','z_mm')],'dims':[r[k] for k in ('dx_mm','dy_mm','dz_mm')],'cargo':i['cargo_type']})
 reviewer=a.validate_layout(mine,{'T':VS[p['vehicle_type']]},placements,full_support_all=True,pressure_limit=500)
 from validate import validate
 producer=validate(rows,its,vs,True,500,False)
 return {'reviewer_valid':reviewer['valid'],'reviewer_errors':reviewer['errors'],'target_valid':producer['valid'],'target_errors':producer['errors'],'fixture_items':its,'fixture_placements':rows}
controls=[]
controls.append({'id':'certified_directional_standard_fragile','expected':True,**target_check(chosen)})
def shift(its,rows):
 r=next(r for r in rows if r['cargo_type']=='G3');r['x_mm']+=300
controls.append({'id':'fragile_support_shift300','expected':False,**target_check(chosen,shift)})
def overload(its,rows):
 for i in its:
  if i['cargo_type']=='G1':i['weight_kg']=300
controls.append({'id':'directional_base_cumulative_overpressure','expected':False,**target_check(chosen,overload)})
def atop(its,rows):
 f=next(r for r in rows if r['cargo_type']=='G3');s=next(r for r in rows if r['cargo_type']=='G1');s.update(x_mm=f['x_mm'],y_mm=f['y_mm'],z_mm=f['z_mm']+f['dz_mm'])
controls.append({'id':'standard_load_on_fragile','expected':False,**target_check(chosen,atop)})

ps=json.loads((E/'results/final/pattern_library.json').read_text());counts=np.array([i['count'] for i in a.CAT.values()]);matrix=np.array([[sum(q['cargo_type']==t for q in p['placements']) for p in ps] for t in a.CAT]);objrecords=[]
for name,allowed,objective in [('v1',{'V1'},'vehicles'),('v2',{'V2'},'vehicles'),('mixed',set(VS),'vehicles'),('cost',set(VS),'cost')]:
 ix=[j for j,p in enumerate(ps) if p['vehicle_type'] in allowed];A=matrix[:,ix];cost=np.array([VS[ps[j]['vehicle_type']]['cost'] for j in ix]);c=cost if objective=='cost' else np.ones(len(ix));ub=np.array([min(counts[k]//A[k,j] for k in range(5) if A[k,j]>0) for j in range(len(ix))]);begin=time.perf_counter()
 r=milp(c,integrality=np.ones(len(ix)),bounds=Bounds(np.zeros(len(ix)),ub),constraints=LinearConstraint(A,counts,counts),options={'time_limit':60,'mip_rel_gap':0});nr=np.rint(r.x).astype(int) if r.x is not None else None
 objrecords.append({'scenario':name,'objective':objective,'actual_status':int(r.status),'message':r.message,'actual_seconds':time.perf_counter()-begin,'limit_seconds':60,'independent_incumbent':float(c@nr) if nr is not None else None,'dual_bound':float(r.mip_dual_bound) if nr is not None else None,'gap':float(r.mip_gap) if nr is not None else None,'matrix_inventory_equality':nr is not None and np.array_equal(A@nr,counts),'scope':'only independently recounted physical pattern library; no original3D optimal claim'})
 print(json.dumps(objrecords[-1]),flush=True)

single=[];nd={}
for v in vs:
 candidates=[]
 for alpha in np.linspace(0,1,11):
  w=np.array([alpha*math.prod(t['dims'])/math.prod(v['dims'])+(1-alpha)*t['weight']/v['payload_kg'] for t in types]);p=main.pack(types,v,counts,w,config);z=pat(p);single.append({'vehicle':v['type_id'],'alpha':float(alpha),'valid':z['valid'],'counts':z['counts']});candidates.append(p)
 candidates += [p for p in ps if p['vehicle_type']==v['type_id']]
 vectors={tuple(p['counts']) for p in candidates};points=[(sum(n*math.prod(t['dims']) for n,t in zip(c,types))/math.prod(v['dims']),sum(n*t['weight'] for n,t in zip(c,types))/v['payload_kg'],c) for c in vectors]
 nd[v['type_id']]=[p[2] for p in points if not any(q[0]>=p[0]-1e-10 and q[1]>=p[1]-1e-10 and (q[0]>p[0]+1e-10 or q[1]>p[1]+1e-10) for q in points)]

# Targeted control of the cross-objective side effect, with actual valid full fleets; fake time-limit result is labelled control, never empirical solver evidence.
cheap=physical_fleet(E/'results/final/selected/q2_cost');small=physical_fleet(E/'results/final/selected/q2_vehicles');indices={(p['vehicle_type'],tuple(p['counts'])):j for j,p in enumerate(ps)};x=np.zeros(len(ps))
for p in cheap:x[indices[(p['vehicle_type'],tuple(p['counts']))]]+=1
old=main.milp;pool=[small]
try:
 main.milp=lambda *args,**kwargs:SimpleNamespace(x=x,status=1,message='controlled time-limit incumbent',mip_gap=.1,mip_dual_bound=0)
 selected,info=main.select(ps,vs,counts.tolist(),'vehicles',45,pool);hascheap=any(fleet_key(f,'cost')==(7850,13) for f in pool)
 main.milp=lambda *args,**kwargs:SimpleNamespace(x=None,status=1,message='controlled no incumbent')
 costselected,info2=main.select(ps,vs,counts.tolist(),'cost',45,pool)
 guardcontrol={'source':'real independently checked13/7850 and12/8400 fleets; mocked solver returns explicitly labelled', 'vehicles_choice':fleet_key(selected,'vehicles'),'raw_cheaper_incumbent_retained':hascheap,'next_cost_choice':fleet_key(costselected,'cost'),'actual_control_pass':fleet_key(selected,'vehicles')==(12,8400) and hascheap and fleet_key(costselected,'cost')==(7850,13)}
finally:main.milp=old
theory={'q_original':bound(ITEMS,VS,'cost')['height_quantum_mm'],'q_size_0_9':bound(*a.expected({'parameter':'cargo_size','factor':'0.9'})[:2],'cost')['height_quantum_mm'],'q_size_1_1':bound(*a.expected({'parameter':'cargo_size','factor':'1.1'})[:2],'cost')['height_quantum_mm'],'continuous_translation_control':'vertical segment lengths unchanged under arbitrary non-grid x/y/z translation; non-overlapping segment sum remains q-multiple even with gaps','proof_valid_for_wider_partial_support':True,'not_valid_for_nonorthogonal_rotation':True}
dump(O/'new-controls-objectives.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all1176_blocks':cert,'controls':controls,'independent_library_MILP':objrecords,'single22_actual_candidates':single,'independent_search_nondominated_counts':nd,'guard_control':guardcontrol,'theory_controls':theory,'seconds':time.perf_counter()-st})
print(json.dumps({'blocks':cert,'controls':[(x['id'],x['expected'],x['reviewer_valid'],x['target_valid']) for x in controls],'ND':nd,'guard':guardcontrol,'seconds':time.perf_counter()-st},ensure_ascii=False),flush=True)
