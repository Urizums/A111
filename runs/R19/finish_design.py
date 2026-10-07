"""Close design preparation only after real terminal delivery and byte freeze."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
level=int(sys.argv[1])
base=f'runs/R19/levels/L{level}'
lock=json.loads((ROOT/base/'design-lock.json').read_text(encoding='utf-8'))
for row in lock['files']:
    data=(ROOT/row['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256']
for name in ['workflow.md','handoff.md','TODO.md','result.json']:
    assert (ROOT/base/'design'/name).is_file()
with ctl.locked(ROOT):
    state=ctl.load(ROOT);task=ctl.task_map(state)[f'R19-D{level}'];assert task['status']=='in_progress'
    outcome=f'{base}/design-preparation-result.json'
    ctl.write_json(ROOT/outcome,dict(task_id=task['id'],attempt_id=task['attempts'][-1]['id'],requirements_hash=ctl.identity(task['acceptance']),
        criteria=[dict(id='d1',status='pass',evidence=[f'{base}/design-lock.json',f'{base}/design/result.json'])],
        effect=dict(target='Independent design preparation',hypothesis='Transferability will be tested by a different executor.',baseline='Same C11/raw problem and own exact level input',
            conditions='Design only, separate context and write domain',observations=f"{len(lock['files'])} actual files frozen; no execution/paper claim",
            limits='Scientific quality and workflow usability remain untested',metrics=dict(design_artifacts=len(lock['files']),papers=0)),
        next_action=f'Wait for sequential R19-L{level} execution after predecessor diagnosis; do not count design pass as paper acceptance.'))
    ctl.finish(state,ROOT,task['id'],outcome)
    state['execution'].setdefault('R19_prepared_designs',[]).append(dict(level=level,lock=f'{base}/design-lock.json',runtime_accepted=False))
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
print(json.dumps(dict(preparation_task=task['id'],status=task['status'],runtime_accepted=False)))
