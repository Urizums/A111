from pathlib import Path
import json,datetime,hashlib,collections
from audit_independent import a,O,E,B,ITEMS,VS,CFG,layout,records
from run_calls import dump
cases={r['case']:r for r in a.readcsv(E/'experiments/experiments.csv')};params=[];methods=[]
for method in ('A','B'):
 cfg=json.loads((O/('config_'+method+'.json')).read_text());cfg['fragile_fixed']=False;d=O/'method_replay'/method
 for group in ('baseline','selected','single'):
  for f in sorted((d/group).iterdir()):
   if f.is_dir():layout(f,cfg=cfg,full=group!='single',tag='fresh_'+method)
 frozen=E/'research/comparison'/f'{method}_seed19'/'guarded/selected'
 methods.append({'method':method,'fresh_scenario_metrics':{name:json.loads((d/'selected'/name/'run.json').read_text())['cost_yuan'] for name in ('q1_all_v1','q1_all_v2','q2_vehicles','q2_cost')},'same_as_old_guard_costs':{name:json.loads((d/'selected'/name/'run.json').read_text())['cost_yuan']==json.loads((frozen/name/'run.json').read_text())['cost_yuan'] for name in ('q1_all_v1','q1_all_v2','q2_vehicles','q2_cost')},'limits':'current corrected candidate preservation, not replay of old raw9 code; elapsed times not required equal'})
for r in sorted(O.glob('parameter_*.receipt.json')):
 receipt=json.loads(r.read_text());case=receipt['label'][len('parameter_'):];c=cases[case];items,vs,cfg=a.expected(c);cfg['geometry']='C'
 if c['parameter']=='fragile_floor':cfg['fragile_floor']=True
 z={'case':case,'actual_exit':receipt['exit'],'actual_seconds':receipt['seconds'],'source_input_check':a.input_match(O/'parameter_inputs'/case,items,vs,cfg)}
 if receipt['exit']==0:
  x=layout(O/'parameter_replay'/case,items,vs,cfg,True,'fresh_'+case);z['layout']=x;z['frozen_metric_equal']={k:abs(float(c[ck])-x['metrics'][k])<1e-7 for ck,k in [('vehicles','vehicle_count'),('cost_yuan','cost_yuan'),('volume_utilization','volume_utilization'),('weight_utilization','weight_utilization')]}
 else:z['stderr']=(O/(receipt['label']+'.stderr.log')).read_text(encoding='utf-8');z['expected_necessary_height_failure']=case=='27_vehicle_height' and 'heuristic_no_fit_not_mathematical_infeasibility' in z['stderr']
 params.append(z)
frozen=json.loads((O/'independent-audit.json').read_text());fs={Path(z['folder']).name:z for z in frozen['layouts'] if z['tag']=='frozen' and '/selected/' in z['folder'].replace('\\','/')};fresh={Path(z['folder']).name:z for z in frozen['layouts'] if z['tag']=='fresh_zip' and '/selected/' in z['folder'].replace('\\','/')}
zipcompare={name:{'frozen_metrics':fs[name]['metrics'],'fresh_metrics':z['metrics'],'all_metrics_match':fs[name]['metrics']==z['metrics'],'placements_bytes_match':fs[name]['placements_sha256']==z['placements_sha256']} for name,z in fresh.items()}
dump(O/'affected-replay-audit.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fresh_A_B_layouts_and_parameters':records,'methods':methods,'parameters':params,'fresh_full_zip_against_frozen':zipcompare,'remaining':{'current_successful_saved_parameters_not_fresh_solver_replayed':29,'old_raw9_calls_not_reexecuted':9,'seed7_41_comparison_saved_results_fully_checked':True},'limits':'all35current successful parameter layouts and raw9+guard9 already fully independently checked; this fresh scope only2method all+6parameter successes+1heightfailure; originalZIP full11 checked inindependent-audit'})
print(json.dumps({'new_layouts':len(records),'invalid':[z['folder'] for z in records if not z['valid']],'method_costs':methods,'parameter_matches':[(z['case'],z.get('frozen_metric_equal',z.get('expected_necessary_height_failure'))) for z in params],'ZIPfull_selected_metrics_match':{k:z['all_metrics_match'] for k,z in zipcompare.items()}},ensure_ascii=False))
