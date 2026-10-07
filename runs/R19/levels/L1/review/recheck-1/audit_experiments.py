"""Independent scenario input deltas and all frozen fixed/count/cost placements."""
from independent_audit import audit,raw_config,OUT,EXEC
import copy,json,time
def expected(name):
    c=raw_config()
    if name=='base':pass
    elif name.startswith('vehicle_'):
        _,axis,delta=name.split('_'); k=['length','width','height'].index(axis)
        for v in c['vehicles']:v['dims'][k]+=float(delta)
    elif name.startswith('cargo_'):
        _,axis,delta=name.split('_');k=['length','width','height'].index(axis)
        for x in c['cargo']:x['dims'][k]+=float(delta)
    elif name.startswith('clearance_'):c['clearance']=float(name.split('_')[1])
    elif name.startswith('payload_'):
        for v in c['vehicles']:v['payload']*=float(name.split('_')[1])
    elif name.startswith('mass_'):
        for x in c['cargo']:x['weight']*=float(name.split('_')[1])
    elif name.startswith('quantity_'):
        for x in c['cargo']:x['quantity']=round(x['quantity']*float(name.split('_')[1]))
    elif name.startswith('fragile_quantity_'):c['cargo'][2]['quantity']=round(c['cargo'][2]['quantity']*float(name.split('_')[-1]))
    elif name.startswith('T1_cost_'):c['vehicles'][0]['cost']=float(name.split('_')[-1])
    elif name.startswith('T2_cost_'):c['vehicles'][1]['cost']=float(name.split('_')[-1])
    elif name.startswith('bearing_'):c['bearing']=float(name.split('_')[1])
    elif name=='fragile_horizontal_rotation':c['fragile_rotation']=True
    elif name=='fragile_floor_only':c['fragile_floor_only']=True
    elif name=='directional_union_resultant':c['directional_center_each']=False
    else:raise ValueError(name)
    return c
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--execution-root',type=type(EXEC),default=EXEC);p.add_argument('--prefix',default='independent-experiment-audit');args=p.parse_args()
    source=args.execution_root
    declared=json.loads((source/'configs/experiments.json').read_text(encoding='utf-8'));reports=[];tic=time.perf_counter()
    for scenario in declared['scenarios']:
        name=scenario['id'];cfg=expected(name);d=json.loads((source/f'results/sensitivity/{name}.json').read_text(encoding='utf-8'))
        cfgmatch=cfg==scenario['config']==d['config']; rr=[]
        for fixed in d['fixed']:
            x={**fixed,'config':cfg};r,_=audit(x,name+'-'+fixed['vehicle_type'],True,cfg);rr.append(r)
        for objective,mixed in d['mixed'].items():
            x={**mixed,'config':cfg};r,_=audit(x,name+'-'+objective,True,cfg);rr.append(r)
        reports.append({'scenario':name,'config_matches_declared_delta_and_raw':cfgmatch,'all_layouts_valid':all(r['valid'] for r in rr),'layout_reports':rr})
    report={'seconds':time.perf_counter()-tic,'all_configs_match':all(r['config_matches_declared_delta_and_raw'] for r in reports),'all_layouts_valid':all(r['all_layouts_valid'] for r in reports),'scenario_count':len(reports),'fleet_count':sum(len(r['layout_reports']) for r in reports),'reports':reports}
    (OUT/f'{args.prefix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['seconds','all_configs_match','all_layouts_valid','scenario_count','fleet_count']},ensure_ascii=False))
    print('violations',[(r['scenario'],rr['task'],rr['violation_count'],rr['violations'][:2]) for r in reports for rr in r['layout_reports'] if not rr['valid']])
if __name__=='__main__':main()
