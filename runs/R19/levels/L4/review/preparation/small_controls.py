from pathlib import Path
import json, time
from copy import deepcopy
from independent_checks import validate, union_area, inventory_errors, aggregate

def item(id, t, xyz=(0,0,0), dims=(100,100,10), mass=100):
    return dict(zip(['id','type','x','y','z','l','w','h','mass'],[id,t,*xyz,*dims,mass]))

def main():
    start=time.perf_counter()
    truck={'L':300,'W':200,'H':100,'capacity':5000,'cost':450}
    cat={'S':{'dims':[100,100,10],'mass':100,'quantity':5,'class':'standard'},
         'F':{'dims':[100,100,10],'mass':100,'quantity':2,'class':'fragile'},
         'D':{'dims':[80,60,50],'mass':25,'quantity':2,'class':'directed'}}
    cases=[]
    def test(name,items,expected,required_error=None,**kw):
        r=validate(truck,items,cat,**kw)
        ok=r['valid']==expected and (required_error is None or required_error in r['errors'])
        cases.append({'name':name,'kind':'synthetic_preparation_control','expected_valid':expected,
                      'expected_error':required_error,'observed':r,'control_pass':ok,'items':items})
    a=item('a','S'); b=item('b','S',(100,0,0))
    test('boundary_touch_is_legal',[a,b],True)
    b['x']=99
    test('positive_volume_overlap',[a,b],False,'overlap')
    b=item('b','S',(201,0,0))
    test('horizontal_boundary',[a,b],False,'boundary')
    test('exact_3cm_gap',[item('d','D',(0,0,47),(80,60,50),25)],False,'floating')
    gapcat=deepcopy(cat);gapcat['T']={'dims':[100,100,97],'mass':100,'quantity':1,'class':'standard'}
    r=validate(truck,[item('t','T',dims=(100,100,97))],gapcat)
    cases.append({'name':'exact_3cm_gap_on_floor','expected_valid':True,'observed':r,'control_pass':r['valid']})
    i=item('t','T',dims=(100,100,97.1));gapcat['T']['dims']=[100,100,97.1]
    r=validate(truck,[i],gapcat)
    cases.append({'name':'gap_2_9cm_rejected','expected_error':'safety_gap','observed':r,'control_pass':'safety_gap' in r['errors']})
    test('directed_rotation',[item('d','D',dims=(60,80,50),mass=25)],False,'orientation')
    test('fragile_on_standard',[a,item('f','F',(0,0,10))],True)
    test('fragile_on_floor',[item('f','F')],True)
    test('fragile_topped',[item('f','F'),item('b','S',(0,0,10))],False,'fragile_topped')
    test('floating_fragile',[item('f','F',(0,0,1))],False,'floating')
    test('partial_fragile_support',[a,item('f','F',(10,0,10))],False,'incomplete_support')
    r=union_area([(0,0,4,10),(6,0,10,10),(0,0,4,10)])
    cases.append({'name':'union_hole_and_duplicate_rectangles','observed_area':r,'expected_area':80,'control_pass':r==80})
    loadcat={'S':{'dims':[100,100,10],'mass':300,'quantity':3,'class':'standard'}}
    chain=[item(str(n),'S',(0,0,n*10),mass=300) for n in range(3)]
    r=validate(truck,chain,loadcat)
    cases.append({'name':'cumulative_not_immediate_load','expected_error':'static_load_infeasible','observed':r,
                  'hand_control':'bottom external load 600kg exceeds 500kg; each immediate item 300kg',
                  'control_pass':'static_load_infeasible' in r['errors']})
    loadcat['S']['mass']=200;chain=[item(str(n),'S',(0,0,n*10),mass=200) for n in range(3)]
    r=validate(truck,chain,loadcat)
    loads=(r.get('forces') or {}).get('incoming_loads_kg',[])
    cases.append({'name':'cumulative_valid_chain','observed':r,'expected_loads':[400,200,0],
                  'control_pass':r['valid'] and len(loads)==3 and all(abs(a-b)<1e-6 for a,b in zip(loads,[400,200,0]))})
    smallcat=deepcopy(cat);smallcat['U']={'dims':[50,50,10],'mass':160,'quantity':1,'class':'standard'}
    small=[a,item('u','U',(25,25,10),(50,50,10),160)]
    top=validate(truck,small,smallcat,pressure_basis='top'); actual=validate(truck,small,smallcat,pressure_basis='contact')
    cases.append({'name':'pressure_semantics_are_separate','observed_top':top,'observed_contact':actual,
                  'hand_control':'top-area limit500kg vs actual contact-area125kg; imposed load160kg',
                  'control_pass':top['valid'] and 'static_load_infeasible' in actual['errors']})
    test('source_mass_spoof',[item('a','S',mass=1)],False,'mass_not_source_bound')
    lowtruck=dict(truck,capacity=99)
    r=validate(lowtruck,[a],cat)
    cases.append({'name':'truck_weight_capacity','observed':r,'control_pass':'truck_weight' in r['errors']})
    test('directed_lower_upper_center',[item('d','D',dims=(80,60,50),mass=25),item('a','S',(40,0,50))],False,'directed_upper_center',full_support_all=False)
    test('duplicate_id',[a,item('a','S',(100,0,0))],False,'duplicate_item_id')
    r=inventory_errors([a],cat,False); r2=inventory_errors([a],cat,True)
    cases.append({'name':'partial_single_vs_complete_batch','observed_single':r,'observed_batch':r2,
                  'control_pass':not r and 'inventory_missing_or_excess' in r2})
    metriccat={'U':{'dims':[100,100,50],'mass':1000,'quantity':2,'class':'standard'}}
    t={'L':100,'W':100,'H':100,'capacity':2000,'cost':450}
    mr=validate(t,[item('m','U',dims=(100,100,50),mass=1000)],metriccat)
    cases.append({'name':'original_volume_denominator','observed':mr,'expected_UV':.5,'expected_UW':.5,
                  'control_pass':mr['valid'] and mr['metrics']['UV']==.5 and mr['metrics']['UW']==.5 and mr['metrics']['UV_usable']!=.5})
    t2=dict(t,L=200,capacity=4000,cost=700)
    mr2=validate(t2,[item('n','U',dims=(100,100,50),mass=1000)],metriccat)
    ag=aggregate([t,t2],[mr,mr2])
    cases.append({'name':'aggregate_ratios_and_cost','observed':ag,'expected_N':2,'expected_cost':1150,
                  'expected_UV':1/3,'expected_UW':1/3,
                  'control_pass':ag['N']==2 and ag['cost']==1150 and abs(ag['UV']-1/3)<1e-12 and abs(ag['UW']-1/3)<1e-12})
    multicat={'B':{'dims':[50,100,10],'mass':100,'quantity':2,'class':'standard'},
              'U':{'dims':[100,100,10],'mass':200,'quantity':1,'class':'standard'}}
    multi=[item('b1','B',dims=(50,100,10)),item('b2','B',(50,0,0),(50,100,10)),item('u','U',(0,0,10),mass=200)]
    r=validate(truck,multi,multicat)
    cases.append({'name':'two_supports_equilibrium','observed':r,'control_pass':r['valid'] and r['forces']['max_balance_residual']<1e-6})
    offcat={'B':{'dims':[20,100,10],'mass':100,'quantity':1,'class':'standard'},
            'U':{'dims':[100,100,10],'mass':10,'quantity':1,'class':'standard'}}
    r=validate(truck,[item('b','B',dims=(20,100,10)),item('u','U',(0,0,10),mass=10)],offcat,full_support_all=False)
    cases.append({'name':'force_moment_impossible_overhang','observed':r,'control_pass':'static_load_infeasible' in r['errors']})
    report={'scope':'preparation_only_not_production_acceptance','all_controls_pass':all(c['control_pass'] for c in cases),
            'control_count':len(cases),'elapsed_seconds':time.perf_counter()-start,'cases':cases}
    p=Path(__file__).parent/'small-controls-results.json'
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False))
    for c in cases:
        print(c['name'],c['control_pass'])
    if not report['all_controls_pass']:raise SystemExit(1)
if __name__=='__main__':main()
