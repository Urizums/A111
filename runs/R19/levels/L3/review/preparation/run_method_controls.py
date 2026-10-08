"""Reviewer-created controls only. No production or optimization input."""
import copy, json, time
from pathlib import Path
from independent_checker import check, compare_metrics, union_area, source_catalog
HERE=Path(__file__).resolve().parent
def item(t,i,x=0,y=0,z=0,dims=None):
    cargo,_=source_catalog()
    dims=dims or cargo[t]['dims']
    return dict(item_id=i,cargo_type=t,vehicle_id='control-T1',vehicle_type='T1',
                x=x,y=y,z=z,dx=dims[0],dy=dims[1],dz=dims[2])
legal=[item('G1','a'),item('G2','b',z=30),item('G3','c',x=100),
       item('G4','d',x=200),item('G5','e',x=300)]
controls=[]
def add(name,rows,expected_code=None,**kwargs):
    controls.append({'name':name,'input':rows,'kwargs':kwargs,
                     'expected':'valid' if expected_code is None else 'reject',
                     'expected_code':expected_code})
add('legal-all-types-support',legal)
add('legal-touching-face',[item('G1','a'),item('G1','b',x=60)])
add('legal-box-wall',[item('G4','a',x=340,y=150)])
add('legal-fragile-standard-top-six-rotation',[item('G1','a'),item('G3','b',z=30,dims=(50,40,70))])
add('legal-seven-source-box-stack',[item('G1',str(i),z=30*i) for i in range(7)])
add('illegal-positive-overlap',[item('G1','a'),item('G1','b',x=59.9)],'overlap')
add('illegal-negative-coordinate',[item('G1','a',x=-0.01)],'negative_coordinate')
add('illegal-top-clearance',[item('G1',str(i),z=30*i) for i in range(8)],'bounds_or_clearance')
add('illegal-fixed-orientation',[item('G4','a',dims=(60,80,50))],'orientation_or_size')
add('illegal-raw-size-substitution',[item('G1','a',dims=(59,40,30))],'orientation_or_size')
add('illegal-floating',[item('G1','a',z=1)],'full_support')
add('illegal-partial-fragile-support',[item('G1','a'),item('G3','b',z=30)],'fragile_standard_support')
add('illegal-on-fragile',[item('G3','a'),item('G2','b',z=40)],'on_fragile')
add('illegal-duplicate-id',[item('G1','a'),item('G2','a',x=100)],'duplicate_id')
add('illegal-full-batch-omission',legal,'full_batch_coverage',full_batch=True)
bad=item('G1','a'); bad['x']=float('nan')
add('illegal-nonfinite',[bad],'nonfinite')
add('illegal-cumulative-pressure-also-too-tall',[item('G1',str(i),z=30*i) for i in range(12)],'cumulative_pressure')
add('alternative-upright-fragile-rejects-rotated-control',[item('G1','a'),item('G3','b',z=30,dims=(50,40,70))],
    'orientation_or_size',fragile_rotation='upright')
add('illegal-directed-upper-center',[item('G4','a'),item('G1','b',x=70,z=50)],'directional_center')
union_support=[item('G1','a',dims=(40,60,30)),item('G1','b',x=40,dims=(40,60,30)),item('G3','c',z=30)]
add('legal-union-standard-fragile-support',union_support)
add('alternative-single-support-rejects-union-control',union_support,'fragile_single_standard_support',fragile_support='single')
start=time.perf_counter(); results=[]
for control in controls:
    t=time.perf_counter(); got=check(control['input'],**control['kwargs'])
    codes={v['code'] for v in got['violations']}
    passed=got['valid_under_declared_model'] if control['expected']=='valid' else not got['valid_under_declared_model'] and control['expected_code'] in codes
    results.append({'name':control['name'],'expected':control['expected'],
                    'expected_code':control['expected_code'],'self_test_pass':passed,
                    'observed':got,'elapsed_seconds':time.perf_counter()-t})
truth=check(legal); faithful=copy.deepcopy(truth); false=copy.deepcopy(truth)
false['vehicles'][0]['Uv']*=1.1
metric_results={'faithful':compare_metrics(truth,faithful),'corrupt':compare_metrics(truth,false)}
union_results={'overlapping_rectangles_union':union_area([(0,0,2,2),(1,0,3,2)]),
               'touching_rectangles_union':union_area([(0,0,1,1),(1,0,2,1)])}
all_pass=all(r['self_test_pass'] for r in results) and not metric_results['faithful'] and metric_results['corrupt']==['control-T1:Uv'] and union_results=={'overlapping_rectangles_union':6.0,'touching_rectangles_union':2.0}
output={'phase':'preparation_method_self_validation_only','control_origin':'reviewer created from raw DOCX source dimensions/masses; no original task solution',
        'source_anchors':['附件1.docx T1 parameters P4-P6','附件1.docx P13-P19','附件1.docx table1 R2-R6'],
        'caveat':'12-box pressure control also violates official height; confirms named cumulative check, not isolated pressure-only feasibility.',
        'actual_controls':results,'metric_tests':metric_results,'rectangle_union_tests':union_results,
        'all_method_controls_pass':all_pass,'production_acceptance_run':False,'elapsed_seconds':time.perf_counter()-start}
def encode(value):
    import math
    if isinstance(value,float) and not math.isfinite(value): return {'encoded_nonfinite_float':str(value)}
    if isinstance(value,dict): return {k:encode(v) for k,v in value.items()}
    if isinstance(value,list): return [encode(v) for v in value]
    return value
(HERE/'method-controls-input.json').write_text(json.dumps(encode(controls),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
(HERE/'method-controls-result.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'controls':len(results),'all_method_controls_pass':all_pass,
                  'elapsed_seconds':output['elapsed_seconds'],'production_acceptance_run':False}))
assert all_pass, 'Method self-test failed; preserve outputs before repair'
