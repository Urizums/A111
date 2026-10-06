from pathlib import Path
import fcntl
import json
import os
import sys

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'scripts'))
import continuation as ctl

receipt=json.loads((root/'runs/R10/publication/source-push-receipt.json').read_text(encoding='utf-8'))
assert receipt['source_commit']==receipt['remote_commit'] and receipt['ci']['conclusion']=='success'
with (root/'state/coordinator.lock').open('a') as lock:
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    holder=dict(owner='root-codex-C8-publication-receipt',pid=os.getpid(),acquired_at=ctl.stamp(),scope='Actual short-lived single-checkout lease for receipt checkpoint')
    ctl.write_json(root/'state/coordinator-lease.json',holder)
    try:
        with ctl.locked(root):
            state=ctl.load(root)
            assert not ctl.validate(state,root)
            state['execution'].update(current_coordinator=holder['owner'],session_state='C8_source_published_development_checkpoint',publication_receipt='runs/R10/publication/source-push-receipt.json',publication_source_commit=receipt['source_commit'],source_ci=receipt['ci'],coordinator_release_evidence='runs/R10/publication/receipt-checkpoint-lease.json')
            state['events'].append(dict(at=ctl.stamp(),command='record_C8_source_publication',result=dict(source_commit=receipt['source_commit'],ci='success',behavior_passed=False,old_budgets_unchanged=True)))
            ctl.write_json(root/'state/continuation.json',state)
            ctl.synchronize(root,state)
            checkpoint=json.loads((root/'state/checkpoint.json').read_text(encoding='utf-8'))
            checkpoint.update(unpublished_work=False,publication_source_commit=receipt['source_commit'],publication_evidence_C8='runs/R10/publication/source-push-receipt.json',current_ci_C8=receipt['ci'])
            ctl.write_json(root/'state/checkpoint.json',checkpoint)
            project=json.loads((root/'state/project-todo.json').read_text(encoding='utf-8'))
            project['meta_workflow_scope_R10'].update(publication_pending=False,published_source_commit=receipt['source_commit'],source_ci='success',publication_receipt='runs/R10/publication/source-push-receipt.json')
            project['updated_at']=ctl.stamp()
            ctl.write_json(root/'state/project-todo.json',project)
    finally:
        holder['released_at']=ctl.stamp()
        ctl.write_json(root/'state/coordinator-lease.json',holder)
        ctl.write_json(root/'runs/R10/publication/receipt-checkpoint-lease.json',dict(acquired=True,released=True,holder=holder))
print(json.dumps(dict(source_publication_saved=True,source_ci='success',lease_released=True,old_failure_or_budget_changed=False)))
