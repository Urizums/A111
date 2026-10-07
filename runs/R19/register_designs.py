"""Add prospective independent preparation tasks; do not alter frozen trial rows."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    assert not any(t['id']=='R19-D2' for t in state['tasks'])
    before={t['id']:ctl.identity(t) for t in state['tasks']}
    for level in (2,3,4):
        state['tasks'].append(dict(id=f'R19-D{level}',title=f'独立准备并冻结Level{level}工作流设计',queue='challenges',
            category='prospective_independent_design_preparation',complexity=2,priority=20,
            depends_on=['R19-01'],owner='root',write_paths=[f'runs/R19/levels/L{level}/design/'],
            inputs=[f'runs/R19/inputs/L{level}.md','runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/PREPARATION_ADDENDUM.md'],
            acceptance=[dict(id='d1',assertion='Actual fresh builder delivered original-source-mapped workflow/handoff, frozen bytes and truthful design-only status; no runtime or paper acceptance implied.')],
            status='planned',evidence=[],attempts=[],repairs_used=0,repair_limit=None,blocker=None,next_action='Construct design from own exact level input and raw source only.',
            execution_policy=dict(mode='progress_guard',source=ctl.ref(ROOT,'runs/R19/PREPARATION_ADDENDUM.md'),
                stop_conditions=['actual host/resource boundary','user stop','completion','persistent unchanged failed path'],progress_state='ready',deadline_utc=None)))
    for level in (2,3):ctl.begin(state,ROOT,f'R19-D{level}',f'runs/R19/levels/L{level}/design-input-inspection-command.json')
    state['execution'].update(R19_preparation_schedule='runs/R19/PREPARATION_ADDENDUM.md',current_paper_level=1,current_frontier_task='R19-L1')
    assert all(ctl.identity(ctl.task_map(state)[ident])==digest for ident,digest in before.items())
    ctl.write_json(ROOT/'state/continuation.json',state)
    ctl.synchronize(ROOT,state)
    cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(next_action='Continue L1 paper/examination; L2/L3 independent design preparation actually dispatched, L4 design next available slot. Paper executions remain L1→L4.',
        R19_preparation_schedule='runs/R19/PREPARATION_ADDENDUM.md',unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
    errors=ctl.validate(state,ROOT);assert not errors,errors
print(json.dumps(dict(existing_tasks_unchanged=len(before),new_preparation_tasks=3,L2_L3_design='in_progress',paper_level=1)))
