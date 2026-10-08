import json,time,copy
from pathlib import Path
from solve import columns,pack,save_scenario
from validator import validate
E=Path(__file__).resolve().parents[1];instance=json.loads((E/'data/instance.json').read_text(encoding='utf8'));cfg=json.loads((E/'configs/main.json').read_text(encoding='utf8'))
small=copy.deepcopy(instance)
for g,q in zip(small['cargo'],[3,4,1,2,2]):g['quantity']=q
ts=time.perf_counter();opts=columns(small,small['vehicles'][0],cfg);p=pack(small,small['vehicles'][0],cfg,opts,[g['quantity'] for g in small['cargo']],[1,1,1,1,1],'shelf',1904)
sm=save_scenario(E/'results','smoke',small,cfg,[p],time.perf_counter()-ts,{'claim':'official small slice'},True)
rows=[]
def add(g,serial,x,y,z,d,ori,support='FLOOR'):
 rows.append({'truck_id':'TR0001','vehicle_type':'T1','item_id':f'{g}-{serial:04d}','cargo_type':g,'x':x,'y':y,'z':z,'l':d[0],'w':d[1],'h':d[2],'orientation':ori,'support_ids':support})
for n in range(3):add('G1',n+1,0,0,30*n,[60,40,30],'LWH','FLOOR' if n==0 else f'G1-{n:04d}')
add('G3',1,0,0,90,[50,40,70],'WHL','G1-0003')
for n in range(4):add('G2',n+1,100,0,25*n,[50,35,25],'LWH','FLOOR' if n==0 else f'G2-{n:04d}')
for n in range(2):add('G4',n+1,200,0,50*n,[80,60,50],'LWH','FLOOR' if n==0 else f'G4-{n:04d}')
add('G5',1,200,0,100,[40,40,60],'LWH','G4-0002')
add('G5',2,300,0,0,[40,40,60],'LWH')
valid=validate(small,cfg,rows,True);assert valid['valid'],valid['errors']
tests=[]
def test(name,mutate,required):
 r=copy.deepcopy(rows);mutate(r);c=validate(small,cfg,r,True);assert not c['valid'] and any(required in e for e in c['errors']),(name,c['errors']);tests.append({'name':name,'rejected':True,'errors':c['errors']})
test('overlap',lambda r:r[4].update(x=0,z=0),'overlap')
test('oriented_flip',lambda r:r[8].update(l=60,w=80,orientation='WLH'),'orientation')
test('fragile_top',lambda r:r[4].update(x=0,z=160),'fragile_top')
test('unsupported_hole_or_extension',lambda r:r[3].update(x=20),'full_support')
test('safety_gap',lambda r:r[-1].update(z=180),'boundary')
cfgpressure=copy.deepcopy(cfg);cfgpressure['pressure_kg_m2']=10;c=validate(small,cfgpressure,rows,True);assert any('load' in e or 'pressure' in e for e in c['errors']);tests.append({'name':'cumulative_pressure','rejected':True,'errors':c['errors']})
tests.append({'name':'right_boundary_contact','accepted':validate(small,cfg,[dict(rows[0],x=360,y=170)],False)['valid']});assert tests[-1]['accepted']
result={'algorithm_slice':{k:sm[k] for k in ['inventory','UV','UW','cost','mass_kg','volume_cm3','elapsed_seconds']},'explicit_chain':valid,'controlled_defects':tests,'gate':'G1 passed; author self-check only'}
(E/'checks/smoke.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(E/'paper/smoke-fragment.md').write_text(f'''# 小切片数值链\n附件1五类取[3,4,1,2,2]，共12件，单车T1。程序实际输出体积{sm['volume_cm3']/1e6:.6f}m³、重量{sm['mass_kg']:.0f}kg、满容率{sm['UV']:.6%}、满载率{sm['UW']:.6%}。逐件数据见results/smoke/placements.csv。另构造G1三层承载G3及G4两层承载G5两层的有效链，并实际拒绝重叠、定向旋转、压易碎件、不完整支撑、3cm间隙违规和累计承重违规。该检查只说明小路径和拒绝机制有效，不证明全量或最优性。\n''',encoding='utf8')
print({'seconds':time.perf_counter()-ts,'options':len(opts),'UV':sm['UV'],'UW':sm['UW'],'tests':len(tests)})
