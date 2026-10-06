"""Adopt an independently reviewed documentation protocol; not skill runtime code."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))


def save(name,value):
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')


def register():
    import continuation as ctl
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location('r12_manager',ROOT/'runs/R12/manage.py')
    module=module_from_spec(spec);spec.loader.exec_module(module)
    with ctl.locked(ROOT):
        state=ctl.load(ROOT)
        assert ctl.task_map(state)['R12-02']['status']=='done'
        assert 'R13-01' not in ctl.task_map(state)
        task=dict(id='R13-01',title='接入已审查规程并核对交接与历史保护',queue='capabilities',
             category='reviewed_protocol_repository_adoption',complexity=1,priority=22,
             depends_on=['R12-02'],owner='root',write_paths=['docs/EVALUATION_PROTOCOL.md','AGENTS.md','START_HERE.md','CODEX_HANDOFF.md','artifact-manifest.json'],
             inputs=['runs/R13/PLAN.md','runs/R12/protocol/v2/evaluation-protocol.md','runs/R12/R12-02-result-v2.json'],
             acceptance=[dict(id='a1',assertion='实际接入冻结规程和有效入口，源/目标字节一致；仅更新明确入口、台账、导出清单并保留旧版本'),
                         dict(id='a2',assertion='真实核验交接图与全历史保护，明确设计审查并非C8业务通过；停止无价值的阶段生成')],
             status='planned',evidence=[],attempts=[],repairs_used=2,repair_limit=2,blocker=None,
             next_action='Write byte-identical reviewed protocol and update repository entry links')
        state['tasks'].append(task)
        ctl.write_json(ROOT/'state/phases/R13.json',module.phase([task],'R13','评估规程研发入口接入'))
        state['events'].append(dict(at=ctl.stamp(),command='register_protocol_adoption',result=dict(task='R13-01',plan='runs/R13/PLAN.md')))
        ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    print(json.dumps(dict(registered='R13-01')))


def adopt():
    protocol=(ROOT/'runs/R12/protocol/v2/evaluation-protocol.md').read_bytes()
    target=ROOT/'docs/EVALUATION_PROTOCOL.md'
    assert not target.exists()
    with target.open('xb') as handle:handle.write(protocol)
    for name in ['AGENTS.md','START_HERE.md','CODEX_HANDOFF.md']:
        old=(ROOT/name).read_bytes()
        path=ROOT/'runs/R13/entry-before'/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as handle:handle.write(old)
    agents=ROOT/'AGENTS.md'
    with agents.open('a',encoding='utf-8',newline='\n') as handle:
        handle.write('\n本轮前瞻研发评估采用[交付与证据评估规程](docs/EVALUATION_PROTOCOL.md)：优先复用适用回执，分别记录命令终态与业务完成，保留原件和累计修正。它不替换既有案例契约、不追溯减预算、不作为C8运行依赖。规程独立设计审查见 runs/R12/review/independent/。\n')
    block='''本轮已完成R12轻量评估规程的独立设计审查，并在R13实际接入[研发评估规程](docs/EVALUATION_PROTOCOL.md)。
规程用于本仓库研发，明确业务核验与记录责任；不加入C8包，也不引入新的运行依赖。
这是设计审查和文档接入，尚无行为效果或效率的实测通过结论。
R08/R10/R11原阻塞及预算保持不变；不创建新样本/C9来替代耗尽的原案例。
最新支线报告 runs/R12/REPORT.md 与 runs/R13/REPORT.md；历史交接版本保留。

'''
    for name in ['START_HERE.md','CODEX_HANDOFF.md']:
        path=ROOT/name;text=path.read_text(encoding='utf-8')
        first,rest=text.split('\n',1)
        path.write_text(first+'\n\n'+block+rest.lstrip('\n'),encoding='utf-8',newline='\n')
    save('runs/R13/adoption.json',dict(target='docs/EVALUATION_PROTOCOL.md',source='runs/R12/protocol/v2/evaluation-protocol.md',
         byte_identical=target.read_bytes()==protocol,sha256=hashlib.sha256(protocol).hexdigest(),
         actual_entry_files=['AGENTS.md','START_HERE.md','CODEX_HANDOFF.md'],candidate_changed=False,
         limits='Actual repository documentation writes, not workflow behavior execution'))
    save('runs/R13/protocol-lock.json',dict(schema='forge-revision-lock/1',revision='R13-research-protocol',
         files=[dict(path='docs/EVALUATION_PROTOCOL.md',size_bytes=len(protocol),sha256=hashlib.sha256(protocol).hexdigest())]))
    old=(ROOT/'artifact-manifest.json').read_bytes()
    path=ROOT/'runs/R13/entry-before/artifact-manifest.json'
    with path.open('xb') as handle:handle.write(old)
    print(json.dumps(dict(adopted='docs/EVALUATION_PROTOCOL.md',byte_identical=True,entry_files_changed=3)))


def start():
    import continuation as ctl
    with ctl.locked(ROOT):
        state=ctl.load(ROOT);attempt=ctl.begin(state,ROOT,'R13-01','runs/R13/adopt-command.json')
        index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
        index['locks'].append('runs/R13/protocol-lock.json');ctl.write_json(ROOT/'state/revision-locks.json',index)
        path=ROOT/'state/phases/R13.json';ctl.write_json(path,ctl.phase_view(json.loads(path.read_text()),state))
        path=ROOT/'state/phases/R12.json';phase=ctl.phase_view(json.loads(path.read_text()),state)
        assert all(t['status']=='done' for t in phase['tasks'][:-1])
        phase['tasks'][-1].update(status='done',blocker=None,evidence=['runs/R13/adopt-command.json','runs/R13/PLAN.md'],
              next_action='Complete already-started repository adoption',
              transition=dict(next_phase_id='R13',todo_path='state/phases/R13.json',first_task_id='R13-01',start_evidence=['runs/R13/adopt-command.json']))
        ctl.write_json(path,phase)
        state['events'].append(dict(at=ctl.stamp(),command='start_protocol_adoption_and_R12_successor',result=attempt))
        state['execution'].update(session_state='R13_repository_protocol_adoption',current_report='runs/R13/REPORT.md')
        ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    print(json.dumps(dict(started='R13-01',R12_next='done',active_phase='R08')))


def inspect():
    base=json.loads((ROOT/'runs/R12/baseline/files.json').read_text(encoding='utf-8'))
    allowed_new={'state/revision-locks.json'}
    changed=[]
    for row in base['files']:
        if row['path'] in allowed_new:continue
        raw=(ROOT/row['path']).read_bytes()
        if len(raw)!=row['size_bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:changed.append(row['path'])
    old=json.loads((ROOT/'runs/R12/baseline/state/continuation.json').read_text(encoding='utf-8'))
    current=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
    tasks={t['id']:t for t in current['tasks']}
    task_changes=[t['id'] for t in old['tasks'] if tasks.get(t['id'])!=t]
    old_index=json.loads(subprocess.check_output(['git','show',base['source_commit']+':state/revision-locks.json'],cwd=ROOT))
    index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
    assert index['locks']==old_index['locks']+['runs/R13/protocol-lock.json']
    old_manifest=json.loads((ROOT/'runs/R13/entry-before/artifact-manifest.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'artifact-manifest.json').read_text(encoding='utf-8'))
    before={r['path']:r for r in old_manifest['entries']};after={r['path']:r for r in manifest['entries']}
    differences=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
    assert differences==['AGENTS.md','CODEX_HANDOFF.md','START_HERE.md','docs/EVALUATION_PROTOCOL.md']
    import re
    links=[]
    for name in ['AGENTS.md','START_HERE.md','CODEX_HANDOFF.md','docs/EVALUATION_PROTOCOL.md']:
        file=ROOT/name
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):
                path=(file.parent/link.split('#')[0]).resolve()
                links.append(dict(source=name,target=link,ok=path.is_relative_to(ROOT) and path.exists()))
    result=dict(ok=not changed and not task_changes and all(r['ok'] for r in links),
       protected_files=len(base['files'])-1,changed_files=changed,historical_tasks=len(old['tasks']),changed_tasks=task_changes,
       preserved_revision_index=True,manifest_changes=differences,links=links,
       frozen_protocol_byte_identical=(ROOT/'docs/EVALUATION_PROTOCOL.md').read_bytes()==(ROOT/'runs/R12/protocol/v2/evaluation-protocol.md').read_bytes(),
       limits='Integrity, entry routing and preservation; no C8 behavior or performance acceptance')
    save('runs/R13/inspection.json',result);assert result['ok'] and result['frozen_protocol_byte_identical']
    print(json.dumps(result,ensure_ascii=False))


def finish():
    import continuation as ctl
    observed=json.loads((ROOT/'runs/R13/inspection.json').read_text(encoding='utf-8'));assert observed['ok']
    with ctl.locked(ROOT):
        state=ctl.load(ROOT);task=ctl.task_map(state)['R13-01'];attempt=task['attempts'][-1]
        paths=['runs/R13/adoption.json','runs/R13/inspection.json','runs/R13/adopt-command.json']
        result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
           criteria=[dict(id='a1',status='pass',evidence=paths),dict(id='a2',status='pass',evidence=paths+['runs/R13/PLAN.md'])],
           effect=dict(target='Repository routing to reviewed protocol',hypothesis='The adopted design is reachable without changing the skill product',
             baseline='R12 frozen protocol and independent design review',conditions='Actual writes to repository docs/entry, source and task preservation inspection',
             observations='Byte-identical protocol adopted, links and original files/tasks checked, manifest previous version preserved',
             limits='Documentation integration; effect in future business use remains unmeasured',metrics=dict(repairs_used=task['repairs_used'],tokens=None,cost=None)),
           next_action='Bounded protocol integration complete; preserve blocked original business gates and report current limits')
        save('runs/R13/R13-01-result.json',result);outcome=ctl.finish(state,ROOT,task['id'],'runs/R13/R13-01-result.json')
        p=ROOT/'state/phases/R13.json';phase=ctl.phase_view(json.loads(p.read_text()),state)
        phase['tasks'][-1].update(status='cancelled',blocker=None,evidence=['runs/R13/R13-01-result.json','runs/R13/PLAN.md'],
           next_action='No useful unblocked successor identified; do not generate another sample to replace exhausted historical acceptance',
           stopping_reason='Bounded documentation adoption complete; original R08/R10/R11 dependency gates remain blocked')
        ctl.write_json(p,phase)
        state['events'].append(dict(at=ctl.stamp(),command='finish',result=outcome))
        state['execution'].update(session_state='R12_R13_documentation_complete_original_gates_blocked',native_pending=[],current_native_pending=[],
              current_report='runs/R13/REPORT.md',checkpoint_reason='Independent protocol design/adoption complete; original behavioral gates and all consumed budgets retained')
        ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
        project=json.loads((ROOT/'state/project-todo.json').read_text(encoding='utf-8'))
        project['evaluation_protocol_R12'].update(stage='done_design_review_only',review='runs/R12/review/v2/independent/result.json',R12_next='done_actual_R13_first_step')
        project['protocol_adoption_R13']=dict(plan='runs/R13/PLAN.md',R13_01='done',R13_next='cancelled_bounded_scope_complete',report='runs/R13/REPORT.md',skill_behavior_passed=False)
        project['updated_at']=ctl.stamp();ctl.write_json(ROOT/'state/project-todo.json',project)
        cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
        cp.update(current_validation='R12 protocol independently reviewed as design; R13 actual repository adoption complete. C8 behavior and original R08/R10/R11 gates remain blocked unchanged.',
             current_native_pending=[],R12_current_budget=dict(cumulative_case_used=2,reviewer_internal_used=0,limit=2,source='runs/R12/review/v2/independent/result.json'),
             R13_actual_first_step='runs/R13/adopt-command.json',R13_current_budget=dict(author_used=task['repairs_used'],limit=2),
             unpublished_work=True,current_development_report='runs/R13/REPORT.md')
        ctl.write_json(ROOT/'state/checkpoint.json',cp)
    print(json.dumps(dict(result=outcome,R13_next='cancelled',active_phase='R08')))


if __name__=='__main__':
    dict(register=register,adopt=adopt,start=start,inspect=inspect,finish=finish)[sys.argv[1]]()
