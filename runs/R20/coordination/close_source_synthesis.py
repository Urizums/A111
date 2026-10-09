"""Close R20 source synthesis only after exact frozen first forward reception."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    assert not state['execution']['current_native_pending']
    old=read('runs/R20/before/task-identities.json')
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    receipt='runs/R20/coordination/c13-first-reception-check-recovery-command.json'
    assert read(receipt)['state']=='finished' and read(receipt)['exit_code']==0
    final='runs/R20/final-lock.json'
    assert (ROOT/final).exists()
    rel='runs/R20/R20-05-result.json'
    assert not (ROOT/rel).exists()
    task=ctl.task_map(state)['R20-05'];attempt=task['attempts'][-1]
    evidence=[final,'runs/R20/forward-case/production-lock.json','runs/R20/forward-case/review/initial-lock.json',
        'runs/R20/forward-case/review/preparation-path-error-lock.json','runs/R20/forward-case/review/preparation-lock.json',receipt]
    ctl.write_json(ROOT/rel,dict(task_id='R20-05',attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
        criteria=[dict(id='t1',status='pass',evidence=evidence)],effect=dict(target='Source-bound synthesis and C13 affected forward reception',
            hypothesis='A conditional source-time clarification supports an explicit receiving interface when prior evaluation becomes calibration input.',
            baseline='C12 accepted full original-data paper after retained author corrections; no controlled C12/C13 matched experiment.',
            conditions='C13 changes only modeling paragraph; 9 Markdown files, 8 byte-identical. Fresh original case, maker and independent receiver; same actor after coordinator path recovery.',
            observations=dict(full_paper='R20-04 independent d1-d5 first PASS plus informed source addendum',
                C13='f1-f3 first independent forward PASS, actual raw rerun, raw reconstruction and lawful/invalid consumers',
                packaging='22438 bytes, nine Markdown, archive readback exact, zero scripts/tests/runners',
                failures='Original author/scientific/controller/CI/reviewer/path recovery observations retained',
                telemetry=dict(model=None,tokens=None,cost=None)),
            limits='Affected bounded interface only, not full four-level C13 papers, causal failure-rate reduction, prize or formal contest compliance. Full paper used the C12-derived workflow; C13 does not retroactively own it.',
            metrics=dict(markdown_files=9,changed_files=1,tokens=None,cost=None)),
        next_action='R20-next: first source-bound diagnostic of known R20 future reliability, then untouched new measurement protocol.'))
    ctl.finish(state,ROOT,'R20-05',rel)
    assert not ctl.validate(state,ROOT)
    state['execution'].update(current_frontier_task='R20-next',current_report='runs/R20/REPORT.md',
        current_candidate='runs/R20/final/candidate/C13-lock.json',candidate_status='C13_targeted_forward_reception_pass_scoped',
        R20_status='source_synthesis_and_forward_reception_done_actual_successor_pending')
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_frontier_task='R20-next',current_report='runs/R20/REPORT.md',
        current_candidate='runs/R20/final/candidate/C13-lock.json',current_native_pending=[],unpublished_work=True,termination=None,
        next_action='R20-next: create frozen plan and execute first known-truth descriptive diagnostic; preserve old judgments and limits.')
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(R20_05='done',frontier='R20-next',old_tasks_unchanged=60)))
