"""Informed author regression; disclosed cases are not blind acceptance."""
import copy,itertools,json,time
from solve import ROOT,DEFAULT
from check import check_fleet


def run():
    started=time.perf_counter();tests=[]
    cfg=copy.deepcopy(DEFAULT);cfg['directional_center_each']=True
    types={c['id']:c for c in cfg['cargo']}
    def item(t,k=1,x=0,y=0,z=0,dims=None):
        c=types[t];ds=dims or c['dims']
        ori=next(list(p) for p in itertools.permutations(range(3)) if [c['dims'][j] for j in p]==ds)
        return dict(item_id=f'{t}-{k:04d}',type_id=t,x=x,y=y,z=z,dx=ds[0],dy=ds[1],dz=ds[2],weight=c['weight'],category=c['category'],orientation=ori)
    def test(name,items,expected=True,rules=(),change=None,trchange=None):
        c=copy.deepcopy(cfg)
        if change:change(c)
        tr=dict(vehicle=copy.deepcopy(c['vehicles'][0]),vehicle_type='T1',truck_id='V001',items=copy.deepcopy(items))
        if trchange:trchange(tr)
        evaluate(name,[tr],c,expected,rules,'author adjacent/control')
    def evaluate(name,f,c,expected,rules,origin,complete=False):
        before=copy.deepcopy((f,c));r=check_fleet(f,c,complete);observed=sorted({e['rule'] for e in r['errors']})
        # NaN intentionally compares unequal; use serialized form for immutability.
        unchanged=json.dumps(before,sort_keys=True)==json.dumps((f,c),sort_keys=True)
        ok=r['valid']==expected and set(rules)<=set(observed) and unchanged
        tests.append(dict(name=name,origin=origin,expected_valid=expected,observed_valid=r['valid'],required_rules=list(rules),observed_rules=observed,input_unmodified=unchanged,pass_self_check=ok))
    disclosed=json.loads((ROOT/'inputs/disclosed_boundary_inputs.json').read_text(encoding='utf8'))
    for d in disclosed:
        inp=d['input'];evaluate(d['name'],inp['fleet'],inp['config'],d['expected_valid'],(), 'initial reviewer disclosed; informed replay',inp.get('complete',False))
    test('legal grounded fragile',[item('G3')])
    test('legal fragile union of two standard supports',[item('G2',dims=[35,50,25]),item('G2',2,x=35,dims=[35,50,25]),item('G3',z=25)])
    for t in types:
        for label in ['standard','fragile','directional']:
            if label!=types[t]['category']:
                b=item(t);b['category']=label
                test(f'{t} relabeled as {label}',[b],False,['category_source_mismatch'])
    lower=item('G3');lower['category']='standard'
    test('F1 original loaded fragile category spoof',[lower,item('G1',z=40)],False,['category_source_mismatch','fragile_loaded'])
    a=item('G4');a['category']='standard'
    test('directional centroid cannot be disabled by category spoof',[a,item('G4',2,x=80),item('G1',x=49,z=50)],False,['category_source_mismatch','directional_contact_center'])
    test('legal relaxed directional scenario',[item('G4'),item('G4',2,x=80),item('G1',x=49,z=50)],True,change=lambda c:c.update(directional_center_each=False))
    a=item('G4');a['category']='standard'
    test('directional support cannot be relabeled for fragile',[a,item('G3',z=50)],False,['category_source_mismatch','fragile_support'])
    test('legal fragile horizontal rotation',[item('G3',dims=[50,70,40])],True,change=lambda c:c.update(fragile_rotation=True))
    test('legal fragile floor-only control',[item('G3')],True,change=lambda c:c.update(fragile_floor_only=True))
    test('nonfloor fragile forbidden in floor-only scenario',[item('G2',dims=[35,50,25]),item('G2',2,x=35,dims=[35,50,25]),item('G3',z=25)],False,['fragile_floor_only'],change=lambda c:c.update(fragile_floor_only=True))
    for t in types:
        test('config category identity tamper '+t,[item(t)],False,['invalid_source_config'],change=lambda c,t=t:next(r for r in c['cargo'] if r['id']==t).update(category='fragile' if t!='G3' else 'standard'))
    test('duplicate config type identity',[item('G1')],False,['invalid_source_config'],change=lambda c:c['cargo'].append(copy.deepcopy(c['cargo'][0])))
    b=item('G1');b['item_id']='G2-0001';test('cross-type item identity',[b],False,['item_source_identity'])
    b=item('G1');b['type_id']='UNKNOWN';test('unknown type rejected structurally',[b],False,['unknown_cargo_type'])
    for iid in ['G1-0000','G1-0801','G1-00001','G1-one',None]:
        b=item('G1');b['item_id']=iid;test('invalid source serial '+str(iid),[b],False,['item_source_identity'])
    b=item('G3');b.pop('category');test('missing category metadata',[b],False,['category_source_mismatch'])
    b=item('G1');b['truck_id']='V999';test('item assigned to different truck',[b],False,['truck_assignment_mismatch'])
    test('vehicle payload metadata cannot relax source',[item('G1')],False,['vehicle_source_mismatch','payload'],change=lambda c:c['vehicles'][0].update(payload=10),trchange=lambda t:t['vehicle'].update(payload=10000))
    test('vehicle bounds metadata cannot relax source',[item('G1',x=410)],False,['vehicle_source_mismatch','boundary_clearance'],trchange=lambda t:t['vehicle'].update(dims=[1000,1000,1000]))
    test('unknown vehicle type',[item('G1')],False,['unknown_vehicle_type'],trchange=lambda t:t.update(vehicle_type='T9'))
    for k in ['x','dx','weight']:
        for v in [float('nan'),float('inf'),True,'12']:
            b=item('G1');b[k]=v
            test('nonfinite/typed '+k+' '+str(v),[b],False,['weight_source_mismatch' if k=='weight' else 'nonfinite_or_invalid_geometry'])
    b=item('G1');b['orientation']=[False,1,2];test('boolean orientation rejected',[b],False,['orientation_label'])
    test('legal numeric parameter variation',[item('G1')],True,change=lambda c:(c.update(clearance=4,bearing=750),c['vehicles'][0].update(cost=300,payload=7200,dims=[430,220,230])))
    test('invalid config nonfinite bearing',[item('G1')],False,['invalid_source_config'],change=lambda c:c.update(bearing=float('nan')))
    test('invalid config fractional inventory',[item('G1')],False,['invalid_source_config'],change=lambda c:c['cargo'][0].update(quantity=1.5))
    report={'kind':'informed author self-check, not independent acceptance','tests':tests,'total':len(tests),'passed':sum(t['pass_self_check'] for t in tests),'seconds':time.perf_counter()-started}
    (ROOT/'review/repair_regression.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='tests'},ensure_ascii=False))
    failures=[t for t in tests if not t['pass_self_check']]
    if failures:raise RuntimeError(failures)


if __name__=='__main__':run()
