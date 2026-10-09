"""Serial R23 continuation under unchanged source/requirements and old task identities."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser();p.add_argument('action',choices=['claim','start','finish','freeze','actor','recovery','close'])
for name in ['task','receipt','result','scope','lock','actor','status','lease-session','note']:p.add_argument('--'+name)
a=p.parse_args()
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
with ctl.locked(ROOT):
    state=ctl.load(ROOT);tasks=ctl.task_map(state)
    snapshot='runs/R23/before-execution/task-identities.json'
    if a.action=='claim':
        assert not (ROOT/snapshot).exists() and not state['execution']['current_native_pending']
        ctl.write_json(ROOT/snapshot,{k:ctl.identity(t) for k,t in tasks.items()})
        lease=read('state/coordinator-lease.json');assert lease['owner']=='root-codex-r23-design' and not lease.get('released_at')
        state['execution'].setdefault('historical_coordinator_snapshots',[]).append(dict(at=ctl.stamp(),fields={k:state['execution'].get(k) for k in ['current_coordinator','coordinator_heartbeat','final_lease_release','coordinator_release_evidence']}))
        state['execution'].update(current_coordinator=lease['owner'],coordinator_heartbeat=ctl.stamp(),actual_lease_pid=lease['pid'],actual_lease_session=int(a.lease_session),final_lease_release=None,coordinator_release_evidence=None)
    before=read(snapshot);mutable={'R23-02','R23-03','R23-04','R23-next'}
    protected={k:v for k,v in before.items() if k not in mutable}
    assert all(ctl.identity(tasks[k])==v for k,v in protected.items())
    if a.action=='start':ctl.begin(state,ROOT,a.task,a.receipt)
    elif a.action=='finish':ctl.finish(state,ROOT,a.task,a.result)
    elif a.action=='freeze':
        folder=(ROOT/a.scope).resolve();lock=(ROOT/a.lock).resolve()
        assert folder.is_relative_to(ROOT/'runs/R23') and lock.is_relative_to(ROOT/'runs/R23') and not lock.exists()
        entries=[];historical_invalid_json=[];commands=[]
        for f in sorted(folder.rglob('*')):
            if not f.is_file() or '__pycache__' in f.parts:continue
            b=f.read_bytes()
            if f.suffix in {'.json','.txt'}:
                try:j=json.loads(b)
                except (ValueError,UnicodeDecodeError):
                    assert not {'receipts','records'}.intersection(f.parts),('Unparseable command receipt',str(f))
                    if f.suffix=='.json':historical_invalid_json.append(f.relative_to(ROOT).as_posix())
                    j=None
                if isinstance(j,dict) and j.get('schema')=='forge-command-record/1':
                    assert j['state']=='finished' and isinstance(j['exit_code'],int) and j.get('end'),str(f)
                    commands.append(dict(path=f.relative_to(ROOT).as_posix(),exit_code=j['exit_code']))
            entries.append(dict(path=f.relative_to(ROOT).as_posix(),size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        assert entries
        ctl.write_json(lock,dict(schema='forge-revision-lock/1',revision=a.scope,frozen_at=ctl.stamp(),files=entries,historical_invalid_json=historical_invalid_json,terminal_commands=commands,claim='Actual terminal artifact byte identity; substantive independent receiving remains separate. Historical invalid non-receipt JSON remains original failure evidence.'))
        registry=read('state/revision-locks.json');assert a.lock not in registry['locks'];registry['locks'].append(a.lock);ctl.write_json(ROOT/'state/revision-locks.json',registry)
        print(json.dumps(dict(frozen_files=len(entries),lock=a.lock)))
    elif a.action=='actor':
        assert a.actor.startswith('/root/r23_') and a.status in ['running','completed','interrupted']
        folder=ROOT/'runs/R23/coordination';folder.mkdir(exist_ok=True);name=a.actor.rsplit('/',1)[-1];serial=1
        while (folder/f'{name}-{a.status}-{serial}.json').exists():serial+=1
        rel=f'runs/R23/coordination/{name}-{a.status}-{serial}.json'
        ctl.write_json(ROOT/rel,dict(actor=a.actor,status=a.status,observed_at=ctl.stamp(),requested_model='gpt-6-luna',actual_model=None,tokens=None,cost=None,scope='Actual collaboration status; local role read/write boundaries are not OS isolation.'))
        pending=[r for r in state['execution']['current_native_pending'] if r['worker']!=a.actor]
        row=dict(worker=a.actor,state=a.status,evidence=rel,actual_model=None)
        if a.status=='running':pending.append(row)
        else:state['execution'].setdefault('completed_native_R23',[]).append(row)
        state['execution'].update(current_native_pending=pending,native_pending_current=pending)
    elif a.action=='recovery':
        task=tasks[a.task];assert task['status']=='failed' and a.task in mutable
        note=read(a.note)
        for key in ['observation','change_or_new_information','expected_check']:assert isinstance(note[key],str) and note[key].strip()
        note['evidence']=[ctl.ref(ROOT,r) for r in note['evidence']]
        task['recovery_note']=note
    elif a.action=='close':
        assert all(tasks[k]['status']=='done' for k in ['R23-01','R23-02','R23-03','R23-04'])
        task=tasks['R23-next'];assert task['status']=='planned' and not task['attempts'] and not state['execution']['current_native_pending']
        note=read(a.note);assert note['bounded_probe_complete'] and note['successor_started'] is False
        task.update(status='cancelled',blocker=None,evidence=[ctl.ref(ROOT,a.note)],next_action=note['next_action'])
        state['execution'].update(R23_status='bounded_probe_complete_no_successor',R23_closure=a.note)
        state.setdefault('events',[]).append(dict(at=ctl.stamp(),command='close_R23_bounded_probe',successor_started=False,evidence=a.note))
    frontier=next((k for k in ['R23-02','R23-03','R23-04','R23-next'] if tasks[k]['status']!='done'),'R23-next')
    state['execution'].update(current_frontier_task=frontier,current_report='runs/R23/REPORT.md',current_task_process_state='Bounded autonomous workflow-design probe; actual pending actors recorded separately.')
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in protected.items())
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_frontier_task=frontier,current_report='runs/R23/REPORT.md',current_native_pending=state['execution']['current_native_pending'],next_action=tasks[frontier]['next_action'],termination=None,unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(action=a.action,frontier=frontier,protected_tasks=len(protected),queue_valid=True)))
