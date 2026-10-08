"""Preparation-only controls. They are not production smoke or acceptance."""
import copy
import hashlib
import json
from pathlib import Path
from independent_check import check

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = ROOT/'runs/R19/final/forward/inputs/raw.json'
raw = json.loads(RAW.read_text(encoding='utf-8-sig'))


def packet(coords):
    return dict(vehicles=[dict(id='review-control-v', type_id='T')], placements=[
        dict(item_id=i, vehicle_id='review-control-v', x_m=x,y_m=y,z_m=z)
        for i,x,y,z in coords])


valid = packet([('S1',0,0,0),('F1',0,0,1),('S2',1,0,0),('S3',1,0,1)])
cases = [('valid_stacked',valid,True,None)]
recursive = packet([('S1',0,0,0),('S2',0,0,1),('F1',0,0,2),('S3',1,0,0)])
cases.append(('recursive_overload',recursive,False,'cumulative_standard_load'))
fragile = packet([('F1',0,0,0),('S1',0,0,1),('S2',1,0,0),('S3',1,0,1)])
cases.append(('fragile_bearing',fragile,False,'fragile_bears_cargo'))
spoof = copy.deepcopy(fragile)
spoof['placements'][0]['category'] = 'standard'
cases.append(('spoofed_source_category',spoof,False,'item_source_conflict'))
for axis in ('x_m','y_m','z_m'):
    for value, label in [(float('nan'),'nan'),(float('inf'),'inf'),(-float('inf'),'minus_inf')]:
        variant = copy.deepcopy(valid)
        variant['placements'][0][axis] = value
        cases.append((f'{axis}_{label}',variant,False,'coordinate_domain'))
for name, mutate, expected in [
    ('missing_item',lambda p:p['placements'].pop(),'item_multiplicity'),
    ('duplicate_item',lambda p:p['placements'].append(copy.deepcopy(p['placements'][0])),'item_multiplicity'),
    ('floating_item',lambda p:p['placements'][1].update(z_m=1.01),'single_complete_support'),
    ('partial_support',lambda p:p['placements'][1].update(x_m=0.05),'single_complete_support'),
    ('overlap',lambda p:p['placements'][1].update(z_m=0.5),'overlap'),
    ('clearance_breach',lambda p:p['placements'][1].update(z_m=2.2),'vehicle_bounds_or_clearance'),
    ('dimension_spoof',lambda p:p['placements'][0].update(length_m=0.5),'item_source_conflict'),
    ('vehicle_spoof',lambda p:p['vehicles'][0].update(payload_kg=999),'vehicle_source_conflict'),
    ('objective_nan',lambda p:p.update(total_cost_CNY=float('nan')),'objective_report_conflict'),
]:
    variant = copy.deepcopy(valid)
    mutate(variant)
    cases.append((name,variant,False,expected))
observations = []
for name, candidate, expect, code in cases:
    observed = check(raw,candidate)
    codes = sorted(set(e['code'] for e in observed['errors']))
    correct = observed['valid'] == expect and (code is None or code in codes)
    observations.append(dict(control=name, expected_valid=expect,
        expected_rejection_code=code, control_agrees=correct, observation=observed))
out = dict(scope='review preparation only; no production inspected or judged',
    raw_sha256=hashlib.sha256(RAW.read_bytes()).hexdigest(),
    false_acceptances=sum(not c['expected_valid'] and c['observation']['valid'] for c in observations),
    false_rejections=sum(c['expected_valid'] and not c['observation']['valid'] for c in observations),
    controls=observations)
(HERE/'control-observations.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(control_count=len(observations),all_controls_agree=all(c['control_agrees'] for c in observations),
    false_acceptances=out['false_acceptances'],false_rejections=out['false_rejections']),ensure_ascii=False))
raise SystemExit(0 if all(c['control_agrees'] for c in observations) else 1)
