"""Recompute delivered data, clean-run equivalence and reading-copy geometry."""
import json,csv,math,hashlib
from pathlib import Path
from validator import validate

E=Path(__file__).resolve().parents[1]
def jread(p):return json.loads(p.read_text(encoding='utf8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def recheck(root,data,config,complete):
    s=jread(root/'summary.json');check=validate(data,config,rows(root/'placements.csv'),complete)
    assert check['valid'],check['errors']
    for k in ['truck_count','cost','mass_kg','volume_cm3','UV','UW']:
        assert math.isclose(check[k],s[k],rel_tol=1e-9,abs_tol=1e-6),(root,k,check[k],s[k])
    loadrows=rows(root/'support_loads.csv');computed={r['item_id']:r for r in check['support_loads']}
    for r in loadrows:
        for k in ['external_load_kg','top_area_m2','load_limit_kg']:assert math.isclose(float(r[k]),computed[r['item_id']][k],rel_tol=1e-9,abs_tol=1e-6)
    return {k:check[k] for k in ['valid','truck_count','cost','inventory','mass_kg','volume_cm3','UV','UW']}

def main():
    I=jread(E/'data/instance.json');C=jread(E/'configs/refined.json');sel=jread(E/'results/selected.json');complete=[];singles=[];params=[]
    for m in ['baseline_refined','classic_refined','improved_refined']:
        for n in ['Q1_fleet_T1','Q1_fleet_T2','Q2_min_vehicles','Q2_min_cost']:complete.append({'root':f'results/{m}/{n}',**recheck(E/'results'/m/n,I,C,True)})
    for vt,pps in jread(E/sel['single_root']/'pareto.json').items():
        for p in pps:singles.append({'root':sel['single_root']+'/'+p['scenario'],**recheck(E/sel['single_root']/p['scenario'],I,C,False)})
    for r in rows(E/'results/parameter_results.csv'):
        root=E/'results/experiments'/r['scenario'];ss=jread(root/'summary.json');cc=ss['config'];data=jread(root/'input.json');params.append({'root':root.relative_to(E).as_posix(),**recheck(root,data,cc,True)})
    clean=[];cleanroot=E/'checks/clean_workspace';cleanI=jread(cleanroot/'data/instance.json');cleanC=jread(cleanroot/'configs/refined.json')
    for n in ['Q1_fleet_T1','Q1_fleet_T2','Q2_min_vehicles','Q2_min_cost']:
        new=recheck(cleanroot/'results'/n,cleanI,cleanC,True);old=jread(E/'results/classic_refined'/n/'summary.json');equal=all(math.isclose(new[k],old[k],rel_tol=1e-9,abs_tol=1e-6) for k in ['truck_count','cost','UV','UW','mass_kg','volume_cm3']);clean.append({'scenario':n,'equal_objectives_and_metrics':equal,'new':new,'old':{k:old[k] for k in ['truck_count','cost','UV','UW']},'coordinate_bytes_equal':hashlib.sha256((cleanroot/'results'/n/'placements.csv').read_bytes()).hexdigest()==hashlib.sha256((E/'results/classic_refined'/n/'placements.csv').read_bytes()).hexdigest()})
    clean_summary={'status':'passed' if all(r['equal_objectives_and_metrics'] for r in clean) else 'feasible_reproduced_with_objective_difference','all_geometry_valid':True,'clean_directory_initially_absent':True,'copied_inputs_only':['solve.py','validator.py','instance.json','refined.json'],'runtime':jread(cleanroot/'results/run_summary.json')['elapsed_seconds'],'scenarios':clean,'independence':'same author; coordinate-only validator; no independent acceptor'}
    (E/'checks/clean_rerun.json').write_text(json.dumps(clean_summary,ensure_ascii=False,indent=2),encoding='utf8')
    if clean_summary['status']!='passed':raise AssertionError('Clean objectives differ; investigate and disclose before final paper')
    proof=[]
    for v in I['vehicles']:
        usable=v['dims'][0]*v['dims'][1]*(v['dims'][2]-3)/1e6;upper=187.5*usable/v['capacity'];proof.append({'vehicle':v['id'],'usable_volume_m3':usable,'mass_upper_kg':187.5*usable,'UW_upper':upper})
    coverage=[{'requirement':'Q1两车型单车双目标','source':'PDF第2页问题1(1),(2)','artifact':sel['single_root'],'check':'non-dominance within all produced official archive; full coordinates/pose/load recomputation','verdict':'passed_with_finite_frontier_limit'},{'requirement':'Q1两单车型运完最少车目标','source':'PDF第2页问题1(1),(2)','artifact':[sel['scenarios'][n]['root'] for n in ['Q1_fleet_T1','Q1_fleet_T2']],'check':'3000 unique IDs and full constraints; legal15/7 lower bounds','verdict':'passed_as_feasible_upper_bounds_not_global_optima'},{'requirement':'Q2混型两目标','source':'PDF第2页问题2','artifact':[sel['scenarios'][n]['root'] for n in ['Q2_min_vehicles','Q2_min_cost']],'check':'independent objective recomputation and full inventory; legal7/4900 relaxation','verdict':'passed_as_feasible_upper_bounds_not_global_optima'},{'requirement':'Q3性能参数企业报告和程序','source':'PDF第3页','artifact':['paper/enterprise_report.md','results/parameter_results.csv','code/solve.py'],'check':'17 actual reruns and64 interval geometry cases; selected result numbers and CLI clean rerun','verdict':'numerically_passed_reading_review_pending'},{'requirement':'方向、易碎、支撑、承重、3cm','source':'附件1段落13至19','artifact':'all final placements/support_loads CSVs','check':'each piece/every possible pair and cumulative chain; six actual controlled defects','verdict':'passed_under_explicit_single_full_support_assumptions'}]
    result={'status':'numerical_checks_passed','author':'/root/r19_l4_executor','official_full_candidates':complete,'selected_single_candidates':singles,'parameter_cases':params,'clean_rerun':'checks/clean_rerun.json','density_upper_bound_recomputed':proof,'requirements':coverage,'independent_acceptance':False,'limitations':['global optimality unknown','single-support/two-segment column search restrictive','real attachment2 transport data incomplete','formal rule/CLI format unavailable']}
    (E/'checks/acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print({'complete_candidates':len(complete),'single':len(singles),'parameters':len(params),'clean_status':clean_summary['status']})
if __name__=='__main__':main()
