"""Close a completed diagnostic, preserving the original scientific verdicts."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser();p.add_argument('level',type=int,choices=range(1,5))
p.add_argument('--execution',default='execution');p.add_argument('--review',default='review/initial')
p.add_argument('--paper-source',default='paper/paper.md')
p.add_argument('--paper-pdf',default='paper/paper.pdf')
p.add_argument('--closure-reason',required=True,help='Actual completed correction or evidenced remaining limitation; not a quality override.')
a=p.parse_args();base=f'runs/R19/levels/L{a.level}'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def check(path):
    lock=read(path)
    for entry in lock['files']:
        data=(ROOT/entry['path']).read_bytes()
        assert len(data)==entry['size_bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],entry['path']
    return lock
for scope in ['design',a.execution,'review/initial',a.review]:
    check(f'{base}/{scope}-lock.json')
report_path=f'{base}/{a.review}/result.json'
initial=read(f'{base}/review/initial/result.json');latest=read(report_path)
verdicts=latest['a1_a6']
assert {v['id'] for v in verdicts}=={f'a{k}' for k in range(1,7)}
assert all(v['status'] in {'pass','fail','blocked','unverified'} and v.get('evidence') for v in verdicts)
execution_root=(ROOT/base/a.execution).resolve()
execution_paths={entry['path'] for entry in read(f'{base}/{a.execution}-lock.json')['files']}
for relative in [a.paper_source,a.paper_pdf]:
    path=(execution_root/relative).resolve()
    assert path.is_relative_to(execution_root),'Paper must be inside the frozen execution scope.'
    assert path.is_file() and path.relative_to(ROOT).as_posix() in execution_paths
with ctl.locked(ROOT):
    state=ctl.load(ROOT);task=ctl.task_map(state)[f'R19-L{a.level}']
    assert task['status']=='in_progress'
    old=read('runs/R19/before/task-identities.json')
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    assert not state['execution']['current_native_pending'],'Reconcile all current actors before closing.'
    path=f'{base}/diagnostic-result.json'
    evidence=[f'{base}/design-lock.json',f'{base}/{a.execution}-lock.json',
              f'{base}/review/initial-lock.json',f'{base}/{a.review}-lock.json',report_path]
    outcome=dict(task_id=task['id'],attempt_id=task['attempts'][-1]['id'],
        requirements_hash=task['attempts'][-1]['requirements_hash'],
        criteria=[dict(id=c['id'],status='pass',evidence=evidence) for c in task['acceptance']],
        initial_scientific_verdict=initial['a1_a6'],latest_scientific_verdict=verdicts,
        initial_quality=initial['quality_diagnosis'],latest_quality=latest['quality_diagnosis'],
        closure_reason=a.closure_reason,latest_mandatory_pass=all(v['status']=='pass' for v in verdicts),
        paper_artifacts=[f'{base}/{a.execution}/{a.paper_source}',f'{base}/{a.execution}/{a.paper_pdf}'],
        claim='Completed transfer/paper/independent diagnostic. First review failures remain; informed repairs do not retroactively pass the first trial.',
        effect=dict(target=f'Level{a.level} actual workflow transfer to paper',
            hypothesis='Frozen meta-workflow supports sparse-input end-to-end execution; single case observations only.',
            baseline='Same C11 and official raw question; original own level prompt; earlier failures preserved.',
            conditions='Fresh builder/executor/reviewer; exact source; independent first review and separately labelled repair if present.',
            observations=dict(initial_verdict=initial['status'],latest_verdict=latest['status'],review_scope=a.review),
            limits='No prize estimate, causal level ranking, repeat-trial or October big-data performance inference. Quality limits remain in reviewer reports.',
            metrics=dict(papers=1,initial_failures=sum(v['status']!='pass' for v in initial['a1_a6']),tokens=None,cost=None)),
        next_action=f'Start sequential R19-L{a.level+1} from its own frozen design.' if a.level<4 else 'Perform R19-05 synthesis from actual four-level observations.')
    assert not (ROOT/path).exists()
    ctl.write_json(ROOT/path,outcome);ctl.finish(state,ROOT,task['id'],path)
    state['execution'].setdefault('R19_completed_diagnostics',[]).append(dict(level=a.level,result=path,
        initial_mandatory_pass=all(v['status']=='pass' for v in initial['a1_a6']),informed_repair=a.review!='review/initial'))
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    assert not ctl.validate(state,ROOT),ctl.validate(state,ROOT)
print(json.dumps(dict(level=a.level,diagnostic_status=task['status'],initial_verdict=initial['status'],latest_verdict=latest['status'],old_tasks_unchanged=len(old))))
