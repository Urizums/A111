import copy,hashlib,itertools,json,math,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
PROD=ROOT/'runs/R19/final/forward/production'
PREP=ROOT/'runs/R19/final/forward/review-preparation'
RAW=ROOT/'runs/R19/final/forward/inputs/raw.json'
sys.path.insert(0,str(PREP))
from independent_check import check,finite
raw=json.loads(RAW.read_text(encoding='utf-8-sig'))
digest=hashlib.sha256(RAW.read_bytes()).hexdigest()

def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def canonical(solution):
    vids=sorted(set(p['vehicle_id'] for p in solution['placements']))
    return dict(vehicles=[dict(id=v,type_id=solution['vehicle_type_id']) for v in vids],
        placements=copy.deepcopy(solution['placements']),
        vehicle_count=solution['objective']['vehicle_count'],total_cost_CNY=solution['objective']['total_cost_CNY'])
def receive(solution,data=raw,bound=True):
    r=check(data,canonical(solution))
    if bound and solution.get('source_sha256') != digest:
        r['errors'].append(dict(code='source_hash_conflict')); r['valid']=False
    supports=(r.get('recomputed') or {}).get('support',{})
    for p in solution['placements']:
        if p['item_id'] in supports and ('support_id' not in p or p['support_id'] != supports[p['item_id']]):
            r['errors'].append(dict(code='declared_support_conflict',item_id=p['item_id']));r['valid']=False
    return r

new=load(HERE/'consumer-solution.json')
original=load(PROD/'solution.json')
solution_checks={'newly_executed':receive(new),'frozen_original':receive(original)}
semantic_keys=['schema','source_sha256','vehicle_type_id','placements','objective','optimality']
semantic_match=all(new[k]==original[k] for k in semantic_keys)

# Independent instance-specific oracle: append each permutation to two physical
# columns per truck, with no producer legal-chain implementation or checker.
# Completeness for THIS source: all y intervals overlap, so floor has <=2 columns;
# equal footprints force every support chain to have common x/y; any chains fit grid.
ids=sorted(p['item_id'] for p in new['placements'])
def oracle(data):
    v=data['vehicles'][0]
    tried=0
    for fleet in range(1,len(ids)+1):
        for order in itertools.permutations(ids):
            for slots in itertools.product(range(2*fleet),repeat=len(ids)):
                heights=[0]*(2*fleet); tops=[None]*(2*fleet); poses=[]
                for name,slot in zip(order,slots):
                    poses.append(dict(item_id=name,vehicle_id=f'oracle-{slot//2}',
                        x_m=slot%2,y_m=0,z_m=heights[slot],support_id=tops[slot]))
                    heights[slot]+=1;tops[slot]=name
                if max(heights)>3 or len(set(p['vehicle_id'] for p in poses)) != fleet: continue
                candidate=dict(source_sha256=None,vehicle_type_id=v['id'],placements=poses,
                               objective=dict(vehicle_count=fleet,total_cost_CNY=fleet*v['cost_CNY']))
                tried+=1
                r=receive(candidate,data,False)
                if r['valid']:
                    return dict(objective=candidate['objective'],candidate=candidate,independent_check=r,
                        full_candidates_examined=tried,smaller_counts_exhausted=list(range(1,fleet)))
    return dict(infeasible=True,full_candidates_examined=tried)

experiments=load(HERE/'consumer-experiments.json')
bas=experiments['floor_only_baseline']['solution']
baseline=receive(bas)
variants=[]
for v in experiments['parameter_variants']:
    data=copy.deepcopy(raw);data['standard_limit_kg_per_m2']=v['standard_limit_kg_per_m2'];data['vehicles'][0]['payload_kg']=v['payload_kg']
    s=dict(source_sha256=None,vehicle_type_id='T',placements=v['placements'],objective=v['objective'])
    recompute=receive(s,data,False)
    independent=oracle(data)
    variants.append(dict(case=v['case'],parameters=dict(standard_limit_kg_per_m2=v['standard_limit_kg_per_m2'],payload_kg=v['payload_kg']),
        actual_producer_objective=v['objective'],independent_recompute=recompute,independent_optimum=independent,
        objective_matches_independent_oracle=v['objective']==independent.get('objective')))
save(HERE/'independent-recomputation.json',dict(new_and_original=solution_checks,solution_semantic_match=semantic_match,
    original_optimality=dict(positive_nonempty_source_lower_bound=1,achieved=solution_checks['newly_executed']['recomputed']['lexicographic_objective'][0],
        conclusion='Achieved one and nonempty lower bound one independently close optimum; identical fixed cost closes secondary objective'),
    baseline=baseline,variants=variants,oracle_scope='Only original four equal unit cubes, one homogeneous type and the listed load/payload variants; structural two-column completeness stated in code'))

# Actual paired reception via frozen verify.py CLI. Controls remain in review.
pairs=HERE/'pairs';pairs.mkdir(exist_ok=True)
cases=[('valid_rerun',copy.deepcopy(new),True,None)]
triple=copy.deepcopy(new)
triple['placements']=[dict(item_id=i,vehicle_id='T1',x_m=x,y_m=0,z_m=z,support_id=s)
    for i,x,z,s in [('S1',0,0,None),('S2',0,1,'S1'),('F1',0,2,'S2'),('S3',1,0,None)]]
