"""Development evidence/ledger only; never shipped inside Forge."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def save(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def entry(name):
    raw=(ROOT/name).read_bytes()
    return dict(path=name,size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def prepare():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    state=read('state/continuation.json')
    task_hashes={t['id']:hashlib.sha256(json.dumps(t,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for t in state['tasks']}
    save('runs/R14/baseline.json',dict(source_commit=head,historical_task_hashes=task_hashes,
        previous_revision_index=read('state/revision-locks.json'),
        allowed_existing_changes=['CODEX_HANDOFF.md','START_HERE.md','artifact-manifest.json',
          'state/continuation.json','state/checkpoint.json','state/phase-todo.json',
          'state/project-todo.json','state/coordinator-lease.json','state/revision-locks.json']))
    directory=ROOT/'runs/R14/candidate/C9/forge-agent-flow'
    files=[entry(p.relative_to(ROOT).as_posix()) for p in sorted(directory.rglob('*')) if p.is_file()]
    assert len(files)==8 and all(row['path'].endswith('.md') for row in files)
    for p in directory.rglob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' not in target:
                linked=(p.parent/target.split('#')[0]).resolve()
                assert linked.is_relative_to(directory.resolve()) and linked.exists(),target
    save('runs/R14/candidate/C9-lock.json',dict(schema='forge-revision-lock/1',revision='C9',parent='C8',
         scope_decision='runs/R14/scope-decision.json',files=files,repair_limit=2,repairs_used=2,
         candidate_source_repairs=0,author_orchestration_corrections=2,
         limits='New user domain/quality scope; does not pass or reset any historical case'))
    levels=read('runs/R14/cases/math/levels.json')
    requirements=read('runs/R14/cases/acceptance.json')['math']
    paths=[]
    for level in range(1,9):
        name=f'runs/R14/cases/math/L{level}/request.json'
        output=f'runs/R14/trials/math/L{level}/'
        request=dict(case_id=f'math-level-{level}',level=level,
             user_request=levels['common']+'\n'+'\n'.join(levels['levels'][str(i)] for i in range(1,level+1)),
             original_requirements=requirements,
             inputs=['runs/R14/cases/math/problem.json','runs/R14/candidate/C9/forge-agent-flow/'],
             output_directory=output,
             delivery='workflow.md; executable solver code and reproduction command; results.json with predictions/allocation/objective and validation facts; actual figure; paper.md; verification.md; result.json with paths/state/failed attempts/cumulative corrections used/limit2 and unknown telemetry',
             scope='One working bounded offline slice; complete required outputs and checks before optional sophistication. Do not read other levels, author diagnostics or research conclusions; no network, no extra actors or external actions.',
             repair_limit=2,model_requested='gpt-6-luna',authenticated_model=None,tokens=None,cost=None,
             comparison_limits='Operationalized cumulative prompt, one small case, no award or causal-level ranking')
        save(name,request);paths.append(name)
    paths+=['runs/R14/cases/math/problem.json','runs/R14/cases/math/levels.json',
            'runs/R14/cases/frontend/request.json','runs/R14/cases/acceptance.json','runs/R14/candidate/C9-lock.json']
    save('runs/R14/cases/frozen-lock.json',dict(schema='forge-case-input-lock/1',files=[entry(p) for p in paths],
         candidate_lock='runs/R14/candidate/C9-lock.json',limits='Frozen before independent execution; no outputs or desired answers'))
    save('runs/R14/author/structure.json',dict(ok=True,files=len(files),total_bytes=sum(r['size_bytes'] for r in files),
         scripts=0,tests=0,links_valid=True,quick_validate='runs/R14/author/quick-validate-command.json',
         source_changes='Workflow blueprint, gate/checker responsibility, conditional modeling/frontend/source references',
         limits='Author structure only; no behavior, performance or competition-quality verdict'))
    print(json.dumps(dict(candidate_files=8,frozen_math_levels=8,pure_document_skill=True,old_tasks=len(task_hashes))))


def register():
    import continuation as ctl
    definitions=[
      ('R14-01','升级Forge纯文档本体与冻结契约','root',[],['runs/R14/candidate/','runs/R14/author/'],[
          ('a1','C9实际改动meta-workflow及质量/领域方法，无产品脚本/测试，链接/frontmatter有效'),
          ('a2','保存版本来源、冻结输入和旧任务/预算，结构检查不代替行为')]),
      ('R14-02','八层输入的新上下文建模工作流实际试运行','independent_luna',['R14-01'],['runs/R14/trials/math/'],[
          ('a1','八个全新上下文各按同一原题和C9交付工作流及真实小题产物，失败/预算与未知不隐藏'),
          ('a2','按原m1–m5判定并报告Level观察边界，不凭长度或模型数宣称奖项/层级因果')]),
      ('R14-03','重前端工作流与实际浏览器试运行','independent_luna',['R14-01'],['runs/R14/trials/frontend/'],[
          ('a1','按冻结f1–f5交付方法/实际应用，真实主路径/错误恢复/视口/键盘检查'),
          ('a2','运行、视觉、自测、独立验收、mock与未知边界分开，预算/失败保留')]),
      ('R14-04','独立核验两类产物与smoke验收职责','independent_luna',['R14-02','R14-03'],['runs/R14/acceptance/'],[
          ('a1','新审查者按原要求/原数据检查实际工件，数值重算与浏览器观察，不只接受作者报告'),
          ('a2','强度未降低、必需/可选判定分开，完整需求-证据结论和独立性局限')])]
    with ctl.locked(ROOT):
        state=ctl.load(ROOT)
        for index,(tid,title,owner,deps,writes,criteria) in enumerate(definitions):
            assert tid not in ctl.task_map(state)
            inputs=['runs/R14/PLAN.md','runs/R14/scope-decision.json'] if index==0 else ['runs/R14/cases/acceptance.json','runs/R14/cases/frozen-lock.json','runs/R14/candidate/C9-lock.json']
            state['tasks'].append(dict(id=tid,title=title,queue='capabilities' if index==0 else 'challenges',
                category='new_domain_workflow_quality',complexity=2,priority=30+index,depends_on=deps,owner=owner,
                write_paths=writes,inputs=inputs,acceptance=[dict(id=k,assertion=v) for k,v in criteria],
                status='planned',evidence=[],attempts=[],repairs_used=2 if index==0 else 0,repair_limit=2,
                blocker=None,next_action=title))
        index=read('state/revision-locks.json')
        index['locks'].append('runs/R14/candidate/C9-lock.json');ctl.write_json(ROOT/'state/revision-locks.json',index)
        ctl.begin(state,ROOT,'R14-01','runs/R14/author/prepare-command.json')
        task=ctl.task_map(state)['R14-01'];attempt=task['attempts'][-1]
        result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='a1',status='pass',evidence=['runs/R14/author/structure.json','runs/R14/candidate/C9-lock.json']),
                      dict(id='a2',status='pass',evidence=['runs/R14/scope-decision.json','runs/R14/baseline.json','runs/R14/cases/frozen-lock.json','runs/R14/author/failed-validator-observation.json'])],
            effect=dict(target='New user-specified meta-workflow quality/domain scope',hypothesis='Explicit gates and domain interfaces can guide stronger workflow construction',
                baseline='C8 general method, prior failures/budgets retained',conditions='Actual C9 eight-document authoring/frontmatter/link checks',
                observations='New skill source and original acceptance/input locks created',
                limits='Author structure only; no behavior or improvement verdict',metrics=dict(source_repairs=0,orchestration_corrections=2,tokens=None,cost=None)),
            next_action='Dispatch frozen math level probes and frontend trial')
        save('runs/R14/R14-01-result.json',result)
        ctl.finish(state,ROOT,'R14-01','runs/R14/R14-01-result.json')
        phase_tasks=[]
        for tid,*rest in definitions:
            task=ctl.task_map(state)[tid]
            phase_tasks.append({k:task[k] for k in ['id','title','owner','depends_on','write_paths','status','blocker','next_action']} |
                dict(acceptance=[a['assertion'] for a in task['acceptance']],evidence=[r['path'] for r in task['evidence']]))
        phase_tasks.append(dict(id='R14-next',title='启动下一阶段任务',owner='root',depends_on=[row['id'] for row in phase_tasks],
            write_paths=['state/','runs/'],acceptance=['满足前驱后冻结并真实启动验收者抗退化测试'],status='planned',evidence=[],blocker=None,next_action='R15 checker sensitivity'))
        ctl.write_json(ROOT/'state/phases/R14.json',dict(schema='forge-phase-todo/1',phase_id='R14',goal='Forge本体与建模/重前端真实工作流',tasks=phase_tasks))
        state['events'].append(dict(at=ctl.stamp(),command='register_new_domain_user_scope',result=dict(plan='runs/R14/PLAN.md',old_case_retries=False)))
        state['execution'].update(session_state='R14_C9_domain_trials',current_report='runs/R14/REPORT.md')
        ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
        cp=read('state/checkpoint.json');cp.update(unpublished_work=True,current_candidate='runs/R14/candidate/C9-lock.json',current_development_report='runs/R14/REPORT.md')
        ctl.write_json(ROOT/'state/checkpoint.json',cp)
        project=read('state/project-todo.json');project['domain_workflows_R14']=dict(plan='runs/R14/PLAN.md',candidate='runs/R14/candidate/C9-lock.json',status='independent_trials_pending',new_user_scope=True)
        ctl.write_json(ROOT/'state/project-todo.json',project)
    print(json.dumps(dict(authoring='done',candidate='C9',independent_cases='pending',active_phase='R08')))


def apply_operation():
    import continuation as ctl
    operation=read(sys.argv[2])
    with ctl.locked(ROOT):
        state=ctl.load(ROOT)
        tid=operation['task_id']
        if operation['action']=='start':
            result=ctl.begin(state,ROOT,tid,operation['evidence'])
        elif operation['action']=='finish':
            task=ctl.task_map(state)[tid]
            task['repairs_used']=max(task['repairs_used'],operation.get('repairs_used',task['repairs_used']))
            result=ctl.finish(state,ROOT,tid,operation['result'])
        else:
            raise ValueError('Unknown operation')
        state['events'].append(dict(at=ctl.stamp(),command=operation['action'],result=result))
        if 'native_pending' in operation:
            state['execution']['native_pending']=operation['native_pending']
            state['execution']['current_native_pending']=operation['native_pending']
        ctl.write_json(ROOT/'state/continuation.json',state)
        p=ROOT/'state/phases/R14.json';ctl.write_json(p,ctl.phase_view(read('state/phases/R14.json'),state))
        ctl.synchronize(ROOT,state)
    print(json.dumps(result))


if __name__=='__main__':
    {'prepare':prepare,'register':register,'operation':apply_operation}[sys.argv[1]]()
