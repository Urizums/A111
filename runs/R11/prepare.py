from pathlib import Path
import json
import sys

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'scripts'))
import continuation as ctl

with ctl.locked(root):
    state=ctl.load(root)
    rows=[dict(id='R11-01',title='交付并实际解包纯方法 C8',queue='capabilities',category='standalone_meta_workflow_package',complexity=1,priority=12,depends_on=['R09-02','R10-01'],owner='root',write_paths=['runs/R11/package/'],inputs=['runs/R11/PLAN.md','runs/R10/candidate/C8-lock.json'],acceptance=[dict(id='a1',assertion='实际输出并解包冻结C8五份文档，核对字节和全部引用，包内无执行器/测试，无个人安装或旧源码修改'),dict(id='a2',assertion='真实命令和边界记录，不以包装验收代替行为、性能或完整产品验收')],next_action='Create standalone document-only package from frozen C8'),dict(id='R11-02',title='独立方法包的 checkpoint 接续验证',queue='challenges',category='portable_meta_workflow_continuation',complexity=2,priority=13,depends_on=['R11-01','R10-02'],owner='independent_codex_or_available_luna',write_paths=['runs/R11/continuation/'],inputs=['runs/R11/PLAN.md','runs/R10/candidate/C8-lock.json'],acceptance=[dict(id='a1',assertion='在执行前冻结基于实际R10输出的checkpoint和新继续要求，独立新上下文从独立技能包恢复并产出可核验结果'),dict(id='a2',assertion='保留原版本、已耗预算、未决决定与有效输出的复用证据，无隐藏仓库依赖；失败与修正不清零')],next_action='Freeze actual R10 artifacts and successor request before independent execution')]
    for task in rows:
        assert task['id'] not in ctl.task_map(state)
        task.update(status='planned',evidence=[],attempts=[],repairs_used=0,repair_limit=2,blocker=None)
        state['tasks'].append(task)
    state['events'].append(dict(at=ctl.stamp(),command='prepare_portable_method_branch',result=dict(plan='runs/R11/PLAN.md',basis=['R09 actual Windows/Linux divergence','C8 document-only structure checked','R10 behavior still pending'],does_not_bypass_R10_acceptance=True,old_failures_or_budgets_changed=False)))
    ctl.write_json(root/'state/continuation.json',state)
    phase=dict(schema='forge-phase-todo/1',phase_id='R11',goal='独立方法包与实际checkpoint接续',tasks=[{k:task[k] for k in ['id','title','owner','depends_on','write_paths','status','evidence','blocker','next_action']}|dict(acceptance=[a['assertion'] for a in task['acceptance']]) for task in rows])
    # Phase dependencies are local; queue retains the cross-branch dependency.
    phase['tasks'][0]['depends_on']=[]
    phase['tasks'][1]['depends_on']=['R11-01']
    phase['tasks'].append(dict(id='R11-next',title='启动下一阶段任务',owner='root',depends_on=['R11-01','R11-02'],write_paths=['state/','runs/'],acceptance=['依据接续结果形成后继并实际启动'],status='planned',evidence=[],blocker=None,next_action='Inspect continuation observations'))
    ctl.write_json(root/'state/phases/R11.json',phase)
    ctl.synchronize(root,state)
print(json.dumps(dict(registered=['R11-01','R11-02'],packaging_is_independent=True)))
