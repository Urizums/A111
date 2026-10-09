"""R22 source judgment; no candidate change without demonstrated source absence."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
state=read('state/continuation.json');tasks={t['id']:t for t in state['tasks']}
assert tasks['R22-02']['status']=='done'
basis=read('runs/R22/final/source-basis.json');assert basis['source_verified'] and basis['C13_files']==9
for c in basis['clauses']:
    assert hashlib.sha256((ROOT/c['path']).read_bytes()).hexdigest()==c['source_sha256']
composition=read('runs/R22/final/reception-composition.json');assert composition['current_verdict']['h6']=='pass'
text='''# R22来源综合：C13保留，设计推导另测

完整三窗两路线共24192键历史回放已经实际完成。首次新上下文独立重建、清洁复现和完整中文论文接收h1–h5通过，h6因同一金额正文与表格不一致失败。v2统一显示舍入后仍在派生差值上作者自检失败；v3由公开CSV文本先作Decimal运算再舍入，并经知情独立完整文档接收。首稿、失败稿、首次判定、两次实质文档修正及接收端工具错误原样保留。科学源、配置、首交结果未修改。

同期限证据仍有限：两前窗合并84个不同日期，第三窗重叠25日，三窗联合101日期。每窗只有4个活动日，活动×早晚空格明确不可估计。覆盖低于名义90%的事实保留；R较低损失不等于逐窗MAE更好或未来普遍较优。已知合成历史固定策略回放不是未见样本、skill因果增益、奖项或正式赛事适用证明。

## 实验观察如何对应源要求

- workflow-design已有“从交付倒推证据、决策、依赖”和“稀疏输入不能取消推导出的领域职责”；所以42日固定交付需判断证据的期限、更新方式与评价单位，但不强制每题三个窗或相同算法。
- modeling已有同一合法数据、split、约束、资源和相关标准比较，首个可行结果后定位会改变答案的实质弱点并作定向实验；evaluation已有smoke实际激活所声称条件。短期校验可以支持有限结论，不能自动证明较长固定交付的可靠性。
- modeling已有正文、表格、单位、精度、符号、假设及主张强度必须在渲染转换后保持，含义缺陷属于实质审查；evaluation要求由违反的源条款或合理推导要求与实际反证支撑拒绝。因此本次h6拒绝与两次修正有现有源依据，不能归因于源从未要求金额一致性。
- 锁定条款逐一来源、行号、原文片段与SHA见source-basis.json；同一C13九份Markdown及原ZIP保留。本次算法、报告渲染与审计脚本属于研发原件，不进入skill产品。

目前没有足以证明一般源缺口的证据，不创建仅增加清单的C14。也不能据此宣称C13已充分解决所有自主设计问题：R22接受了协调者详细预写协议，其成功未验证新设计者能否自行从中性题目推导验证范围。

## 有限的真实下一步

R23只探查上述自主设计缺口：给新上下文C13、中性业务简报和原CSV，不发送R22详细实验方案、旧论文、结果、诊断或接收答案；另一消费者操作设计选择的实质切片，再由新接收者检查推导、可操作接口、证据和语言边界。原数据已知，不称全新科学样本或Level1–4重跑；不启动5–8。原始输入审计必须真实执行，不能以计划算首步。定界探查完成后结束，只有实质新目标才另启工作。

文档修正等待期间作者意外获得其他actor工具摘要，披露保留；此前科学生产已冻结，不追溯改成知情调参；修正与复审明确知情。未知actual model/token/cost均null，局部读写域不是OS隔离。原失败、预算、R08阻塞、R19 L3 partial、前端宿主拒绝及正式十月赛事未知规则全部保留。
'''
with (BASE/'final/SYNTHESIS.md').open('x',encoding='utf-8',newline='') as f:f.write(text)
obj=dict(candidate='C13',source_changed=False,product_markdown_files=9,package_scripts=0,package_tests=0,
    conclusion='Current evidence demonstrates execution/document defects covered by existing source, not a proven general source absence.',
    untested='Autonomous workflow designer derivation without coordinator detailed protocol.',
    next_plan='runs/R23/PLAN.md',source_basis='runs/R22/final/source-basis.json',reception='runs/R22/final/reception-composition.json',model=None,tokens=None,cost=None)
with (BASE/'final/source-decision.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
print(json.dumps(obj,ensure_ascii=False))
