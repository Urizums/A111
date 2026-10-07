import json,itertools,copy
from solve import ROOT,DEFAULT,validate_config
from check import check_fleet
cfg=copy.deepcopy(DEFAULT);cfg['directional_center_each']=True
types={c['id']:c for c in cfg['cargo']}
def item(t,k,x=0,y=0,z=0,dims=None):
 c=types[t];dims=dims or c['dims'];p=next(list(p) for p in itertools.permutations(range(3)) if [c['dims'][j] for j in p]==dims)
 return dict(item_id=f'{t}-{k:04d}',type_id=t,x=x,y=y,z=z,dx=dims[0],dy=dims[1],dz=dims[2],weight=c['weight'],category=c['category'],orientation=p)
def check(name,items,expected,rule=None,change=None,complete=False):
 c=copy.deepcopy(cfg)
 if change:change(c)
 v=copy.deepcopy(c['vehicles'][0]);r=check_fleet([dict(vehicle=v,vehicle_type=v['id'],truck_id='V001',items=items)],c,complete)
 observed={e['rule'] for e in r['errors']};ok=(r['valid']==expected) and(rule is None or rule in observed)
 records.append(dict(name=name,expected_valid=expected,observed_valid=r['valid'],expected_rule=rule,observed_rules=sorted(observed),test_pass=ok))
records=[]
check('exact floor contact',[item('G1',1),item('G1',2,x=60)],True)
check('positive overlap .01cm',[item('G1',1),item('G1',2,x=59.99)],False,'overlap')
check('rotated boundary',[item('G1',1,y=180,dims=[30,60,40])],False,'boundary_clearance')
check('missing 3cm top gap',[item('G5',1,z=160)],False,'boundary_clearance')
check('payload exceeded',[item('G1',1)],False,'payload',lambda c:c['vehicles'][0].update(payload=10))
check('duplicate ID',[item('G1',1),item('G1',1,x=60)],False,'duplicate_ids')
check('missing entire inventory',[],False,'inventory_conservation',complete=True)
check('directional rotated',[item('G4',1,dims=[60,80,50])],False,'orientation')
check('fragile compressed',[item('G3',1),item('G1',1,z=40)],False,'fragile_loaded')
check('gap under fragile',[item('G2',1,dims=[35,50,25]),item('G2',2,x=40,dims=[35,50,25]),item('G3',1,z=25)],False,'support_gap')
check('noncoplanar support',[item('G2',1,dims=[35,50,25]),item('G1',1,x=35,dims=[40,60,30]),item('G3',1,z=30)],False,'support_gap')
check('cumulative high stack',[item('G5',1),item('G5',2,z=60),item('G5',3,z=120)],False,'cumulative_bearing',lambda c:c.update(bearing=200))
check('direct contact COM outside',[item('G4',1),item('G4',2,x=80),item('G1',1,x=49,z=50)],False,'directional_contact_center')
check('inventory overflow',[item('G1',1),item('G1',2,x=60)],False,'inventory_conservation',lambda c:c['cargo'][0].update(quantity=1))
try:
 validate_config({'cargo':[{'id':'A2','dims':[30.1,30.1,34.7]}],'vehicles':cfg['vehicles'],'bearing':500});accepted=True
except ValueError as e:accepted=False;reason=str(e)
records.append({'name':'attachment2 missing business fields','test_pass':not accepted,'observed_reason':reason})
(ROOT/'review/boundary_tests.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print('Boundary tests',sum(x['test_pass'] for x in records),'/',len(records))
if not all(x['test_pass'] for x in records):raise RuntimeError(records)
