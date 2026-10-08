"""Preparation identity/invariant check only; never reads revised execution."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import platform
import time

started = time.perf_counter()
here = Path(__file__).resolve().parent
root = here.parents[3]
assert root.name == 'R19'
sources = [
    root / 'acceptance.json', root / 'quality-diagnosis.md',
    root / 'levels/L3/review/preparation/review-plan.md',
    root / 'levels/L3/review/preparation/independent_checker.py',
    root / 'levels/L3/review/initial/result.json',
    root / 'levels/L3/review/initial/report.md',
    root / 'levels/L3/review/initial/figure-paper-audit.json',
    root / 'levels/L3/review/initial/retention-and-method-check.json',
]
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, obj):
    (here / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
initial = json.loads(sources[4].read_text(encoding='utf-8-sig'))
acceptance = json.loads(sources[0].read_text(encoding='utf-8-sig'))
baseline = {
    'phase': 'first_review_preserved_not_regraded',
    'status': initial['status'],
    'a1_a6': initial['a1_a6'],
    'quality_diagnosis': initial['quality_diagnosis'],
    'not_verified': initial['not_verified'],
    'historical_evidence_limit_remains': True,
    'source_identity': [{'path': p.relative_to(root).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in sources],
}
write('baseline.json', baseline)
plan = (here / 'review-plan.md').read_text(encoding='utf-8')
checks = {
    'initial_mandatory_ids_unchanged': [x['id'] for x in initial['a1_a6']] == [f'a{i}' for i in range(1,7)],
    'initial_four_pass_one_fail_one_partial': dict(collections.Counter(x['status'] for x in initial['a1_a6'])) == {'pass':4,'fail':1,'partial':1},
    'initial_quality_three_achieved_three_partial': dict(collections.Counter(x['status'] for x in initial['quality_diagnosis'])) == {'achieved':3,'partial':3},
    'six_frozen_quality_dimensions_preserved': [x['dimension'] for x in initial['quality_diagnosis']] == acceptance['quality_diagnosis'],
    'future_freeze_gate_present': '正式授权之后' in plan and '没有读取活动' in plan,
    'full_chinese_reasoning_read_present': '逐节读完整新 paper' in plan and '不预设后续 AI 润色' in plan,
    'pdf_semantics_not_glyph_quota': '不能仅匹配 Unicode 出现次数' in plan,
    'history_not_reconstructed': '不能通过新运行追认恢复' in plan,
    'changed_scope_run_and_unrerun_disclosure': '按依赖关系实际干净运行' in plan and '本次未重新运行' in plan,
    'source_files_unchanged_during_prep': all(sha(root/x['path']) == x['sha256'] for x in baseline['source_identity']),
}
assert all(checks.values()), checks
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
write('method-selfcheck.json', {
    'kind':'preparation_consistency_only_not_scientific_acceptance',
    'checks':checks,'passed':sum(checks.values()),'total':len(checks),
    'limits':['Checks presence and consistency of preparation requirements only; does not judge any revised scientific text, rendering or numeric output.'],
    'python':platform.python_version(),'platform':platform.platform(),
    'elapsed_seconds':time.perf_counter()-started,'finished_at_utc':now,
    'exit_code':0,'pending_calls':[],'active_self_started_processes':[],
})
write('result.json', {
    'task_id':'R19-C11-L3-informed-recheck-1-preparation',
    'role':'/root/r19_l3_reviewer','phase':'informed_recheck_preparation_only',
    'status':'preparation_completed_waiting_frozen_revision',
    'first_review_summary':{'pass':4,'fail':1,'partial':1,'overall':initial['status']},
    'first_review_quality_summary':{'achieved':3,'partial':3,'missing':0},
    'revision_received':False,'revision_verdict':None,
    'new_a1_a6':[{'id':f'a{i}','status':'pending_not_received','evidence':[], 'reason':'Only method preparation authorized; frozen revision not received.'} for i in range(1,7)],
    'new_quality_diagnosis':[{'dimension':d,'status':'pending_not_received'} for d in acceptance['quality_diagnosis']],
    'historic_receipts_recovered':False,'old_evidence_retroactively_accepted':False,
    'chinese_argument_quality_current_delivery':True,
    'read_activity':{'revised_execution':False,'other_levels':False,'root_synthesis_or_state':False},
    'network_used':False,'software_installed':False,'uploaded':False,'author_messaged':False,
    'model':None,'token_usage':None,'cost':None,'whole_task_deadline':None,
    'pending_calls':[],'active_self_started_processes':[],'child_agents':[],
    'all_own_calls_terminal':True,
    'finished_at_utc':now,
    'next_action':'Root freezes these preparation artifacts; reviewer stops until formal revised-packet authorization.',
})
payload = sorted(p for p in here.rglob('*') if p.is_file() and p.name != 'manifest.json')
manifest = {'phase':'recheck_1_preparation_only','generated_at_utc':now,
    'payload_count':len(payload),'files':[{'path':p.relative_to(here).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in payload],
    'manifest_excludes_itself':True,'all_self_started_processes_terminal':True}
write('manifest.json', manifest)
print(json.dumps({'status':'preparation_completed_waiting_frozen_revision','method_checks':checks,'payload_count':len(payload),'manifest_sha256':sha(here/'manifest.json')},ensure_ascii=False))
