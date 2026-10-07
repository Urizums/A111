"""Independent disclosed F1 + raw-bound adjacent tests; not author 68-case replay."""
from independent_audit import OUT,ROOT,raw_config,audit
import copy,json,sys,math,re,itertools,datetime
sys.path.insert(0,str(OUT/'sandbox/runs/R19/levels/L1/execution-v2/src'))
from check import check_fleet
BASE=raw_config();records=[];CASES=[]
old=json.loads((OUT.parent/'initial/independent-boundary-tests.json').read_text(encoding='utf-8'))
for t in old['tests']:
    CASES.append((t['name'],copy.deepcopy(t['input']),t['expected_valid'],t['name']=='missing full inventory'))
def item(cid,k=1,x=0,y=0,z=0,dims=None):
    c=next(c for c in BASE['cargo'] if c['id']==cid);ds=dims or c['dims'];ori=next(list(o) for o in itertools.permutations(range(3)) if [c['dims'][j] for j in o]==list(ds))
    return {'item_id':f'{cid}-{k:04d}','type_id':cid,'truck_id':'test','x':x,'y':y,'z':z,'dx':ds[0],'dy':ds[1],'dz':ds[2],'weight':c['weight'],'category':c['category'],'orientation':ori}
def fixture(items):return {'config':copy.deepcopy(BASE),'fleet':[{'truck_id':'test','vehicle_type':'T1','vehicle':copy.deepcopy(BASE['vehicles'][0]),'items':items}]}
def add(name,d,expected=False,mutate=None):
    d=copy.deepcopy(d)
    if mutate:mutate(d)
    CASES.append((name,d,expected,False))
floor=fixture([item('G3')]);standard=fixture([item('G1')])
add('valid fragile on floor',floor,True)
add('valid fragile on coplanar two standard supports',fixture([item('G2',dims=[35,50,25]),item('G2',2,x=35,dims=[35,50,25]),item('G3',z=25)]),True)
add('valid directional floor',fixture([item('G4')]),True)
for cid in ['G1','G2','G3','G4','G5']:
    for category in ['standard','fragile','directional']:
        if category==next(c for c in BASE['cargo'] if c['id']==cid)['category']:continue
        add(f'{cid} output category changed to {category}',fixture([item(cid)]),mutate=lambda d,cat=category:d['fleet'][0]['items'][0].update(category=cat))
    add(cid+' config source category changed',fixture([item(cid)]),mutate=lambda d,cid=cid:next(c for c in d['config']['cargo'] if c['id']==cid).update(category='standard' if cid in ['G3','G4','G5'] else 'fragile'))
add('source relabel conceals directional contact centroid',fixture([item('G4'),item('G4',2,x=80),item('G1',x=49,z=50)]),mutate=lambda d:d['fleet'][0]['items'][0].update(category='standard'))
add('source relabel makes directional support appear standard for fragile',fixture([item('G4'),item('G3',z=50)]),mutate=lambda d:d['fleet'][0]['items'][0].update(category='standard'))
for field,value in [('category',None),('weight',None),('weight',float('nan')),('weight',float('inf')),('weight',True),('weight',0),('type_id','G9'),('item_id','G3-0001'),('item_id','G1-0000'),('item_id','G1-0801'),('item_id','G1-00001'),('item_id',None),('orientation',[0,0,2]),('orientation',[True,1,2]),('orientation',None),('truck_id','other')]:
    add('invalid item '+field+'='+repr(value),standard,mutate=lambda d,k=field,v=value:d['fleet'][0]['items'][0].update({k:v}))
for field in ['x','y','z','dx','dy','dz']:
    for value in [float('nan'),float('inf'),-float('inf')]:
        add('nonfinite item '+field+'='+repr(value),standard,mutate=lambda d,k=field,v=value:d['fleet'][0]['items'][0].update({k:v}))
for key,value in [('payload',1e8),('dims',[1e8,1e8,1e8]),('cost',1),('id','T2')]:
    add('vehicle header mismatch '+key,standard,mutate=lambda d,k=key,v=value:d['fleet'][0]['vehicle'].update({k:v}))
for key,value in [('bearing',float('nan')),('clearance',float('inf')),('directional_center_each',1)]:
    add('nonfinite or invalid source '+key,standard,mutate=lambda d,k=key,v=value:d['config'].update({k:v}))
add('duplicate source cargo identity',standard,mutate=lambda d:d['config']['cargo'].append(copy.deepcopy(d['config']['cargo'][0])))
add('unknown source vehicle identity',standard,mutate=lambda d:d['config']['vehicles'][0].update(id='T9'))
add('valid declared numerical mass scenario',standard,True,lambda d:(d['config']['cargo'][0].update(weight=13),d['fleet'][0]['items'][0].update(weight=13)))
add('valid declared dimensional scenario',standard,True,lambda d:(d['config']['cargo'][0].update(dims=[60,40,29]),d['fleet'][0]['items'][0].update(dz=29)))
add('valid declared inventory scenario',standard,True,lambda d:d['config']['cargo'][0].update(quantity=1))
add('valid fixed-type scenario',standard,True,lambda d:d['config'].update(vehicles=[d['config']['vehicles'][0]]))
add('valid declared vehicle scenario',standard,True,lambda d:(d['config']['vehicles'][0].update(payload=5500,cost=300),d['fleet'][0]['vehicle'].update(payload=5500,cost=300)))

