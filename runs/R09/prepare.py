"""Freeze a distinct successor from actual host observations, before its start."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def write(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def main():
    names=['scripts/host_preflight.py','scripts/test_host_preflight.py','runs/R09/PLAN.md','runs/R09/README.md']
    rows=[]
    for name in names:
        raw=(ROOT/name).read_bytes();rows.append(dict(path=name,size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    write('runs/R09/source-lock.json',dict(schema='forge-r09-source-lock/1',files=rows,repair_limit=2,repairs_used=0))
    descriptions=[
        ('R09-01','实现并实际运行宿主与冻结字节预检','root',['R08-03'],['scripts/host_preflight.py','scripts/test_host_preflight.py','runs/R09/preflight/'],[
            '只读 JSON CLI 诊断当前宿主的 continuation/安全文件打开/计时条件，字节漂移、非法路径和损坏锁拒绝；不修改文件、预算、租约或真实调用',
            '实际 Windows 与 Linux/WSL 命令和相关测试分别留存；不声称已经移植原生 Windows 控制器或证明 provider/恢复发布'
        ]),
        ('R09-02','独立新checkout核验跨环境预检边界','independent_codex_or_available_luna',['R09-01'],['runs/R09/independent/'],[
            '新上下文从实际 Git 提交创建新 checkout，独立运行预检、continuation 与 lease；冻结版本和要求，不接收作者答案或诊断',
            '保留真实命令、首产物、环境差异、失败与最多两轮预算；未知provider/token/cost保持null'
        ])]
    phase=dict(schema='forge-phase-todo/1',phase_id='R09',goal='从真实Windows/WSL差异建立安全可复核的接续预检',tasks=[])
    s=read('state/continuation.json')
    for task_id,title,owner,deps,writes,criteria in descriptions:
        assert not any(t['id']==task_id for t in s['tasks'])
        task=dict(id=task_id,title=title,queue='capabilities' if task_id=='R09-01' else 'challenges',category='cross_environment_diagnostics',complexity=3,priority=8 if task_id=='R09-01' else 9,depends_on=deps,owner=owner,write_paths=writes,inputs=['runs/R09/PLAN.md','runs/R09/source-lock.json'],acceptance=[dict(id='a'+str(i+1),assertion=c) for i,c in enumerate(criteria)],status='planned',evidence=[],attempts=[],repairs_used=0,repair_limit=2,blocker=None,next_action='Run frozen preflight on the actual host' if task_id=='R09-01' else 'Dispatch fresh checkout verifier after R09-01 acceptance')
        s['tasks'].append(task)
        phase['tasks'].append({k:task[k] for k in ['id','title','owner','write_paths','status','evidence','blocker','next_action']})
        phase['tasks'][-1].update(depends_on=[] if task_id=='R09-01' else ['R09-01'],acceptance=criteria)
    phase['tasks'].append(dict(id='R09-next',title='启动下一阶段任务',owner='root',depends_on=['R09-01','R09-02'],write_paths=['state/','runs/'],acceptance=['从本阶段真实观察选有价值新支线并实际启动'],status='planned',evidence=[],blocker=None,next_action='Select a meaningful successor from observed R09 results'))
    s['events'].append(dict(at=datetime.now(timezone.utc).isoformat(),command='prepare_R09_from_observed_host_failures',result=dict(plan='runs/R09/PLAN.md',new_tasks=['R09-01','R09-02'],old_acceptance_unchanged=True,old_budgets_unchanged=True,early_commands_are_setup_not_phase_transition=True)))
    write('state/continuation.json',s);write('state/phases/R09.json',phase)
    print(json.dumps(dict(prepared_phase='R09',first_task='R09-01',not_started=True)))

if __name__=='__main__':main()
