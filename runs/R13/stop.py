"""Retain failed adoption and restore pre-adoption files; never retry or pass R13."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))


def save(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def rollback():
    names=['AGENTS.md','START_HERE.md','CODEX_HANDOFF.md','artifact-manifest.json',
           'docs/EVALUATION_PROTOCOL.md','state/revision-locks.json']
    snapshots=[]
    for name in names:
        raw=(ROOT/name).read_bytes();p=ROOT/'runs/R13/failed-adoption'/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
        snapshots.append(dict(path=name,preserved_as=p.relative_to(ROOT).as_posix(),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    for name in ['AGENTS.md','START_HERE.md','CODEX_HANDOFF.md','artifact-manifest.json']:
        (ROOT/name).write_bytes((ROOT/'runs/R13/entry-before'/name).read_bytes())
    target=ROOT/'docs/EVALUATION_PROTOCOL.md'
    assert target.read_bytes()==(ROOT/'runs/R12/protocol/v2/evaluation-protocol.md').read_bytes()
    assert target.resolve().is_relative_to(ROOT.resolve())
    target.unlink()
    index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
    assert index['locks'][-1]=='runs/R13/protocol-lock.json'
    index['locks'].pop()
    # Restore the exact original index bytes; the failed index snapshot remains above.
    import subprocess
    base=json.loads((ROOT/'runs/R12/baseline/files.json').read_text(encoding='utf-8'))
    original=subprocess.check_output(['git','show',base['source_commit']+':state/revision-locks.json'],cwd=ROOT)
    assert json.loads(original)==index
    (ROOT/'state/revision-locks.json').write_bytes(original)
    save('runs/R13/rollback.json',dict(action='contain_failed_adoption_restore_prior_release_files',snapshots=snapshots,
       failure_record='runs/R13/inspection-command.json',failure='UTF-8 decode failed on Windows default-encoded export manifest',
       task_acceptance='failed',repairs_used=2,repair_limit=2,new_protocol_adopted=False,
       original_attempts_retained=True,rerun_or_repair_after_exhaustion=False,
       limits='Reversible containment and evidence retention, not a corrective attempt to obtain R13 acceptance'))
    print(json.dumps(dict(rolled_back=True,failed_snapshots=len(snapshots),R13_acceptance='failed',no_retry=True)))


def close():
    import continuation as ctl
    with ctl.locked(ROOT):
        state=ctl.load(ROOT);task=ctl.task_map(state)['R13-01'];attempt=task['attempts'][-1]
        assert task['status']=='in_progress' and task['repairs_used']==2
        paths=['runs/R13/adopt-command.json','runs/R13/manifest-command.json','runs/R13/inspection-command.json',
               'runs/R13/rollback.json','runs/R13/rollback-command.json','runs/R13/authoring/repair-ledger.json']
        result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
           criteria=[dict(id='a1',status='fail',evidence=paths),dict(id='a2',status='fail',evidence=paths)],
           effect=dict(target='Adoption of reviewed documentation protocol',hypothesis='The protocol can be routed through the current repository entries',
             baseline='R12 v2 prospective design pass, historical root entries and UTF-8 release manifest',
             conditions='Windows3.12 real adoption and export commands; R13 preparation cumulative corrections2/2',
             observations='Actual protocol/entry writes succeeded, default-encoding export command exited0 but UTF-8 inspection failed. Failed adopted files/index/manifest retained; root routing/manifest restored; no repair or acceptance rerun.',
             limits='R13 adoption failed at exhausted budget; R12 design review still passes. Rollback integrity checks cannot replace adoption acceptance.',
             metrics=dict(repairs_used=2,repair_limit=2,tokens=None,cost=None)),
           next_action='Preserve exhausted failed adoption, publish protocol as reviewed research artifact only, no same-case rerun')
        save('runs/R13/R13-01-result.json',result)
        outcome=ctl.finish(state,ROOT,task['id'],'runs/R13/R13-01-result.json')
        task['blocker']='UTF-8 export inspection failed after actual adoption; cumulative preparation corrections2/2. Adoption rolled back, same case cannot be retried.'
        p=ROOT/'state/phases/R13.json';phase=ctl.phase_view(json.loads(p.read_text()),state)
        phase['tasks'][-1].update(status='blocked',blocker='Required R13-01 adoption acceptance failed at exhausted correction budget',
            evidence=['runs/R13/R13-01-result.json'],next_action='Preserve failed adoption and original blockers; do not fabricate successor')
        ctl.write_json(p,phase)
        state['execution'].update(session_state='R12_design_pass_R13_adoption_failed_checkpoint',native_pending=[],current_native_pending=[],
             current_report='runs/R13/REPORT.md',checkpoint_reason='R12 independent protocol design pass; actual R13 adoption failed UTF-8 export inspection and rolled back; all old failures/budgets retained')
        state['events'].append(dict(at=ctl.stamp(),command='finish_and_stop_exhausted_adoption',result=outcome))
        ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
        project=json.loads((ROOT/'state/project-todo.json').read_text(encoding='utf-8'))
        project['evaluation_protocol_R12'].update(stage='done_design_review_only',review='runs/R12/review/v2/independent/result.json',R12_next='done_actual_R13_first_step_later_failed',case_repairs_used=2)
        project['protocol_adoption_R13']=dict(plan='runs/R13/PLAN.md',R13_01='blocked_failed_utf8_export',R13_next='blocked_dependency',
              report='runs/R13/REPORT.md',repairs_used=2,repair_limit=2,adopted=False,rollback='runs/R13/rollback.json')
        project['updated_at']=ctl.stamp();ctl.write_json(ROOT/'state/project-todo.json',project)
        cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
        cp.update(current_validation='R12 prospective protocol independently reviewed and passed. R13 actual adoption failed UTF-8 export inspection at2/2 and was rolled back. Original R08/R10/R11 gates remain blocked unchanged.',
            current_native_pending=[],R12_current_budget=dict(cumulative_case_used=2,reviewer_internal_used=0,limit=2),
            R13_actual_first_step='runs/R13/adopt-command.json',R13_current_budget=dict(used=2,limit=2,status='blocked_failed_adoption'),
            current_development_report='runs/R13/REPORT.md',unpublished_work=True,
            root_entries_rolled_back=True,reviewed_protocol_research_artifact='runs/R12/protocol/v2/evaluation-protocol.md')
        ctl.write_json(ROOT/'state/checkpoint.json',cp)
    print(json.dumps(dict(result=outcome,R13_next='blocked',root_release_restored=True)))


if __name__=='__main__':
    dict(rollback=rollback,close=close)[sys.argv[1]]()
