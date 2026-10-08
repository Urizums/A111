"""Source-bound document clarification and a separate original forward case."""
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / 'runs/R19/final/candidate/C12/forge-agent-flow'
dest = ROOT / 'runs/R20/final/candidate/C13/forge-agent-flow'
assert not dest.exists()
shutil.copytree(source, dest)
path = dest / 'references/modeling.md'
before = path.read_bytes()
anchor = b'Do not use information unavailable at the proposed decision time.'
assert before.count(anchor) == 1
paragraph = (b'\n\nWhen an earlier evaluation result later feeds calibration, tuning or another\n'
    b'decision, treat it as an input at that new decision time. Check the exact\n'
    b'label revision and its arrival time, as well as the source prediction made\n'
    b'under its original information. For a joint residual or grouped statistic,\n'
    b'check when all required coordinates became available and how incomplete\n'
    b'groups are handled. A past target date or an earlier test-window name alone\n'
    b'does not establish availability. Make this rule explicit in the receiving\n'
    b'interface and test a relevant late-arrival or revision boundary.')
if b'\r\n' in before:
    paragraph = paragraph.replace(b'\n', b'\r\n')
path.write_bytes(before.replace(anchor, anchor + paragraph))
files = [p for p in dest.rglob('*') if p.is_file()]
assert len(files) == 9 and all(p.suffix == '.md' for p in files)
changed = [p.relative_to(dest).as_posix() for p in files if p.read_bytes() != (source / p.relative_to(dest)).read_bytes()]
assert changed == ['references/modeling.md']
def write(rel, text):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
def obj(rel, data):
    write(rel, json.dumps(data, ensure_ascii=False, indent=2)+'\n')
obj('runs/R20/final/candidate/C13-change.json', dict(
    previous='runs/R19/final/candidate/C12-lock.json', changed=changed, markdown_files=9,
    cause=['runs/R20/execution/evidence/repair-001.md', 'runs/R20/review/source-recheck/source-recheck-report.md'],
    decision='Narrow prospective clarification of evaluation-to-input role changes and complete-vector readiness.',
    interpretation='C12 ultimately supported an accepted result after author correction. This change has not demonstrated a causal failure-rate improvement.',
    excluded='No solver/model/page quota, fixed rounding precision, universal calendar, package script, installed skill or revised historical verdict.',
    forward_test='runs/R20/forward-case/; original small dataset, independent external gate withheld from producer.'))
write('runs/R20/forward-case/inputs/PROBLEM.md', '''# 原创分批到达校准任务

请用提供的Forge meta-workflow搭建并实际执行一份可交接的残差校准流程。附件是既有固定原点预测、实际量版本和两个新的决策原点，数据全部为原创合成。

对每个新原点输出可用于校准的完整日向量、所选预测/标签版本与来源到达时刻、逐项残差、完整性和可用性说明，以及可复跑代码和短中文科学说明。series.csv定义每个完整日期所需的坐标。forecast_origin是既有预测的固定信息截止；原点之后补写的预测不能当成当时预测。新决策只能使用该原点已可知的信息。同键修订不是独立坐标，完全重传也不增加样本。

标签可以选择每个新原点的最新可用版本，也可采用声明的固定评价版本成熟后再纳入的保守策略；需明确政策及不足时的处理、保持所有产物一致，不得把事后才到达版本提前使用。未成完整日向量不能凭空补造。无需训练新预测模型、完整竞赛论文或获奖判断。所有时间为Asia/Shanghai；残差=所选实际量-原固定原点预测量，单位件。
''')
write('runs/R20/forward-case/inputs/request.md', '用所给Forge skill完成这份附件的可交接工作流及实际校准结果、可复跑程序和中文说明。\n')
raw = ROOT / 'runs/R20/forward-case/inputs/raw'; raw.mkdir(parents=True)
def table(name, columns, rows):
    with (raw / name).open('x', encoding='utf-8', newline='') as f:
        w = csv.writer(f); w.writerow(columns); w.writerows(rows)
