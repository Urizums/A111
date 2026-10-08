from pathlib import Path
import copy,json
from validate import validate
from main import readitems,typesfrom,pack,export,csvwrite,dump,ROOT
def item(i,cat='标准件',ds=(1000,1000,1000),w=100):return {'item_id':i,'cargo_type':i,'category':cat,'canonical_l_mm':ds[0],'canonical_w_mm':ds[1],'canonical_h_mm':ds[2],'weight_kg':w}
def place(s,x=0,y=0,z=0):return {'vehicle_id':'T1','vehicle_type':'V1','item_id':s['item_id'],'cargo_type':s['cargo_type'],'x_mm':x,'y_mm':y,'z_mm':z,'dx_mm':s['canonical_l_mm'],'dy_mm':s['canonical_w_mm'],'dz_mm':s['canonical_h_mm'],'orientation_id':'012'}
v=[{'type_id':'V1','dims':[4000,3000,4030],'payload_kg':6000,'cost_yuan_per_trip':450,'clearance_mm':30}];tests=[]
def test(name,ss,pp,expect=True,**kw):
 z=validate(pp,ss,v,**kw);tests.append({'name':name,'expected_valid':expect,'actual_valid':z['valid'],'passed':z['valid']==expect,'errors':z['errors']});assert z['valid']==expect,(name,z['errors'])
a=item('a');b=item('b');test('tangent_legal',[a,b],[place(a),place(b,x=1000)])
test('overlap_1mm_reject',[a,b],[place(a),place(b,x=999)],False)
test('clearance_equal_legal',[a],[place(a,z=0)])
aa=item('a',ds=(1000,1000,4000));test('top_gap_exact_legal',[aa],[place(aa)])
pp=place(aa);pp['dz_mm']+=1;test('overheight_reject',[aa],[pp],False)
di=item('di','定向件',ds=(1000,500,1000));pp=place(di);pp['orientation_id']='102';pp['dx_mm'],pp['dy_mm']=500,1000;test('direction_reject',[di],[pp],False)
f=item('f','易碎件');test('fragile_on_floor_legal',[f],[place(f)])
test('fragile_gap_reject',[a,f],[place(a),place(f,x=1,z=1000)],False)
test('fragile_directional_support_reject',[di,f],[place(di),place(f,z=1000)],False)
test('fragile_top_load_reject',[f,a],[place(f),place(a,z=1000)],False)
test('duplicate_reject',[a],[place(a),place(a,x=1000)],False)
test('omission_reject',[a,b],[place(a)],False)
bad=copy.deepcopy(a);bad['weight_kg']='';test('missing_weight_reject',[bad],[place(a)],False)
bottom=item('bottom',ds=(1000,1000,1000),w=100);mid=item('mid',w=300);top=item('top',w=300)
test('cumulative_600kg_per_m2_reject',[bottom,mid,top],[place(bottom),place(mid,z=1000),place(top,z=2000)],False)
top['weight_kg']=200;test('pressure_equal_500_legal',[bottom,mid,top],[place(bottom),place(mid,z=1000),place(top,z=2000)])
left=item('left',ds=(500,1000,1000),w=100);right=item('right',ds=(500,1000,1000),w=100);ff=item('frag','易碎件',w=150)
test('union_standard_support_legal',[left,right,ff],[place(left),place(right,x=500),place(ff,z=1000)])
dump(ROOT/'checks/boundary_tests.json',tests)
items=readitems(ROOT/'data/items.csv');sm=[]
for t in ['G1','G2','G3','G4','G5']:sm.extend([r for r in items if r['cargo_type']==t][:3])
ts=typesfrom(sm);vs=json.loads((ROOT/'data/vehicles.json').read_text(encoding='utf8'));p=pack(ts,vs[0],[3]*5,[1]*5,{'pressure':500});export([p],ts,[vs[0]],sm,ROOT/'checks/smoke','smoke',{'config':{'pressure':500},'objective':'feasibility'})
print(json.dumps({'tests':len(tests),'passed':sum(t['passed'] for t in tests),'smoke_items':len(sm)}))

# Current C smoke, not only the inherited column constructor smoke.
p=pack(ts,vs[0],[3]*5,[1]*5,{'pressure':500,'geometry':'C'})
export([p],ts,[vs[0]],sm,ROOT/'checks/smoke_C','smoke_C',{'config':{'pressure':500,'geometry':'C'},'objective':'feasibility'})
# A real protected G5 grid is accepted; 1mm cross-base shift violates local center.
import blocks
fullts=typesfrom(items);cat=blocks.catalog(fullts,vs[1],{'pressure':500},__import__('main').orientations)
b=next(b for b in cat if b['tag']=='protected_directional' and b['counts'][4]>0)
lookup={t['cargo_type']:t for t in fullts};ii=[];rr=[]
for i,q in enumerate(b['placements']):
 t=lookup[q['cargo_type']];iid='H'+str(i);ii.append(item(iid,t['category'],t['dims'],t['weight']));ii[-1]['cargo_type']=t['cargo_type'];rr.append({'vehicle_id':'B','vehicle_type':'V2','item_id':iid,**q})
z=validate(rr,ii,[vs[1]]);assert z['valid'];bad=copy.deepcopy(rr);j=next(j for j,q in enumerate(bad) if lookup[q['cargo_type']]['category']=='标准件');bad[j]['x_mm']+=1
zz=validate(bad,ii,[vs[1]]);assert not zz['valid']
dump(ROOT/'checks/protected_block_controls.json',{'accepted_real_G5_block':z['valid'],'one_mm_cross_directional_support_rejected':not zz['valid'],'errors':zz['errors'],'legal_placements':rr,'mutated_placements':bad,'items':ii})
print('C smoke15 and real protected-block positive/negative controls passed')
