"""Bind actual receiving outcomes to source clauses; no new candidate inferred."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'runs/R23';OUT=BASE/'final'
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
state=read('state/continuation.json');tasks={t['id']:t for t in state['tasks']}
assert tasks['R23-03']['status']=='done' and tasks['R23-03']['repairs_used']==1
assert [a['status'] for a in tasks['R23-03']['attempts']]==['failed','done']
verdict=read('runs/R23/review/clean-initial/verdict.json');assert all(c['status']=='pass' for c in verdict['criteria'].values())
locks=['design-lock.json','reception-preparation-lock.json','execution-lock.json','initial-reception-lock.json','design-correction-v2-lock.json','clean-preparation-lock.json','receiving-packet-lock.json','clean-reception-lock.json']
scopes=[]
for rel in locks:
    lock=read('runs/R23/'+rel);records=[];invalid=[]
    for entry in lock['files']:
        p=ROOT/entry['path'];b=p.read_bytes();assert len(b)==entry['size_bytes'] and hashlib.sha256(b).hexdigest()==entry['sha256'],entry['path']
        if p.suffix not in {'.json','.txt'}:continue
        try:j=json.loads(b)
        except (ValueError,UnicodeDecodeError):
            assert not {'records','receipts'}.intersection(p.parts)
            if p.suffix=='.json':invalid.append(entry['path'])
            continue
        if isinstance(j,dict) and j.get('schema')=='forge-command-record/1':
            assert j['state']=='finished' and isinstance(j['exit_code'],int) and j.get('end')
            records.append(dict(path=entry['path'],exit_code=j['exit_code']))
    scopes.append(dict(lock='runs/R23/'+rel,files=len(lock['files']),terminal_commands=len(records),nonzero_commands=sum(r['exit_code']!=0 for r in records),historical_invalid_json=invalid))
basis=read('runs/R23/source-basis-v2.json');assert basis['C13_files']==9
for c in basis['clauses']:
    p=ROOT/c['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==c['sha256']
    assert '\n'.join(p.read_text(encoding='utf-8').splitlines()[c['start_line']-1:c['end_line']])==c['excerpt']
source_lock=read('runs/R20/final/candidate/C13-lock.json');assert len(source_lock['files'])==9
for entry in source_lock['files']:
    b=(ROOT/entry['path']).read_bytes();assert entry['path'].endswith('.md') and len(b)==entry['size_bytes'] and hashlib.sha256(b).hexdigest()==entry['sha256']
OUT.mkdir(exist_ok=True)
decision=dict(schema='r23-source-adjudication/1',decision='retain_C13',new_candidate=None,source_files=9,source_kind='pure Markdown; no product scripts/tests',
    original_first_attempt='failed, retained',informed_task_restarts=1,repair_limit=None,
    current_receiving=dict(verdict='runs/R23/review/clean-initial/verdict.json',criteria={k:c['status'] for k,c in verdict['criteria'].items()},scope='Current versioned workflow + actual one-date point slice only'),
    source_basis='runs/R23/source-basis-v2.json',
    defects=[dict(defect='Every-method final-output obligation lost after recommendation',basis='workflow-design.md lines20-28,54-57; modeling.md lines76-86',judgment='Existing source requires complete outcome-to-receiving mapping. Actual workflow omitted a task-defined method set; corrected the workflow, not a case-specific product quota.'),
        dict(defect='Diagnosis text reached a receiver through historical command argv',basis='evaluation.md lines51-60; collaboration.md lines21-26',judgment='Existing withholding rule covers author diagnosis regardless of transport. Root packet violated it; narrowed actual returned fields and used a fresh receiver prospectively. A new ban repeating the same rule is not a confirmed absent source principle.'),
        dict(defect='Consumer freeze/tool errors and weaker v1 service-date filter',basis='modeling.md lines20-33,68-72; iteration-and-recovery.md lines3-30',judgment='Existing availability/version/recovery obligations apply; original code/results/errors retained and exact original point condition independently received. No general two-error stop was introduced.')],
    limits='This is a source-bound coordinator judgment, not proof that C13 always prevents defects or causes quality gain. No corrected full42-day outputs, intervals, optimization, final registry or paper were produced; original four-level/history/real-contest/frontend outcomes unchanged.',telemetry=dict(actual_model=None,tokens=None,cost=None))
for name,data in [('source-decision.json',decision),('source-basis.json',basis),('artifact-and-process-audit.json',dict(scopes=scopes,claim='Actual lock byte identity and terminal command counts; excludes tool failures before child creation, separately retained by actors.'))]:
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
paper='''# R23 定界设计探查与来源综合

新上下文只收到C13、中性业务题和原始材料，确实生成了可交接工作流；另一消费者也确实从原件实现并运行切片。但首次工作流并未满足全部接口义务：题目要求每种比较方法的未来表，原设计只保留推荐方法。首次独立判定j1 fail/j2–j4 pass原样保留，Root核查发现历史收据argv泄露修正说明，严格j4改为未验证。不能说自主首版已完整通过。

原任务R23-03 attempt1保持failed；同一设计者在独立目录做知情契约修订，推荐与交付集合分开，每个冻结方法的预测和备货各4032键，方法缺失/失败不得删去或由其他方法代替。消费科学字节不改；原34条命令、10条非零终态、8次计算中的6次失败，以及v1/v2结果全部保留。Root重新设计窄字段接收包，以原路径/hash和实际终态字段核过程，排除历史诊断argv/streams；新的接收上下文从原件复算，当前j1–j4按各自范围pass。这是知情修订后的前瞻接收，不能补成首次无反馈成功或重置旧计数。

## 实际支持和未覆盖

消费者按2026-10-14 18:00的信息预测10-15，两方法各96键。新接收者独立重算192行，Ridge与CSV最大差4.94e-11、weekly median差0；标签修订/公布时点、MAE/RMSE/bias均吻合，实际晚到修订边界被触发。34条来源过程字段逐项匹配，含10条非零exit。单日点预测是实算，不是文件存在或自评通过。

这份切片没有区间、场景、q、约束/损失复算、最终方法注册表、42日生产、敏感性或完整中文论文。单日误差不选胜者、不证明泛化/可靠性。两份操作文档的接口和科学范围表述经过接收，但没有新的论文可作语言/渲染验收。旧R22完整稿、R19四层诊断及其L3 partial、R16旧失败、正式十月规则未知、前端宿主拒绝与全部预算都不变。

## C13决定与适用限制

保留C13九份Markdown和原ZIP。已有条款要求从最终交付倒推全部原要求和接收接口、在独立上下文扣留作者诊断、核数据可用时间与版本、分类恢复、保留原失败，并将妨碍科学含义的语言纳入实质审查。本轮缺陷是这些已存义务在工作流/协调包/实现中未落实；现有证据未确认一个应另加进技能的通用缺失原则。具体源行与判断见source-basis.json/source-decision.json，不以“已有原则”追认第一次执行正确。

C13不会因本次局部接收成为通用保证；这不是新盲科学样本、Level1–4重跑、skill因果增益、获奖或正式赛事合规证据。研发计算、审计和控制脚本只在runs/，不进入产品。requested model与actual model分开，实际model/token/cost仍null。宿主前/工具构造失败没有子收据时按原轨迹/narrative保留，不能用命令数掩盖这些事件。

本阶段已回答定界设计问题，包括首次失败与实际修订；按原PLAN结束。未出现需新候选前瞻接收的源缺口，不为延续虚构R24或重复回放。R23-next按目标完成取消，不标真实启动done；总项目及其他未完成支线仍active/原状。
'''
with (OUT/'SYNTHESIS.md').open('x',encoding='utf-8') as f:f.write(paper)
print(json.dumps(dict(scopes=scopes,source='retain_C13',task_restarts=1,full_production=False)))
