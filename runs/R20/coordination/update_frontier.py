"""Refresh mutable navigation only; immutable trial documents stay unchanged."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
state = json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
frontier = state['execution']['current_frontier_task']
tasks = {t['id']:t for t in state['tasks']}
if tasks['R20-04']['status']=='done':
    production_state = ('原创数据题完整11页中文论文、1344预测/整数备货已按原问获独立五门首判通过，知情来源补核保留；'
        'C13仅明确评价结果转校准输入的可用时点，九份Markdown，受影响新原件前瞻接收仍在推进。')
elif (ROOT/'runs/R20/execution-lock.json').exists():
    production_state = '完整中文论文、预测/整数备货及全部历史产物已终态并锁定602文件，独立接收正在按原始数据和最终PDF执行；五门正式判定尚未完成。'
else:
    production_state = '原创数据、稀疏请求和外部五门已冻结，新构建/独立准备实际启动，正式生产与论文验收按台账接续。'
paragraph = ('当前前沿 '+frontier+'：R20-01当前赛事/规则/数据状态检查完成，专项提交/AI条款仍未知，未声明正式合规；'
    +production_state+
    'R19四层诊断及C12有限新题首验保留：L3当前a6 partial不追认；C12九份Markdown、包内零脚本/测试。'
    '当前实质状态见runs/R20/REPORT.md和checkpoint，原C11/失败/预算不变。')
for name in ['START_HERE.md','CODEX_HANDOFF.md']:
    path = ROOT/name
    raw = path.read_bytes()
    text = raw.decode('utf-8')
    parts = text.split('\n\n',2)
    if len(parts) != 3:
        parts = text.replace('\r\n','\n').split('\n\n',2)
    assert len(parts) == 3
    content = parts[0].rstrip()+'\n\n'+paragraph+'\n\n'+parts[2].replace('\r\n','\n')
    previous = subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)
    if b'\r\n' in previous:
        content = content.replace('\n','\r\n')
    path.write_bytes(content.encode('utf-8'))
project_path = ROOT/'state/project-todo.json'
project = json.loads(project_path.read_text(encoding='utf-8'))
entry = next(t for t in project['todo'] if t['id']=='R20-data-workflow')
entry.update(status='in_progress',next_action=frontier+': original data workflow handoff through actual independent paper reception; current policy unknowns retained.')
for relative in ['runs/R20/R20-01-result.json','runs/R20/R20-02-result.json','runs/R20/input-lock.json','runs/R20/evaluation-lock.json']:
    if relative not in entry['evidence']:
        entry['evidence'].append(relative)
for relative in ['runs/R20/R20-03-result.json','runs/R20/R20-04-result.json','runs/R20/design-lock.json','runs/R20/execution-lock.json',
        'runs/R20/review/reception-preparation-lock.json','runs/R20/review/initial-lock.json','runs/R20/review/source-recheck-lock.json',
        'runs/R20/coordination/formal-reception-dispatch.json','runs/R20/final/candidate/C13-lock.json']:
    if (ROOT/relative).exists() and relative not in entry['evidence']:
        entry['evidence'].append(relative)
content = json.dumps(project,ensure_ascii=False,indent=2)+'\n'
previous = subprocess.check_output(['git','show','HEAD:state/project-todo.json'],cwd=ROOT)
if b'\r\n' in previous:
    content = content.replace('\n','\r\n')
project_path.write_bytes(content.encode('utf-8'))
print(json.dumps(dict(frontier=frontier,only_mutable_navigation_updated=True)))
