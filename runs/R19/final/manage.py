"""Root-only reuse of the existing queue/locks for R19 synthesis."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser();p.add_argument('action',choices=['start','actor','freeze','finish']);p.add_argument('--actor');p.add_argument('--status');p.add_argument('--scope');p.add_argument('--lock');a=p.parse_args()
with ctl.locked(ROOT):
    state=ctl.load(ROOT);old=json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    if a.action=='start':
        assert all(ctl.task_map(state)[f'R19-L{k}']['status']=='done' for k in range(1,5))
        ctl.begin(state,ROOT,'R19-05','runs/R19/final/comparison-first-step-command.json')
    elif a.action=='actor':
        assert a.actor.startswith('/root/r19_c12_') and a.status in ['running','completed']
        prefix='runs/R19/final/actor-'+a.actor.rsplit('/',1)[-1]+'-'+a.status
        serial=1;path=prefix+'.json'
        while (ROOT/path).exists():serial+=1;path=prefix+'-'+str(serial)+'.json'
        ctl.write_json(ROOT/path,dict(actor=a.actor,state=a.status,observed_at=ctl.stamp(),provenance='Actual parent collaboration tool return/status; not authenticated provider telemetry',model=None,tokens=None,cost=None))
        pending=[v for v in state['execution'].get('current_native_pending',[]) if v['worker']!=a.actor]
        row=dict(worker=a.actor,state=a.status,evidence=path,actual_model=None)
        if a.status=='running':pending.append(row)
        else:state['execution'].setdefault('completed_native_R19',[]).append(row)
        state['execution'].update(current_native_pending=pending,native_pending_current=pending)
    elif a.action=='freeze':
        scope=(ROOT/a.scope).resolve();lock=(ROOT/a.lock).resolve();allowed=(ROOT/'runs/R19/final').resolve()
        assert scope.is_relative_to(allowed) and lock.is_relative_to(allowed) and not lock.exists()
        files=[]
        for f in sorted(scope.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:
                b=f.read_bytes();files.append(dict(path=f.relative_to(ROOT).as_posix(),size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        assert files
        ctl.write_json(lock,dict(schema='forge-revision-lock/1',revision=a.scope,frozen_at=ctl.stamp(),files=files,claim='Actual terminal bytes/identity only; acceptance remains separate.'))
        index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'));index['locks'].append(lock.relative_to(ROOT).as_posix());ctl.write_json(ROOT/'state/revision-locks.json',index)
        print(json.dumps(dict(frozen_scope=a.scope,files=len(files))))
    elif a.action=='finish':
        assert not state['execution']['current_native_pending']
        ctl.finish(state,ROOT,'R19-05','runs/R19/final/result.json')
    state['execution'].update(current_frontier_task='R19-05',current_report='runs/R19/REPORT.md',current_task_process_state='R19-05 source-bound synthesis/targeted forward check; historical four verdicts preserved.')
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'));cp.update(current_frontier_task='R19-05',current_native_pending=state['execution'].get('current_native_pending',[]),current_report='runs/R19/REPORT.md',next_action='Complete evidence-based C12 document-only revision and relevant fresh forward check; then justified R20 plan and actual first step.',termination=None,unpublished_work=True);ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(action=a.action,old_tasks_unchanged=len(old),task_status=ctl.task_map(state)['R19-05']['status'])))