cases.append(('recursive_overload',triple,False,'cumulative_standard_load'))
for name,mutate,code in [
    ('source_category',lambda s:s['placements'][0].update(category='standard'),'item_source_conflict'),
    ('source_mass',lambda s:s['placements'][0].update(mass_kg=1),'item_source_conflict'),
    ('source_dimensions',lambda s:s['placements'][0].update(length_m=0.5),'item_source_conflict'),
    ('source_vehicle',lambda s:s.update(vehicle_type_id='different-type'),'unknown_vehicle_type'),
    ('source_hash',lambda s:s.update(source_sha256='wrong'),'source_hash_conflict'),
    ('declared_neighbor_support',lambda s:s['placements'][0].update(support_id='S2'),'declared_support_conflict'),
    ('missing',lambda s:s['placements'].pop(),'item_multiplicity'),
    ('duplicate',lambda s:s['placements'].append(copy.deepcopy(s['placements'][0])),'item_multiplicity'),
    ('objective_nan',lambda s:s['objective'].update(total_cost_CNY=float('nan')),'objective_report_conflict'),
    ('objective_inf',lambda s:s['objective'].update(vehicle_count=float('inf')),'objective_report_conflict'),
    ('dimension_inf',lambda s:s['placements'][0].update(height_m=float('inf')),'item_source_conflict'),
]:
    s=copy.deepcopy(new);mutate(s);cases.append((name,s,False,code))
for axis in ('x_m','y_m','z_m'):
    for value,name in [(float('nan'),'nan'),(float('inf'),'inf'),(-float('inf'),'minus_inf')]:
        s=copy.deepcopy(new);s['placements'][0][axis]=value;cases.append((axis+'_'+name,s,False,'coordinate_domain'))
fragile=copy.deepcopy(new)
fragile['placements']=[dict(item_id=i,vehicle_id='T1',x_m=x,y_m=0,z_m=z,support_id=s)
    for i,x,z,s in [('F1',0,0,None),('S1',0,1,'F1'),('S2',1,0,None),('S3',1,1,'S2')]]
fragile['placements'][0]['category']='standard'
cases.append(('fragile_identity_laundering',fragile,False,'fragile_bears_cargo'))
observations=[]
for name,s,expected,code in cases:
    path=pairs/(name+'-solution.json');out=pairs/(name+'-checks.json')
    # Deliberate JSON NaN/Inf token accepted by Python decoder, then required to reject.
    path.write_text(json.dumps(s,ensure_ascii=False,indent=2,allow_nan=True)+'\n',encoding='utf-8')
    command=[sys.executable,'-B','-X','pycache_prefix='+str(HERE/'bytecode-not-used'),str(PROD/'verify.py'),'--input',str(RAW),'--solution',str(path),'--output',str(out)]
    started=time.perf_counter()
    r=subprocess.run(command,cwd=PROD,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,encoding='utf-8',errors='replace')
    actual=load(out) if out.exists() else None
    ind=receive(s)
    agrees=actual is not None and actual['valid']==expected and ind['valid']==expected and (r.returncode==0)==expected
    if code: agrees=agrees and any(e['code']==code for e in ind['errors'])
    observations.append(dict(case=name,expected_acceptance=expected,independent=ind,actual_receiver=actual,
        actual_receipt=dict(command=command,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,
            elapsed_seconds=time.perf_counter()-started,state='finished'),paired_assertion_agrees=agrees))
save(HERE/'paired-receiving-observations.json',dict(pairing='Every invalid variant is paired with same source and valid_rerun; actual frozen CLI plus own logic',
    cases=observations,all_agree=all(c['paired_assertion_agrees'] for c in observations),
    false_acceptances=sum(not c['expected_acceptance'] and c['actual_receiver']['valid'] for c in observations),
    false_rejections=sum(c['expected_acceptance'] and not c['actual_receiver']['valid'] for c in observations),
    all_started_processes_terminal=True))

# Original workflow smoke activation, not simply accepting author's test labels.
tests=load(HERE/'consumer-tests.json')
smoke=[]
for c in tests['cases']:
    s=c.get('mutated_solution') or (new if c['case']=='original_valid' else None)
    if s is not None:
        own=receive(s)
        smoke.append(dict(case=c['case'],author_actual_received=c['accepted'],own_check=own,
            agreement=own['valid']==c['accepted']))
save(HERE/'smoke-activation.json',dict(selected_from_workflow=['Raw solve-to-receive-to-paper actual result','Relevant three-level cumulative overload rejection'],
    original_activation=solution_checks['newly_executed']['recomputed']['activation'],
    actual_three_level_receiver=next(c for c in observations if c['case']=='recursive_overload'),
    self_test_artifacts_rechecked=smoke,
    limits='Payload modified case checked through parameter variants; NaN tested separately through actual CLI; no author assertion_passed is treated as oracle'))
print(json.dumps(dict(independent_valid=solution_checks['newly_executed']['valid'],semantic_match=semantic_match,
    variant_oracle_matches=all(v['objective_matches_independent_oracle'] for v in variants),
    receiver_cases=len(observations),all_pairs_agree=all(c['paired_assertion_agrees'] for c in observations)),ensure_ascii=False))
