"""Bind the actual resumed terminal CI receipt; no invented extra network query."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
rel='runs/R23/resume-ci-command.json';receipt=read(rel)
assert receipt['state']=='finished' and receipt['exit_code']==0
raw=json.loads(receipt['stdout'])
assert raw['headSha']=='6d2222d198ebafcbdd3faab4f2a8905cdd7c22be'
assert raw['status']=='completed' and raw['conclusion']=='success'
assert len(raw['jobs'])==3 and all(j['status']=='completed' and j['conclusion']=='success' for j in raw['jobs'])
row=dict(databaseId=37920111228,headSha=raw['headSha'],status=raw['status'],conclusion=raw['conclusion'],url=raw['url'],workflowName='Cloud delivery validation')
with ctl.locked(ROOT):
    state=ctl.load(ROOT);tasks=ctl.task_map(state);before=read('runs/R23/before-execution/task-identities.json')
    protected={k:v for k,v in before.items() if k not in {'R23-02','R23-03','R23-04','R23-next'}}
    assert all(ctl.identity(tasks[k])==v for k,v in protected.items())
    serial=1
    while (ROOT/f'runs/R19/publication/observation-{serial}.json').exists():serial+=1
    evidence=f'runs/R19/publication/observation-{serial}.json'
    ctl.write_json(ROOT/evidence,dict(observed_at=receipt['end']['utc'],source_commit=raw['headSha'],ci=[row],jobs=raw['jobs'],actual_query_receipt=ctl.ref(ROOT,rel),scope='Actual terminal CI for the previous main submission. No new remote-main assertion and no scientific/skill-quality inference.'))
    state['execution'].update(current_source_ci=[row],current_source_ci_observed=receipt['end']['utc'],current_publication=evidence)
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_source_ci=[row],publication_evidence=evidence);ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(actual_ci=row,query_receipt=rel,evidence=evidence,protected_tasks=len(protected))))
