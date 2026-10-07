from independent_audit import OUT,EXEC,ROOT,raw_config,audit
import json,copy,re,openpyxl
history=[]
for name,complete in [('results/main/fixed_T1.json',True),('results/modules/T2_4.json',True),('results/smoke.json',True),('results/smoke_v3.json',True)]:
    d=json.loads((EXEC/name).read_text(encoding='utf-8'));cfg=raw_config()
    if 'smoke' in name:
        for c in cfg['cargo']:c['quantity']=3
    # Inspect old geometries against current disclosed raw-source rule; old cfg tags
    # are recorded but not allowed to dilute the current directional assertion.
    r,_=audit({'fleet':d['fleet']},name,complete,cfg)
    history.append({'path':name,'reported_version':d.get('config',{}).get('version'),'audited_under':'current strict static source interpretation; no claim old run used current code','valid':r['valid'],'violation_count':r['violation_count'],'violations':r['violations'],'metrics':r['metrics']})
workbook=openpyxl.load_workbook(ROOT/'runs/R19/inputs/raw/附件2：验证数据集.xlsx',data_only=False)
ps=workbook['箱装产品尺寸'];vs=workbook['车型尺寸']
def ends(value):
    n=list(map(float,re.findall(r'\d+(?:\.\d+)?',str(value))));return min(n),max(n)
products=[];vehicles=[];fits=[]
for row in range(3,11):products.append({'name':ps.cell(row,1).value,'upper_cm':[ends(ps.cell(row,col).value)[1]/10 for col in [3,5,7]],'lower_cm':[ends(ps.cell(row,col).value)[0]/10 for col in [3,5,7]],'source_cells':[ps.cell(row,col).coordinate for col in [3,5,7]]})
for row in range(4,12):vehicles.append({'name':vs.cell(row,1).value,'lower_cm':[ends(vs.cell(row,col).value)[0]*100 for col in [2,3,4]],'source_row':row})
for p in products:
    for v in vehicles:fits.append({'product':p['name'],'vehicle':v['name'],'fits':all(p['upper_cm'][i]<=v['lower_cm'][i]-(3 if i==2 else 0) for i in range(3))})
reported=json.loads((EXEC/'inputs/attachment2_geometry.json').read_text(encoding='utf-8'))
fitmatch=all(a['fits']==b['fits_single_geometry'] and a['product']==b['product'] and a['vehicle']==b['vehicle'] for a,b in zip(fits,reported['fits'])) and len(fits)==len(reported['fits'])
productsmatch=all(a['upper_cm']==b['dims_cm_upper'] and a['lower_cm']==b['dims_cm_lower'] for a,b in zip(products,reported['products']))
vehiclesmatch=all(a['lower_cm']==b['dims_cm_lower'] for a,b in zip(vehicles,reported['closed_rectangular_vehicles']))
countscheck=True
base=json.loads((EXEC/'configs/base.json').read_text(encoding='utf-8')); countscheck=base==raw_config()
repeat=[]
for name in ['fixed_T1','fixed_T2','mixed_count','mixed_cost','single_T1_0','single_T1_1','single_T2_0']:
    original=json.loads((EXEC/f'results/final/{name}.json').read_text(encoding='utf-8'))
    for folder in ['raw-rerun','zip-raw-rerun']:
        actual=json.loads((OUT/f'{folder}/{name}.json').read_text(encoding='utf-8'));repeat.append({'task':name,'rerun':folder,'all_geometry_equal':actual['fleet']==original['fleet'],'all_statistics_equal':actual['statistics']==original['statistics']})
exprepeat=[]
for name in ['base','T1_cost_300','bearing_250','cargo_height_-5','directional_union_resultant']:
    original=json.loads((EXEC/f'results/sensitivity/{name}.json').read_text(encoding='utf-8'));actual=json.loads((OUT/f'experiment-rerun/results/sensitivity/{name}.json').read_text(encoding='utf-8'))
    exprepeat.append({'scenario':name,'both_objective_metrics_equal':all(original['mixed'][obj]['statistics']==actual['mixed'][obj]['statistics'] for obj in ['count','cost']),'claim_limit':'elapsed/solver receipts may differ; comparison of metrics, not identical search history'})
result={'historical_rejected_artifact_checks':history,'attachment2':{'pairs':len(fits),'fits':sum(r['fits'] for r in fits),'product_units_ranges_match':productsmatch,'vehicle_units_ranges_match':vehiclesmatch,'reported_fits_match':fitmatch,'no_business_solve_attempted':True,'missing_business_fields_confirmed':['quantity','package_weight','category/orientation','vehicle_payload','trip_distance_and_cost_basis'],'independent_products':products,'independent_vehicles':vehicles},'normalized_base_matches_own_raw':countscheck,'repeat_comparisons':repeat,'selected_experiment_repeat_comparisons':exprepeat}
(OUT/'extra-source-history-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'history':[(x['path'],x['valid'],x['violation_count']) for x in history],'a2':{k:v for k,v in result['attachment2'].items() if not k.startswith('independent')},'all_main_reruns_equal':all(r['all_geometry_equal'] and r['all_statistics_equal'] for r in repeat),'all5_scenario_metrics_equal':all(r['both_objective_metrics_equal'] for r in exprepeat)},ensure_ascii=False,indent=2))
