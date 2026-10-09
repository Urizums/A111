"""Cross-check frozen receiving and write a post-measurement Chinese appendix."""
import base64
import csv
import hashlib
import json
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'runs/R21'
def read(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def digest(rel): return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
def save(rel,obj):
    with (ROOT/rel).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
def near(actual,expected):
    a,b=D(str(actual)),D(str(expected))
    assert abs(a-b) <= max(D('1e-8'),abs(b)*D('1e-10')),(a,b)
initial=read('runs/R21/review/initial/result.json')
future=read('runs/R21/review/holdout/result.json')
assert all(initial['gate_status'][g]['status'].startswith('PASS') for g in ['g1','g2','g3','g4'])
assert initial['future_truth_opened'] is False and initial['gate_status']['g5']['status']=='NOT_EXECUTED'
assert future['g5_verdict']=='PASS' and future['all_preregistered_metrics_and_groups_recomputed']
assert future['initial_lock_sha256']==digest('runs/R21/review/initial-lock.json')
assert future['execution_lock_sha256']==digest('runs/R21/execution-lock.json')
assert future['evaluation_lock_sha256']==digest('runs/R21/evaluation-lock.json')
assert datetime.fromisoformat(read('runs/R21/review/initial-lock.json')['frozen_at']) < datetime.fromisoformat(future['first_truth_open_utc'])
freeze=read('runs/R21/execution/prospective-freeze.json')
for name,sha in freeze['source_hashes'].items():
    assert digest('runs/R21/execution/source/v1/'+name)==sha
commands=[]
for domain in ['execution','review/initial','review/holdout']:
    for f in (BASE/domain).rglob('*.json'):
        record=json.loads(f.read_text(encoding='utf-8'))
        if not isinstance(record,dict) or record.get('schema')!='forge-command-record/1': continue
        assert record['state']=='finished' and record['end'] and type(record['exit_code']) is int
        for stream in ['stdout','stderr']:
            assert base64.b64decode(record[stream+'_base64']).decode('utf-8',errors='replace')==record[stream]
        commands.append(dict(path=f.relative_to(ROOT).as_posix(),state='finished',exit_code=record['exit_code'],begin=record['begin']['utc'],end=record['end']['utc']))
scientific=next(c for c in commands if '002-' in c['path'] and c['path'].startswith('runs/R21/execution/commands/'))
assert datetime.fromisoformat(freeze['actual_frozen_at_utc']) < datetime.fromisoformat(scientific['begin'])
root=read('runs/R21/final/root-decimal-holdout.json')
with (BASE/'review/holdout/group_metrics.csv').open(encoding='utf-8',newline='') as f:
    independent=list(csv.DictReader(f))
by_group={(r['route'],r['dimension'],r['group']):r for r in independent}
assert len(by_group)==len(independent)==len(root['groups'])==166
def band(text): return '-'.join(f'{int(v):02d}' for v in text.split('-'))
checks=0
for row in root['groups']:
    dimension,group=row['dimension'],row['group']
    if dimension=='overall': group='all_42_days'
    if dimension=='activity': group='activity' if group=='1' else 'ordinary'
    if dimension=='horizon_band': group=band(group)
    if dimension=='activity_horizon':
        activity,horizon=group.split('|'); dimension='activity_x_horizon'
        group=('activity' if activity=='1' else 'ordinary')+'_'+band(horizon)
    other=by_group[(row['route'],dimension,group)]
    assert row['keys']==int(other['key_count']) and row['dates']==int(other['date_count'])
    mapping={'mae':'abs_error','bias_pred_minus_truth':'error','coverage':'covered','below_rate':'below',
             'above_rate':'above','mean_interval_width':'width','mean_interval_score':'interval_score'}
    for metric,m in mapping.items(): near(other[metric],row['mean'][m]); checks+=1
    near(other['rmse'],row['rmse']); checks+=1
    for metric,m in {'shortage_yuan_per_day':'shortage','waste_yuan_per_day':'waste',
                     'two_part_loss_yuan_per_day':'loss','q_units_per_day':'q','procurement_yuan_per_day':'procurement'}.items():
        near(other[metric],D(row['total'][m])/D(row['dates'])); checks+=1
with (BASE/'review/holdout/daily_route_differences.csv').open(encoding='utf-8',newline='') as f:
    ind_days={r['service_date']:r for r in csv.DictReader(f)}
assert len(ind_days)==len(root['daily_differences'])==42
for r in root['daily_differences']:
    other=ind_days[r['date']]
    near(other['loss_yuan_delta_weekly_minus_ridge'],r['loss_W_minus_R'])
    near(other['interval_score_mean_delta_weekly_minus_ridge'],D(r['interval_score_W_minus_R'])/D(96))
    checks+=2
state=read('state/continuation.json')
old=read('runs/R21/before/task-identities.json')
tasks={t['id']:t for t in state['tasks']}
identity=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
assert all(identity(tasks[k])==v for k,v in old.items())
assert not state['execution']['current_native_pending']
save('runs/R21/final/CLOSURE.json',dict(schema='r21-source-bound-closure/1',independent_gates=['g1','g2','g3','g4','g5'],
    first_verdicts_preserved=True,optional_wording_note=initial['evidence']['paper_note'],
    root_decimal_groups=166,numeric_cross_checks=checks,commands=commands,
    nonzero_commands=[c for c in commands if c['exit_code']],all_current_workers_terminal=True,
    old_task_identities_preserved=len(old),C13_source_unchanged=True,model=None,tokens=None,cost=None,
    limitations='One synthetic sample; independent reception is not a causal skill comparison, coverage guarantee or competition outcome.'))
text='''# R21 首锁后的结果附录与接续

本附录在13页完整中文初稿、生产域和独立首轮接收分别冻结后新增。初稿中的“未来实绩未知”描述的是首交付时点，原稿不回写；以下是独立g5开放固定新真值后的测量。算法、配置、历史选路、两条4032键预测及整数备货没有修改，作者未获得未来答案用于调参。

| 新未来42日指标 | R：共享ridge10 | W：56日星期均值 |
| --- | ---: | ---: |
| MAE（件/键） | 2.6083 | 3.1379 |
| RMSE（件/键） | 3.2686 | 4.0283 |
| 名义90%区间实测覆盖 | 86.73% | 84.42% |
| 平均宽度（件） | 10.1730 | 11.0424 |
| 协议区间评分（件/键） | 14.1471 | 17.3942 |
| 缺货损失（元） | 19,844.10 | 23,470.10 |
| 报废损失（元） | 10,092.15 | 11,155.80 |
| 两项损失总额（元） | 29,936.25 | 34,625.90 |
| 日均两项损失（元/日） | 712.77 | 824.43 |
| 采购支出（元） | 226,028 | 226,038 |
| 总备货（件） | 64,537 | 64,590 |
| 产能满载日 / 预算满额日 | 24 / 0 | 12 / 0 |

R在这一段未来的总损失比W少4,689.65元（111.66元/日）；W有5日更低、37日更高。这支持本次历史预选R的有限样本表现，不能证明C13比旧skill更好：R正是旧算法政策在新历史上的公平重拟合，没有产生超越该基线的新方法。W更简单，但本次并未改善结果。两者覆盖都低于名义90%，不能宣称可靠性问题已解决。

活动日各12个、普通日各30个。R活动日覆盖82.03%、普通日88.61%；W为69.18%、90.52%。R在22–28步整体覆盖79.76%，该带活动子组72.92%，仍有明显薄弱处；各交叉活动子组只有2个日期，不推断显著性或因果。4032店品键、42连续日期及共享训练均不能当作独立重复。完整166组、逐键和42日配对保留于[独立测量报告](../review/holdout/HOLDOUT_REPORT.md)和同域CSV。

接收者g1–g3通过；g4通过且保留可选措辞提示。root在此明确：虚构案例中的R计划只是研究产物，不是现实采购建议。g5的PASS表示事前两路线测量、组别与资源核验完成，不是另设成功配额。独立报告可行性段的“24/12个产能满载日/预算满额日”表述容易混淆；准确解释为R/W产能满载日分别24/12，两者预算满额日均0，其原表与数据正确。本附录澄清，首报告不覆盖。

root在独立首判后用独立Decimal计算逐组交叉核对，并逐日核对两路线损失/评分差；仅为额外整合检查，不冒充独立接收。作者一次公式渲染错误、一次预期已有目录拒绝、接收者一次provenance解析失败及所有原收据都保留；工具恢复、科学修复和研究分别记录。g5首次封装真值读取之后发生一次授权只读文件探查，工具输出存在但未用recorder封装，明确披露且不伪造收据。实际模型/token/费用未知为null。

当前C13仍九份纯Markdown，包内零脚本/测试；没有确证源头缺口就不自动发布C14。本次实际行为接收不是四层重跑、真实比赛表现或获奖证据，专项AI/提交规则仍未知。R19 L3部分达成及旧失败/计数/主R08阻塞均保留。

下一项有依据的研究是补齐同期限验证：R21历史每原点14日，固定交付42日；15–42步不能只靠原14日成绩。R22先从同一历史原件实查42日窗口、标签版本/到达、残差整日来源、外生量可用性、活动×步长覆盖和窗口重叠，然后另锁同期限实验。既有历史和本次已见未来不再叫新未见样本，不因局限就更换样本或追调首方案。

[完整初稿Markdown](../execution/paper-final-v4/paper.md)与[13页PDF](../execution/paper-final-v4/paper.pdf)保持第一次交付身份；本附录与独立评价共同构成当前交付的测量边界。
'''
with (BASE/'final/APPENDIX.md').open('x',encoding='utf-8') as f: f.write(text)
attempt=tasks['R21-03']['attempts'][-1]
evidence=['runs/R21/execution-lock.json','runs/R21/review/initial-lock.json','runs/R21/review/holdout-lock.json',
          'runs/R21/final/CLOSURE.json','runs/R21/final/APPENDIX.md','runs/R21/root-decimal-holdout-command.json']
save('runs/R21/R21-03-result.json',dict(task_id='R21-03',attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
    criteria=[dict(id='t1',status='pass',evidence=evidence)],
    effect=dict(target=tasks['R21-03']['title'],hypothesis='Independent scientific reception and first-lock future measurement expose real limitations without success quotas.',
        baseline='Frozen old current-policy ridge10 algorithm refitted on original new history; weekly mean56 is an actual simpler candidate.',
        conditions='Single original synthetic case; g1–g4 before truth, g5 only after first production and receiving locks.',
        observations=future['route_metrics'],metrics=dict(groups=166,root_numeric_cross_checks=checks,model=None,tokens=None,cost=None),
        limits='Coverage below nominal; future/date dependence and horizon mismatch retained. No causal skill/real contest/prize guarantee; C13 unchanged.'),
    next_action='R21-next: actually audit feasible 42-day historical evidence under a source-bound R22 plan.'))
print(json.dumps(dict(independent_gates=5,numeric_cross_checks=checks,commands_terminal=len(commands),old_tasks_preserved=len(old),C13_unchanged=True)))
