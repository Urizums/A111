"""Save actual post-turn release and current frontier; no background schedule."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

probe = json.loads(subprocess.check_output([sys.executable, 'scripts/coordinator_lease.py',
    'probe', '--root', str(ROOT)], cwd=ROOT, text=True))
assert probe['busy'] is False
lease = json.loads((ROOT / 'state/coordinator-lease.json').read_text(encoding='utf-8'))
assert lease['owner'] == 'root-codex-r19-l4-resource-resume' and lease.get('released_at')
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = json.loads((ROOT / 'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    previous = json.loads((ROOT / 'runs/R20/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in previous.items())
    assert not state['execution']['current_native_pending']
    index_path = ROOT / 'state/revision-locks.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    relative = 'runs/R20/supplement-audit-1-lock.json'
    for entry in json.loads((ROOT / relative).read_text(encoding='utf-8'))['files']:
        data = (ROOT / entry['path']).read_bytes()
        assert len(data) == entry['size_bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']
    if relative not in index['locks']:
        index['locks'].append(relative)
    ctl.write_json(index_path, index)
    ci_receipt = json.loads((ROOT / 'runs/R19/publication/c12-accepted-r20-ci-final-observation-command.json').read_text(encoding='utf-8'))
    assert ci_receipt['state'] == 'finished' and ci_receipt['exit_code'] == 0
    ci = json.loads(ci_receipt['stdout'])
    assert ci['headSha'] == 'ca282442b11d63cf14d4fe8128c8cb552581e040'
    state['execution'].update(current_frontier_task='R20-01', current_report='runs/R20/REPORT.md',
        current_task_process_state='No live actors/pending calls. Actual first official audit and bounded supplement search saved; R20-01 remains incomplete, not a background scheduler.',
        final_lease_release='runs/R20/lease-release-observation.json',
        source_artifact_commit=ci['headSha'], final_source_ci_observation=ci,
        receipt_metadata_commit_pending=True)
    errors = ctl.validate(state, ROOT)
    assert not errors, errors
    ctl.write_json(ROOT / 'runs/R20/handback.json', dict(saved_at=ctl.stamp(), frontier='R20-01',
        R19='diagnostics_synthesis_successor_done', C12='scoped_first_forward_reception_pass',
        independent_b1_b5='pass', old_L3_a6='partial_preserved',
        actual_next_action='Precise current submission/AI supplement route; retain formal-rule/data unknowns, then freeze explicitly original data task for fresh handoff.',
        actors_pending=[], coordinator_release=dict(metadata=lease, probe=probe),
        source_commit=ci['headSha'], ci_status=ci['status'], ci_conclusion=ci['conclusion'],
        publication_scope='New code/papers/locks published; final observation and release receipts follow in metadata commit.',
        historical_tasks_preserved=len(previous), original_tasks_preserved=len(old),
        budgets_reset=False, background_schedule=False, model=None, tokens=None, cost=None))
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
    cp_path = ROOT / 'state/checkpoint.json'
    cp = json.loads(cp_path.read_text(encoding='utf-8'))
    cp.update(current_frontier_task='R20-01', current_report='runs/R20/REPORT.md',
        current_native_pending=[], next_action='R20-01: use precise current official supplement/platform route; append evidence, retain unknowns, then freeze explicitly original data workflow task.',
        handback='runs/R20/handback.json', termination='phase_result_and_actual_successor_first_step_saved_no_live_actor',
        actual_lease_release='runs/R20/lease-release-observation.json',
        source_artifact_commit=ci['headSha'], final_source_ci_observation=ci,
        receipt_commit_pending_at_this_snapshot=True, unpublished_work=True)
    ctl.write_json(cp_path, cp)
print(json.dumps(dict(frontier='R20-01', lease_released_and_probe_free=True,
    old_tasks_unchanged=len(old), previous_tasks_unchanged=len(previous),
    registered_locks=len(index['locks']), queue_valid=True, source_ci=ci['status'] + '/' + ci['conclusion'])))
