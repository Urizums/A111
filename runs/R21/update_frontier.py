"""Current R21 navigation; prior paper and release evidence stay immutable."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(rel):
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def write_like_head(rel,text):
    previous=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)
    text=text.replace('\r\n','\n')
    if b'\r\n' in previous:
        text=text.replace('\n','\r\n')
    (ROOT/rel).write_bytes(text.encode('utf-8'))
state=read('state/continuation.json')
frontier=state['execution']['current_frontier_task']
tasks={t['id']:t for t in state['tasks']}
paragraph=('当前前沿 '+frontier+'：C13派生完整13页中文论文及独立g1–g5接收已完成，首锁后42日实测R/W覆盖86.73%/84.42%，'
    '总损失29936.25/34625.90元，低于名义覆盖的限制保留；新R22同期限历史证据审计已真实完成，模型实验尚未启动。'
    '当前C13仍九份纯Markdown、包内零脚本/测试；R20完整11页中文论文及独立首判、C13受影响小案三门首接收保留，'
    '不称C13的四层重跑或优于旧版的因果证据。R19 L3 a6 partial、旧失败/预算不变。'
    '正式赛事专项AI/提交规则仍未知；实质进度见runs/R22/REPORT.md、R21结果附录和checkpoint。')
for rel in ['START_HERE.md','CODEX_HANDOFF.md']:
    text=(ROOT/rel).read_text(encoding='utf-8').replace('\r\n','\n')
    parts=text.split('\n\n',2)
    assert len(parts)==3
    tail=parts[2]
    tail=tail.replace('成品方向为Forge meta-workflow。当前受检C12及四层实测入口：',
        '成品方向为Forge meta-workflow。历史C12及四层实测入口：')
    current=('当前技能与新实测入口：[C13技能](runs/R20/final/candidate/C13/forge-agent-flow/SKILL.md)、'
        '[C13纯文档包](runs/R20/final/package/Forge-C13-meta-workflow-candidate.zip)、'
        '[完整13页论文](runs/R21/execution/paper-final-v4/paper.pdf)、'
        '[首锁后结果附录](runs/R21/final/APPENDIX.md)、[R22当前状态](runs/R22/REPORT.md)。')
    if tail.startswith('当前技能与新实测入口：'):
        tail=current+'\n\n'+tail.split('\n\n',1)[1]
    else:
        tail=current+'\n\n'+tail
    write_like_head(rel,parts[0]+'\n\n'+paragraph+'\n\n'+tail)
project=read('state/project-todo.json')
entry=next(t for t in project['todo'] if t['id']=='R21-interval-reliability')
entry.update(status='done',next_action=tasks[frontier]['next_action'])
for rel in ['runs/R21/protocol-lock.json','runs/R21/input-lock.json','runs/R21/evaluation-lock.json',
    'runs/R21/R21-02-result.json','runs/R21/preparation-audit-corrected-command.json']:
    if rel not in entry['evidence']:
        entry['evidence'].append(rel)
write_like_head('state/project-todo.json',json.dumps(project,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(frontier=frontier,mutable_navigation_updated=True)))
