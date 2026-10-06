"""Publication metadata only; does not retry or alter adoption acceptance."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl

receipt=json.loads((ROOT/'runs/R13/publication/source-receipt.json').read_text(encoding='utf-8'))
assert receipt['local_commit']==receipt['remote_commit']
with (ROOT/'state/coordinator.lock').open('a') as coordinator:
    fcntl.flock(coordinator.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    previous=json.loads((ROOT/'state/coordinator-lease.json').read_text(encoding='utf-8'))
    assert previous.get('released_at')
    info=dict(owner='root-codex-r12-r13-publication-receipt',pid=os.getpid(),acquired_at=ctl.stamp(),
              scope='Actual single-checkout fcntl lease for receipt checkpoint only')
    ctl.write_json(ROOT/'state/coordinator-lease.json',info)
    with ctl.locked(ROOT):
        state=ctl.load(ROOT)
        assert ctl.task_map(state)['R13-01']['status']=='blocked'
        state['execution'].update(session_state='R12_research_and_R13_failure_published',
            R12_R13_publication_receipt='runs/R13/publication/source-receipt.json',
            R12_R13_publication_source_commit=receipt['local_commit'],
            coordinator_release_evidence='runs/R13/publication/receipt-lease.json')
        state['events'].append(dict(at=ctl.stamp(),command='record_development_publication',result=dict(source_commit=receipt['local_commit'],adoption_passed=False)))
        ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
        cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
        cp.update(unpublished_work=False,R12_R13_published_source_commit=receipt['local_commit'],
                 R12_R13_publication_receipt='runs/R13/publication/source-receipt.json')
        ctl.write_json(ROOT/'state/checkpoint.json',cp)
        project=json.loads((ROOT/'state/project-todo.json').read_text(encoding='utf-8'))
        project['evaluation_protocol_R12'].update(published_source_commit=receipt['local_commit'],publication_pending=False)
        project['protocol_adoption_R13'].update(published_source_commit=receipt['local_commit'],publication_scope='Actual failed adoption and rollback evidence, not adopted protocol')
        ctl.write_json(ROOT/'state/project-todo.json',project)
    info['released_at']=ctl.stamp();ctl.write_json(ROOT/'state/coordinator-lease.json',info)
    ctl.write_json(ROOT/'runs/R13/publication/receipt-lease.json',dict(previous=previous,actual=info,released=True))
print(json.dumps(dict(source_commit=receipt['local_commit'],unpublished_work=False,lease_released=True,adoption_passed=False)))
