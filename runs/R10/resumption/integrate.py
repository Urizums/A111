"""Integrate retained terminal evidence without changing candidate or frozen cases."""
from pathlib import Path
import hashlib
import json
import sys

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'scripts'))
import continuation as ctl

def new(name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

original='runs/R10/validation/independent/evidence/first-command.json'
raw=(root/original).read_bytes();record=json.loads(raw)
assert record['exit_code']==0 and record['argv'] and record['begin'] and record['end']
terminal={k:record[k] for k in ['argv','cwd','begin','end','exit_code']}
terminal.update(schema='forge-terminal-transcription/1',state='finished',source=dict(path=original,sha256=hashlib.sha256(raw).hexdigest()),limits='Transcription of an actual finished command; not a new command execution. Original missing-state record unchanged.')
new('runs/R10/resumption/first-command-terminal.json',terminal)

with ctl.locked(root):
    state=ctl.load(root)
    assert not ctl.validate(state,root)
    r09=ctl.task_map(state)['R09-02'];attempt=r09['attempts'][-1]
    report=json.loads((root/'runs/R09/independent/report.json').read_text(encoding='utf-8'))
    assert report['actual_commit']=='11e5ce90864e73a3f600df066cfbb469c6428a18'
    for command in report['commands']:
        item=json.loads((root/'runs/R09/independent'/command['record']).read_text(encoding='utf-8'))
        assert item['state']=='finished' and isinstance(item['exit_code'],int)
    new('runs/R09/R09-02-result.json',dict(task_id='R09-02',attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],criteria=[dict(id='a1',status='pass',evidence=['runs/R09/independent/report.json','runs/R09/independent/commit.json','runs/R09/independent/preflight-windows.json','runs/R09/independent/preflight-wsl.json','runs/R09/independent/continuation-wsl-validate.json','runs/R09/independent/lease-wsl-hold.json','runs/R09/independent/lease-wsl-competing-probe.json','runs/R09/independent/lease-wsl-post-release-probe.json']),dict(id='a2',status='pass',evidence=['runs/R09/independent/report.json','runs/R09/independent/first-command.json','runs/R09/independent/creation-return.json'])],effect=dict(target='Independent checkout/environment verification',hypothesis='Preflight reflects actual APIs and frozen bytes; lease excludes competing coordinator in same checkout',baseline='Published Git commit11e5ce9, frozen R09 implementation',conditions='Fresh local clone, Windows3.12.8 and Ubuntu24.04 Python3.12.3',observations='22 finished command records; exact commit; Windows rejects unsupported runtime; WSL validates31 tasks and exercises acquired/competing-busy/released/free',limits='No Windows implementation port, provider, distributed isolation or crash durability proof. Requested model gpt-6-luna/max; report self-label GPT-6 is not authenticated exact model telemetry; actual provider model unknown.',metrics=dict(command_records=22,repairs_used=0,repair_limit=2,provider=None,tokens=None,cost=None)),next_action='Integrate independent result, retain R08 block, proceed user-requested meta-workflow branch'))
    result=ctl.finish(state,root,'R09-02','runs/R09/R09-02-result.json')
    state['events'].append(dict(at=ctl.stamp(),command='finish',result=result))
    r10=ctl.begin(state,root,'R10-02','runs/R10/resumption/first-command-terminal.json')
    state['events'].append(dict(at=ctl.stamp(),command='start',result=r10))
    state['execution'].update(current_coordinator='root-codex-c8-resume',session_state='resuming_same_R10_02_after_quota_interruption',native_pending=['/root/c8_workflow_trial'],current_native_pending=[dict(worker='/root/c8_workflow_trial',task='R10-02',state='same_actor_followup_sent_status_unconfirmed',evidence='runs/R10/resumption/decision.json')],coordinator_heartbeat=ctl.stamp(),checkpoint_reason='R09 independent terminal evidence integrated; C8 same-task resumption requested; no replacement or budget reset')
    state['execution'].setdefault('completed_native_R09',[]).append(dict(worker='/root/r09_independent',state='terminal_report_on_disk',evidence='runs/R09/independent/report.json'))
    assert not ctl.validate(state,root)
    ctl.write_json(root/'state/continuation.json',state)
    for phase_id in ['R09','R10']:
        path=root/f'state/phases/{phase_id}.json'
        ctl.write_json(path,ctl.phase_view(json.loads(path.read_text(encoding='utf-8')),state))
    ctl.synchronize(root,state)
    checkpoint=json.loads((root/'state/checkpoint.json').read_text(encoding='utf-8'))
    checkpoint.update(current_validation='R09-02 independently checked and integrated done; C8 authoring passed; R10-02 original actor interrupted by quota, same-task resumption unconfirmed',current_native_pending=state['execution']['current_native_pending'],R10_current_budget=dict(coordinator_used=2,coordinator_limit=2,evaluator_recording_correction_used=1,evaluator_limit=2,candidate_source_repairs=0,evidence='runs/R10/resumption/decision.json'))
    ctl.write_json(root/'state/checkpoint.json',checkpoint)
print(json.dumps(dict(R09_02='done',R10_02='in_progress',actor='/root/c8_workflow_trial',original_record_unchanged=True)))
