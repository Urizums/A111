"""Final shared checkpoint under an actual short-lived coordinator lease."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import sys

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'scripts'))
import continuation as ctl

with (root/'state/coordinator.lock').open('a') as lock:
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    old=json.loads((root/'state/coordinator-lease.json').read_text(encoding='utf-8'))
    assert old.get('released_at'), 'Previous actual coordinator must release first'
    holder=dict(owner='root-codex-c8-final-checkpoint',pid=os.getpid(),acquired_at=ctl.stamp(),scope='Actual short-lived single-checkout advisory lease; no distributed guarantee')
    ctl.write_json(root/'state/coordinator-lease.json',holder)
    try:
        with ctl.locked(root):
            state=ctl.load(root)
            assert not ctl.validate(state,root)
            state['execution'].update(session_state='development_candidate_checkpoint',current_report='runs/R10/REPORT.md',current_native_pending=[],native_pending=[],coordinator_heartbeat=ctl.stamp(),coordinator_release_evidence='runs/R10/publication/lease-release.json',final_checkpoint_lease='runs/R10/publication/final-checkpoint-lease.json',checkpoint_reason='C8 document-only candidate and actual standalone package; R09 independent checks done; R10 original actor3/2 blocked, dependent R11 continuation blocked; budgets/history preserved')
            state['events'].append(dict(at=ctl.stamp(),command='C8_development_checkpoint',result=dict(R09_02='done',R10_01='done',R10_02='blocked3_over2',R11_01='done_actual_successor_first_step',R11_02='blocked_dependency',old_budgets_changed=False,full_acceptance_passed=False)))
            ctl.write_json(root/'state/continuation.json',state)
            ctl.synchronize(root,state)
            checkpoint=json.loads((root/'state/checkpoint.json').read_text(encoding='utf-8'))
            checkpoint.update(current_native_pending=[],unpublished_work=True,publication_scope='C8 development candidate and evidence; independent behavior/full product not accepted',C8_delivery=dict(source='runs/R10/candidate/C8-lock.json',package='runs/R11/package/Forge-C8-meta-workflow.zip',behavior_passed=False,personal_installation=False),next_action='Retain exhausted original cases and dependent blockers; do not fabricate a ready task or reset budget',R09_branch=dict(status='done_with_actual_R11_successor',evidence='runs/R09/R09-02-result.json'),R11_branch=dict(packaging='done',actual_first_step='runs/R11/package/first-command.json',continuation='blocked_dependency'))
            ctl.write_json(root/'state/checkpoint.json',checkpoint)
            project=json.loads((root/'state/project-todo.json').read_text(encoding='utf-8'))
            project['meta_workflow_scope_R10'].update(publication_scope='authorized development candidate and evidence',publication_pending=True,behavior_passed=False)
            project['updated_at']=ctl.stamp()
            ctl.write_json(root/'state/project-todo.json',project)
            archive=root/'runs/R11/package/Forge-C8-meta-workflow.zip'
            raw=archive.read_bytes()
            package_lock=root/'runs/R11/package/package-lock.json'
            assert not package_lock.exists()
            ctl.write_json(package_lock,dict(schema='forge-method-package-lock/1',source='runs/R10/candidate/C8-lock.json',files=[dict(path=archive.relative_to(root).as_posix(),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())],claim='Exact archive identity; no independent behavior pass'))
            index=json.loads((root/'state/revision-locks.json').read_text(encoding='utf-8'))
            assert package_lock.relative_to(root).as_posix() not in index['locks']
            index['locks'].append(package_lock.relative_to(root).as_posix())
            ctl.write_json(root/'state/revision-locks.json',index)
    finally:
        holder['released_at']=ctl.stamp()
        ctl.write_json(root/'state/coordinator-lease.json',holder)
        ctl.write_json(root/'runs/R10/publication/final-checkpoint-lease.json',dict(acquired=True,released=True,holder=holder,previous_released_holder=old))
print(json.dumps(dict(checkpoint_saved=True,short_lease_released=True,old_budgets_unchanged=True,C8_behavior_passed=False)))