def finite(x):return type(x) in [int,float] and math.isfinite(x)
def own_source_gate(d):
    """Independent raw category identity/finite intake; numeric scenarios allowed."""
    reasons=[];cfg=d['config'];cs=cfg['cargo'];vs=cfg['vehicles'];raw={c['id']:c for c in BASE['cargo']}
    if len(cs)!=5 or {c.get('id') for c in cs}!=set(raw):reasons.append('source_cargo_identities')
    for c in cs:
        if c.get('id') not in raw or c.get('category')!=raw[c['id']]['category']:reasons.append('source_category_identity')
        if len(c.get('dims',[]))!=3 or any(not finite(x) or x<=0 for x in c.get('dims',[])):reasons.append('source_dimensions')
        if not finite(c.get('weight')) or c['weight']<=0:reasons.append('source_weight')
        if type(c.get('quantity'))!=int or c['quantity']<0:reasons.append('source_quantity')
    if not vs or len({v.get('id') for v in vs})!=len(vs) or not {v.get('id') for v in vs}<={'T1','T2'}:reasons.append('source_vehicle_identities')
    for v in vs:
        if len(v.get('dims',[]))!=3 or any(not finite(x) or x<=0 for x in v.get('dims',[])):reasons.append('source_vehicle_dimensions')
        if any(not finite(v.get(k)) or v[k]<=0 for k in ['payload','cost']):reasons.append('source_vehicle_parameters')
    for k in ['clearance','bearing']:
        if not finite(cfg.get(k)) or cfg[k]<0 or(k=='bearing' and cfg[k]==0):reasons.append('source_'+k)
    for k in ['fragile_rotation','fragile_floor_only','directional_center_each']:
        if k in cfg and type(cfg[k])!=bool:reasons.append('source_rule_flag')
    if reasons:return reasons,False
    types={c['id']:c for c in cs};can_audit=True
    for t in d['fleet']:
        for i in t['items']:
            cid=i.get('type_id');iid=i.get('item_id')
            if cid not in types:reasons.append('item_type_identity');can_audit=False;continue
            if not isinstance(iid,str) or not re.fullmatch(cid+r'-\d{4,}',iid):reasons.append('item_id_identity');can_audit=False
            elif len(iid.split('-')[1])>max(4,len(str(types[cid]['quantity']))) or not 1<=int(iid.split('-')[1])<=types[cid]['quantity'] or iid!=f'{cid}-{int(iid.split("-")[1]):04d}':reasons.append('item_id_inventory')
            if i.get('category')!=types[cid]['category']:reasons.append('item_category_source')
            if not finite(i.get('weight')) or i['weight']!=types[cid]['weight']:reasons.append('item_weight_source')
            if any(not finite(i.get(k)) for k in ['x','y','z','dx','dy','dz']) or any(i[k]<=0 for k in ['dx','dy','dz'] if finite(i.get(k))):reasons.append('item_geometry_finite');can_audit=False
            o=i.get('orientation')
            if not isinstance(o,list) or len(o)!=3 or any(type(x)!=int for x in o) or sorted(o)!=[0,1,2]:reasons.append('item_orientation_schema');can_audit=False
            if 'truck_id' in i and i['truck_id']!=t['truck_id']:reasons.append('item_truck_assignment')
    return reasons,can_audit
for name,d,expected,complete in CASES:
    reasons,safe=own_source_gate(d);physical=None
    if safe:
        try:physical,_=audit(d,name,complete,d['config']);reasons+=['physical:'+x['code'] for x in physical['violations']]
        except Exception as e:reasons.append('own_audit_exception:'+repr(e))
    own_valid=not reasons
    before=json.dumps(d,sort_keys=True)
    try:r=check_fleet(d['fleet'],d['config'],complete);accepted=r['valid'];errors=r['errors'];exception=None
    except Exception as e:accepted=False;errors=[];exception=repr(e)
    mutated=before!=json.dumps(d,sort_keys=True)
    records.append({'name':name,'expected_valid':expected,'complete':complete,'independent_valid':own_valid,'independent_reasons':reasons,'revised_valid':accepted,'revised_errors':errors,'revised_exception':exception,'input_mutated':mutated,'independent_matches_expected':own_valid==expected,'revised_matches_expected':accepted==expected,'input':d})
report={'informed_re_review':True,'frozen_initial_cases_reused':15,'test_count':len(records),'independent_expected_matches':sum(r['independent_matches_expected'] for r in records),'revised_expected_matches':sum(r['revised_matches_expected'] for r in records),'all_inputs_unmutated':all(not r['input_mutated'] for r in records),'structured_results_without_exceptions':all(r['revised_exception'] is None for r in records),'tests':records,'source':'own initial15 witnesses and independent raw-bound adjacent controls; author68 report not read before this test','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/'independent-source-boundary-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='tests'},ensure_ascii=False));print('mismatches',[(r['name'],r['independent_reasons'],r['revised_errors'],r['revised_exception']) for r in records if not r['revised_matches_expected'] or not r['independent_matches_expected'] or r['input_mutated']])
