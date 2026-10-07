"""Record parent-observed agent lifecycle; this is not provider telemetry."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
level=int(sys.argv[1]); role=sys.argv[2]; status=sys.argv[3]
actor=f'/root/r19_l{level}_{role}'
path=f'runs/R19/levels/L{level}/{role}-{status}-observation.json'
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    serial=1
    while (ROOT/path).exists():
        serial+=1
        path=f'runs/R19/levels/L{level}/{role}-{status}-observation-{serial}.json'
    ctl.write_json(ROOT/path,dict(actor=actor,state=status,observed_at=ctl.stamp(),
        provenance='Parent observed collaboration tool return/notification; not authenticated model or token telemetry.',
        actual_model=None,tokens=None,cost=None))
    rows=state['execution'].get('current_native_pending',[])
    rows=[r for r in rows if r['worker']!=actor]
    row=dict(worker=actor,state=status,evidence=path,actual_model=None)
    if status in {'created','running_observed'}:rows.append(row)
    else:state['execution'].setdefault('completed_native_R19',[]).append(row)
    if role in {'executor','reviewer'}:
        state['execution']['current_paper_level']=level
    state['execution'].setdefault('current_paper_level',1)
    paper_level=state['execution']['current_paper_level']
    state['execution'].update(current_native_pending=rows,native_pending_current=rows,
        current_task_process_state=f'R19 L{level}: {role} {status}; actual pending count {len(rows)}.',
        current_report='runs/R19/PLAN.md',R19_current_level=paper_level,latest_observed_actor_level=level)
    state['execution'].setdefault('pre_R19_publication',{
        key:state['execution'].get(key) for key in ['current_publication','current_source_commit','current_source_ci','current_source_ci_observed']})
    state['execution']['current_frontier_task']=f'R19-L{paper_level}'
    if state['execution'].get('R19_publication_status')=='source_pushed_observed':
        state['execution'].update(R19_unpublished_followups=True,
            source_ci_scope='Preserve actual published source observation; later working changes and paper quality are separate.')
    else:
        state['execution'].update(R19_publication_status='not_yet_published',
            current_publication=None,current_source_commit=None,current_source_ci=None,current_source_ci_observed=None,
            source_ci_scope='Old C10 CI stays in pre_R19_publication; no C11 or paper acceptance follows from it.')
    state['events'].append(dict(at=ctl.stamp(),command='parent_actor_observation',actor=actor,status=status))
    ctl.write_json(ROOT/'state/continuation.json',state)
    ctl.synchronize(ROOT,state)
    cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_native_pending=rows,current_report='runs/R19/PLAN.md',R19_status=f'L{level}_{role}_{status}',
        next_action=f'Continue L{paper_level} paper execution/review in L1–L4 order; other levels may independently prepare designs under PREPARATION_ADDENDUM. Latest L{level} {role} {status}.',unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(actor=actor,status=status,pending=len(rows))))
