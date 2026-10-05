"""Integrate both original and bounded-repair attempts without replacing evidence."""
import base64,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];run=root/'runs/S03/repair-1'
markers=[json.loads(p.read_text()) for p in (run/'events').glob('*.json')];stages={}
for name in ['coordinator_setup','coordinator_receive','coordinator_review','coordinator_decision','coordinator_commit']:
 begin=[m for m in markers if m['stage']==name and m['event']=='begin'];end=[m for m in markers if m['stage']==name and m['event']=='end']
 assert len(begin)==len(end)==1 and begin[0]['boot_id']==end[0]['boot_id'] and begin[0]['monotonic_ns']<end[0]['monotonic_ns']
 stages[name]={'elapsed_seconds':(end[0]['monotonic_ns']-begin[0]['monotonic_ns'])/1e9,'begin':begin[0],'end':end[0]}
logs=[json.loads(p.read_text()) for p in (run/'logs').glob('*.json')]
assert len(logs)==23
for log in logs:
 assert log['actor']=='coordinator' and log['exit_code']==0
 for stream in ['stdout','stderr']:assert base64.b64decode(log[stream+'_base64'],validate=True).decode(errors='replace')==log[stream]
 assert log['begin']['boot_id']==log['end']['boot_id'] and log['begin']['monotonic_ns']<=log['end']['monotonic_ns']
review=json.loads((run/'review.json').read_text());assert review['passed']
commit=json.loads((run/'logs/021-commit.json').read_text());assert json.loads(commit['stdout'])['phase']=='committed'
assert (run/'expenses.csv').read_bytes()==(root/'runs/S03/native/expenses.csv').read_bytes()
assert (run/'plan.json').read_bytes()==(root/'runs/S03/native/plan.json').read_bytes()
result={'schema':'forge-s03-validation/2','status':'passed_after_bounded_repair','candidate':'C2','candidate_lock_sha256':hashlib.sha256((root/'runs/S02/candidate-lock.json').read_bytes()).hexdigest(),'total_new_ordinary_workers':2,'old_c1_native_calls':0,'unchanged_business_inputs':True,'unchanged_acceptance':True,'attempts':[{'path':'runs/S03/native','worker':'/root/luna_forge_fe59e381cb4d','business':'pass','worker_observed_protocol':'pass','coordinator_capture':'fail','worker_targets':11,'worker_corrections':0,'note':'Original passing overall grade is superseded by the retained post-commit review in repair-plan.json; original controller records are not rewritten.'},{'path':'runs/S03/repair-1','worker':'/root/luna_forge_d847e131cd3a','business':'pass','observed_protocol':'pass_with_disclosed_limits','coordinator_targets':23,'worker_targets':review['captured_worker_targets'],'worker_reported_corrections':0,'root_counted_worker_corrections':1,'worker_correction_reason':'Disclosed JavaScript tool-wrapper syntax retry before first shell target; retained in operations.json.','coordinator_repair_round':1,'repair_limit':2,'creates':1,'queries':2,'waits':0,'source_review_checks':len(review['checks']),'coordinator_stages':stages}], 'scope_limits':['Retains both attempts; no replacement, success-rate or performance claim.','Native raw returned objects are recorded by Root, not independently authenticated provider events.','Complete worker host-tool trace and host-enforced filesystem/tool containment are unavailable.','Administrative cloud/S01/repository integration commands are outside the measured sample target denominator; elapsed spans include their gaps.','Provider SDK/global limits/natural network faults/UI/external effects were not tested.'],'provider_tokens':None,'provider_cost':None,'provider_internal_identity':None,'evidence':['runs/S03/validation-initial.json','runs/S03/repair-plan.json','runs/S03/repair-1/review.json','runs/S03/repair-1/source-review.md','runs/S03/repair-1/logs/021-commit.json','runs/S03/repair-1/logs/022-reconcile.json']}
(root/'runs/S03/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'attempts':2,'worker_targets':[11,13],'coordinator_repair_round':1}))
