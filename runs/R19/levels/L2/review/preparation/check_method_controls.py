from pathlib import Path
import json,copy,datetime
from independent_checker import validate_layout,union_area
out=Path(__file__).parent
V={'v':{'dims':[1000,1000,1000],'clearance':30,'payload':10000,'cost':450}}
def item(k,d=[100,100,100],w=1,c='standard'):
 return {'dims':d,'weight':w,'category':c,'cargo':k}
def place(k,p=[0,0,0],d=[100,100,100]):
 return {'item_id':k,'vehicle_id':'v','xyz':p,'dims':d,'cargo':k}
C=[]
def add(name,it,ps,valid,rule=None,**opts):C.append((name,it,ps,valid,rule,opts))
add('legal_touching_faces',{'a':item('a'),'b':item('b')},[place('a'),place('b',[100,0,0])],True)
add('reject_positive_overlap',{'a':item('a'),'b':item('b')},[place('a'),place('b',[99,0,0])],False,'overlap')
add('legal_exact_top_clearance',{'a':item('a',[100,100,970])},[place('a',d=[100,100,970])],True)
add('reject_clearance_plus_one_mm',{'a':item('a',[100,100,971])},[place('a',d=[100,100,971])],False,'boundary_clearance')
add('reject_negative_coordinate',{'a':item('a')},[place('a',[-1,0,0])],False,'boundary_clearance')
add('reject_directional_swap',{'a':item('a',[100,200,100],c='directional')},[place('a',d=[200,100,100])],False,'orientation')
add('legal_standard_permutation',{'a':item('a',[100,200,100])},[place('a',d=[200,100,100])],True)
add('legal_fragile_planar_rotation',{'a':item('a',[100,200,150],c='fragile')},[place('a',d=[200,100,150])],True)
add('reject_fragile_vertical_rotation',{'a':item('a',[100,200,150],c='fragile')},[place('a',d=[150,100,200])],False,'orientation')
base={'a':item('a',[500,1000,100]),'b':item('b',[500,1000,100]),'f':item('f',[1000,1000,100],w=15,c='fragile')}
ps=[place('a',d=[500,1000,100]),place('b',[500,0,0],[500,1000,100]),place('f',[0,0,100],[1000,1000,100])]
add('legal_fragile_coplanar_union_support',base,ps,True)
hole=copy.deepcopy(ps);hole[1]['xyz'][0]=501;hole[1]['dims'][0]=499;bad=copy.deepcopy(base);bad['b']['dims'][0]=499
add('reject_one_mm_support_hole',bad,hole,False,'fragile_full_support')
add('reject_fragile_supported_by_directional',{'d':item('d',c='directional'),'f':item('f',c='fragile')},[place('d'),place('f',[0,0,100])],False,'fragile_support_material')
add('reject_load_on_fragile',{'f':item('f',c='fragile'),'a':item('a')},[place('f'),place('a',[0,0,100])],False,'fragile_no_load')
add('reject_floating',{'a':item('a')},[place('a',[0,0,1])],False,'floating')
add('legal_contact_pressure_equality',{'a':item('a',[1000,1000,100]),'b':item('b',[1000,1000,100],w=500)},[place('a',d=[1000,1000,100]),place('b',[0,0,100],[1000,1000,100])],True)
add('reject_contact_pressure_above_equality',{'a':item('a',[1000,1000,100]),'b':item('b',[1000,1000,100],w=500.001)},[place('a',d=[1000,1000,100]),place('b',[0,0,100],[1000,1000,100])],False,'cumulative_contact_pressure')
add('reject_cumulative_chain_not_only_direct_load',{'a':item('a',[1000,1000,100]),'b':item('b',[1000,1000,100],w=250),'c':item('c',[1000,1000,100],w=251)},[place('a',d=[1000,1000,100]),place('b',[0,0,100],[1000,1000,100]),place('c',[0,0,200],[1000,1000,100])],False,'cumulative_contact_pressure')
add('reject_local_directional_center_outside',{'d':item('d',[400,1000,100],c='directional'),'a':item('a',[1000,1000,100])},[place('d',d=[400,1000,100]),place('a',[0,0,100],[1000,1000,100])],False,'directional_local_center')
add('legal_local_directional_center_on_edge',{'d':item('d',[500,1000,100],c='directional'),'a':item('a',[1000,1000,100])},[place('d',d=[500,1000,100]),place('a',[0,0,100],[1000,1000,100])],True)
add('reject_duplicate_id',{'a':item('a')},[place('a'),place('a',[100,0,0])],False,'duplicate_item')
add('reject_full_inventory_omission',{'a':item('a'),'b':item('b')},[place('a')],False,'inventory_equality')
add('legal_single_vehicle_subset',{'a':item('a'),'b':item('b')},[place('a')],True,full=False)
add('reject_missing_weight',{'a':item('a',w=None)},[place('a')],False,'nonfinite_or_missing')
add('reject_nonfinite_coordinate',{'a':item('a')},[place('a',[float('nan'),0,0])],False,'nonfinite_or_missing')
add('reject_over_payload',{'a':item('a',w=10001)},[place('a')],False,'payload')
results=[]
for name,it,ps,want,rule,opts in C:
 got=validate_layout(it,V,ps,**opts)
 passed=got['valid']==want and (rule is None or rule in [e['rule'] for e in got['errors']])
 results.append({'case':name,'expected_valid':want,'expected_rule':rule,'options':opts,'passed':passed,'actual':got})
# Independent unit anchors: cm->mm, mm^2->m^2, cost/nominal volume objective definitions.
anchors={'1_m2_in_mm2':1000*1000,'250_kg_on_half_m2_pressure':250/(500*1000/1e6),'union_area_with_hole_mm2':union_area([[0,0,500,1000],[501,0,1000,1000]]),'full_union_area_mm2':union_area([[0,0,500,1000],[500,0,1000,1000]])}
unit_pass=anchors=={'1_m2_in_mm2':1000000,'250_kg_on_half_m2_pressure':500.0,'union_area_with_hole_mm2':999000.0,'full_union_area_mm2':1000000.0}
payload={'status':'review_method_controls_only_not_producer_verdict','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture_data_origin':'reviewer synthetic analytical examples; no execution artifact','count':len(results),'all_passed':all(x['passed'] for x in results) and unit_pass,'unit_anchors':anchors,'unit_anchors_passed':unit_pass,'cases':results}
(out/'checker-controls.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=True),encoding='utf-8')
print(json.dumps({'count':len(results),'all_passed':payload['all_passed'],'failed':[x['case'] for x in results if not x['passed']]},ensure_ascii=False))
if not payload['all_passed']:raise SystemExit(1)

