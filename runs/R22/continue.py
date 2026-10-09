"""Serial R22 continuation; old tasks, requirements, failures and locks stay intact."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser(); p.add_argument('action',choices=['claim','freeze','bind','start','finish','actor','recovery','recovery-derived'])
for name in ['task','receipt','result','scope','lock','actor','status','lease-session']: p.add_argument('--'+name)
a=p.parse_args()
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
with ctl.locked(ROOT):
    state=ctl.load(ROOT); tasks=ctl.task_map(state)
    before='runs/R22/before-execution/task-identities.json'
    if a.action=='claim':
        assert not (ROOT/before).exists()
        ctl.write_json(ROOT/before,{k:ctl.identity(v) for k,v in tasks.items()})
        lease=read('state/coordinator-lease.json')
        assert lease['owner']=='root-codex-r22-horizon' and not lease.get('released_at')
        state['execution'].setdefault('historical_coordinator_snapshots',[]).append(dict(at=ctl.stamp(),fields={
            k:state['execution'].get(k) for k in ['current_coordinator','coordinator_heartbeat','final_lease_release','coordinator_release_evidence']}))
        state['execution'].update(current_coordinator=lease['owner'],coordinator_heartbeat=ctl.stamp(),
            actual_lease_pid=lease['pid'],actual_lease_session=int(a.lease_session),final_lease_release=None,coordinator_release_evidence=None)
    old=read(before)
    protected={k:v for k,v in old.items() if k not in ['R22-02','R22-03','R22-next']}
    assert all(ctl.identity(tasks[k])==v for k,v in protected.items())
    if a.action=='freeze':
        folder=(ROOT/a.scope).resolve(); lock=(ROOT/a.lock).resolve()
        assert folder.is_relative_to(ROOT/'runs/R22') and lock.is_relative_to(ROOT/'runs/R22') and not lock.exists()
        entries=[]
        for f in sorted(folder.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:
                b=f.read_bytes()
                if f.suffix=='.json':
                    j=json.loads(b)
                    if isinstance(j,dict) and j.get('schema')=='forge-command-record/1':assert j['state']=='finished',str(f)
                entries.append(dict(path=f.relative_to(ROOT).as_posix(),size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        assert entries
        ctl.write_json(lock,dict(schema='forge-revision-lock/1',revision=a.scope,frozen_at=ctl.stamp(),files=entries,
            claim='Frozen byte identity of actual terminal artifacts; substantive independent reception separate.'))
        index=read('state/revision-locks.json');assert a.lock not in index['locks'];index['locks'].append(a.lock)
        ctl.write_json(ROOT/'state/revision-locks.json',index)
        print(json.dumps(dict(frozen_files=len(entries),lock=a.lock)))
    elif a.action=='bind':
        task=tasks['R22-02']; assert task['status']=='planned' and not task['attempts']
        for rel in ['runs/R22/protocol-lock.json','runs/R21/input-lock.json','runs/R21/execution-lock.json','runs/R20/final/candidate/C13-lock.json']:
            assert (ROOT/rel).is_file()
            if rel not in task['inputs']:task['inputs'].append(rel)
    elif a.action=='recovery':
        task=tasks['R22-02'];assert task['status']=='failed'
        verdict=read('runs/R22/review/initial/result.json')
        assert verdict['criterion_statuses']==dict(h1='pass',h2='pass',h3='pass',h4='pass',h5='pass',h6='fail')
        task['recovery_note']=dict(
            observation='First independent h6 fails on inconsistent two-decimal presentation of 340.075; first verdict and all artifacts retained.',
            change_or_new_information='Document-only new renderer uses a declared Decimal ROUND_HALF_UP display rule; also reconcile repeated monetary values, preserve original scientific source/config/results.',
            expected_check='Informed independent h6 recheck of complete corrected Chinese MD and every final PDF page; carry h1-h5 only with original locked science identity unchanged.',
            category='substantive document consistency correction, not scientific refit or reviewer tool errors',
            evidence=[ctl.ref(ROOT,r) for r in ['runs/R22/initial-reception-lock.json','runs/R22/review/initial/result.json','runs/R22/execution-lock.json']])
    elif a.action=='recovery-derived':
        task=tasks['R22-02'];assert task['status']=='failed' and task['repairs_used']==1
        failed=read('runs/R22/execution/correction-v2/receipts/0006-full-document-selfcheck.json')
        assert failed['state']=='finished' and failed['exit_code']==1
        task['recovery_note']=dict(
            observation='v2 author check actually failed: published CSV decimal subtraction and float-first subtraction differ in a half-cent case. Original independent h6 rejection remains unchanged; no independent v2 judgment exists.',
            change_or_new_information='New v3 renderer performs displayed monetary subtraction and paired means/min/max directly on original published CSV decimal text before ROUND_HALF_UP. Context-summary exposure during v2 waiting is disclosed; no scientific refit.',
            expected_check='Complete author monetary audit and actual final-page inspection, followed by informed independent h6 reception. Scientific h1-h5 carried only after byte identity verification.',
            category='substantive document consistency correction 2; not tool recovery or scientific tuning',
            evidence=[ctl.ref(ROOT,r) for r in ['runs/R22/document-correction-v2-lock.json','runs/R22/R22-02-v2-result.json','runs/R22/execution/correction-v2/derived-monetary-counterexamples.json','runs/R22/create-correction-v3-command.json']])
    elif a.action=='start':ctl.begin(state,ROOT,a.task,a.receipt)
    elif a.action=='finish':ctl.finish(state,ROOT,a.task,a.result)
    elif a.action=='actor':
        assert a.actor.startswith('/root/r22_') and a.status in ['running','completed','interrupted']
        actor=a.actor.rsplit('/',1)[-1]; folder=ROOT/'runs/R22/coordination-current';folder.mkdir(exist_ok=True)
        serial=1
        while (folder/f'{actor}-{a.status}-{serial}.json').exists():serial+=1
        rel=f'runs/R22/coordination-current/{actor}-{a.status}-{serial}.json'
        ctl.write_json(ROOT/rel,dict(actor=a.actor,status=a.status,observed_at=ctl.stamp(),model=None,tokens=None,cost=None,
            scope='Actual collaboration status; local read/write scopes are not OS isolation.'))
        pending=[r for r in state['execution']['current_native_pending'] if r['worker']!=a.actor]
        row=dict(worker=a.actor,state=a.status,evidence=rel,actual_model=None)
        if a.status=='running':pending.append(row)
        else:state['execution'].setdefault('completed_native_R22',[]).append(row)
        state['execution'].update(current_native_pending=pending,native_pending_current=pending)
    frontier=next((k for k in ['R22-02','R22-03','R22-next'] if tasks[k]['status']!='done'),'R22-next')
    state['execution'].update(current_frontier_task=frontier,current_report='runs/R22/REPORT.md',
        current_task_process_state='R22 fixed same-horizon historical research; actual actors recorded separately.')
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in protected.items())
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_frontier_task=frontier,current_report='runs/R22/REPORT.md',
        current_native_pending=state['execution']['current_native_pending'],next_action=tasks[frontier]['next_action'],termination=None,unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(action=a.action,frontier=frontier,protected_tasks=len(protected),queue_valid=True)))
