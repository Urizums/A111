"""Record actual independent preparation, without a production verdict."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lock = json.loads((ROOT / 'runs/R19/levels/L4/review/preparation-lock.json').read_text(encoding='utf-8'))
assert len(lock['files']) == 17
for relative in ['START_HERE.md', 'CODEX_HANDOFF.md']:
    path = ROOT / relative
    text = path.read_text(encoding='utf-8')
    before = '两个新上下文分别执行自身原工作流和独立原件/方法准备，尚无论文或验收结论。'
    after = '新executor已实际完成原件审计/真实小烟测并进入全量求解，独立reviewer17文件原件/方法准备终态冻结，25小控制通过但生产判定为空，等待正式成稿。'
    assert before in text
    path.write_text(text.replace(before, after, 1), encoding='utf-8')
path = ROOT / 'runs/R19/REPORT.md'
text = path.read_text(encoding='utf-8')
before = '| 新独立上下文仅原件/方法准备，未接收生产、未判定 |'
assert before in text
text = text.replace(before, '| 新独立上下文17份原件/方法准备终态冻结，25小控制通过；未接收生产、未判定 |', 1)
text += '\n本次协调核查实际完成：完整handoff检查18124份revision、91份skill、375份cutoff及1062份release均ok；随后新增L4准备17文件单独真实身份检查ok，原50任务identity guard保持。上述是源码/工件/依赖身份核查，不是L4论文或普通竞赛/十月大数据能力通过。\n'
path.write_text(text, encoding='utf-8')
path = ROOT / 'runs/R19/TODO.md'
text = path.read_text(encoding='utf-8')
before = '新executor执行至论文、新reviewer只做独立原件方法准备。两者不读其他层结果，未交付/未验收；'
assert before in text
text = text.replace(before, '新executor已实跑原件/小烟测及全量求解；新reviewer17文件事前方法冻结、25小控制通过但未判生产。两者不读其他层结果，论文未交付/未验收；', 1)
path.write_text(text, encoding='utf-8')
print(json.dumps({'independent_preparation_files': 17, 'production_verdict': None}))