table('series.csv', ['series_id'], [['A'], ['B']])
forecasts = []
for n in range(1, 5):
    for series, base in [('A', 9), ('B', 19)]:
        forecasts.append([f'2026-05-0{n}', series, 1, '2026-04-30T18:00:00+08:00', '2026-04-30T17:00:00+08:00', base+n])
forecasts += [['2026-05-01', s, 2, '2026-04-30T18:00:00+08:00', '2026-05-04T12:00:00+08:00', 99] for s in ['A','B']]
table('forecasts.csv', ['target_date','series_id','revision','forecast_origin','available_at','prediction_units'], forecasts)
labels = [
    ['2026-05-01','A',1,'2026-05-02T09:00:00+08:00',11],
    ['2026-05-01','B',1,'2026-05-03T18:00:00+08:00',22],
    ['2026-05-02','A',1,'2026-05-03T09:00:00+08:00',12],
    ['2026-05-02','B',1,'2026-05-04T09:00:00+08:00',20],
    ['2026-05-03','A',1,'2026-05-04T09:00:00+08:00',14],
    ['2026-05-03','B',1,'2026-05-04T09:00:00+08:00',23],
    ['2026-05-04','A',1,'2026-05-05T09:00:00+08:00',15],
    ['2026-05-04','B',1,'2026-05-07T09:00:00+08:00',24],
    ['2026-05-01','A',2,'2026-05-05T09:00:00+08:00',13],
    ['2026-05-01','B',2,'2026-05-05T12:00:00+08:00',24],
    ['2026-05-02','B',2,'2026-05-07T09:00:00+08:00',25],
]
labels.append(labels[0][:])
table('labels.csv', ['target_date','series_id','revision','available_at','actual_units'], labels)
obj('runs/R20/forward-case/inputs/raw/decisions.json', dict(timezone='Asia/Shanghai', origins=[
    '2026-05-03T18:00:00+08:00', '2026-05-06T18:00:00+08:00'], evaluation_label_cutoff='2026-05-08T12:00:00+08:00'))
write('runs/R20/forward-case/evaluation/ACCEPTANCE.md', '''# C13独立受影响前瞻接收

原件和这三个门在生产前冻结。本案只检验评价转校准的可用性及可交接路径，不推断通用正确率、完整论文或四层效果。

f1：原raw逐原点独立重建符合作者公开政策的完整日向量、原固定预测版本、实际量版本/到达、ready和逐值残差。原origin恰等于到达、单坐标晚到、未成熟修订、事后补写预测、完全重复要按原问正确处理；不得自定固定向量数量来拒绝声明一致的保守策略。空池必须解释，不能伪造风险估计。

f2：从raw真实重跑完整当前入口，实际消费当前产物；至少一个合法/非法控制激活时间、来源或完整性条件。拒绝非法输入/输出的证据不能仅为静态文本或描述。核对机器结果与中文说明一致、原点/量纲/限制明确。

f3：五类关键来源/时间断言有原件、实际检查、判定及限制；调用全部终态/完整记录，产物身份冻结。首判失败与知情修复分别保留，不把作者自检冒充独立通过。未实测model/token/cost为null，不设模型/页数/纠错配额。
''')
obj('runs/R20/forward-case/PLAN.json', dict(created_at=datetime.now(timezone.utc).isoformat(),
    source='runs/R20/final/candidate/C13/forge-agent-flow',
    conditions='Two fresh contexts, original small raw case, independent external f1-f3 withheld from maker, no R20 diagnoses or prior results.',
    sequence=['freeze source/inputs/external gates','fresh maker constructs and executes workflow','freeze maker','fresh receiver independently reruns and recomputes','preserve first verdict; integrate scoped result'],
    scope='Affected maturity/interface clause only; no complete competitive paper or causal C12/C13 comparison.'))
print(json.dumps(dict(candidate='C13', changed=changed, skill_docs=9, raw_forecast_rows=len(forecasts),
    raw_label_rows=len(labels), source_and_original_case_prepared=True, behavioral_validation='pending')))
