"""Refresh mutable reading entries only after actual R23 first-step integration."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
s=read('state/continuation.json');tasks={t['id']:t for t in s['tasks']}
assert s['execution']['current_frontier_task']=='R23-02' and tasks['R23-01']['status']=='done'
assert not s['execution']['current_native_pending']
receipt=read('runs/R22/final/receipt-audit.json')
counts='；'.join(f"{d['domain']}：{d['count']}条终态/{d['nonzero']}条非零" for d in receipt['domains'])
r22=f'''# R22 同期限历史验证已完成

固定三原点、两路线的42日研究实际完成，共24192键。新上下文从原件独立重建、清洁复现，首次h1–h5通过；h6因同一金额正文与表格不一致失败。第一修正版v2又因金额差值先作浮点相减而作者自检失败，未进入独立接收。第二修正版v3改为公开CSV十进制文本先计算金额再统一舍入，完整中文Markdown及13页PDF经知情独立h6复审通过。首稿、失败稿、首次独立失败与原268份科学字节保留，原任务attempt1/2失败、attempt3通过、repair2/null上限；作者核验工具错误另列，未降低原h1–h6要求。

[完整中文研究稿](execution/correction-v3/report/REPORT.pdf)、[正文](execution/correction-v3/report/REPORT.md)、[首判](review/initial/REVIEW.md)、[修正后独立判定](review/recheck-v3/result.json)、[来源综合](final/SYNTHESIS.md)、[接收组合](final/reception-composition.json)。

同期限只是匹配评价长度：前两窗84不同日期，第三窗重叠25日，联合101日期，不能称126次独立重复；每窗4个活动日，空格不可估计，覆盖低于名义90%的事实保留。知情合成历史回放不证明未见数据表现、现实采购、skill因果增益、四层重跑、获奖或正式十月赛事适用性。R21首锁后一次42日测量及旧论文/失败保持原样。

Root额外185384项数值核对与37项相关接续回归通过；整库安装检查主动中断，未声称通过。实际原始命令：{counts}。全部收据含开始/结束、完整流及实际退出，详情见final/receipt-audit.json。

修正等待期间作者调用代理清单，工具意外返回其他actor摘要，包括非本修正文档所需的未来结果与首判；实际暴露和作者未使用声明保留，科学字节未改。修正文档和复审明确知情，不声明全程上下文隔离或未见摘要。actual model/token/cost未知为null。

现有C13十项实际源条款已经要求从交付倒推证据、稀疏输入下领域职责、匹配比较、smoke激活条件及正文/表格/渲染的数值和意义一致性。当前未证明一般源缺口，保留九份纯Markdown和原ZIP，不为执行失误添加C14或产品脚本/测试。

R22-02/03/next已完成，R23-01已经实际从冻结原CSV核查中性输入、版本可用性和4032键交付范围；当前R23-02待新上下文自行制作验证与执行工作流，未构建新工作流、未执行消费切片或获得设计接收。[下一阶段](../R23/REPORT.md)。原71份非本轮任务身份、旧失败/预算、R08阻塞、R19 L3 partial及前端宿主拒绝保留。

此前eb8d217对应CI37884838207实际success，属于该提交的源码检查；新增成果的main提交、逐blob核验和CI观察另存publication，不把旧CI算新成果通过。没有后台worker或定时接续承诺，checkpoint记录当前前沿和真实租约终态。
'''
(ROOT/'runs/R22/REPORT.md').write_text(r22,encoding='utf-8')
(ROOT/'runs/R22/TODO.md').write_text('''# R22 TODO

- [x] R22-01 实际42日历史窗口与信息可用性审计。
- [x] R22-02 同期限计算、首判与两次文稿修正后知情独立接收；原失败保留。
- [x] R22-03 来源综合；现有条款覆盖所观察缺陷，保留C13。
- [x] R22-next 冻结R23中性角色输入并实际执行R23-01原CSV审计。

当前前沿R23-02，尚未构建新工作流；R22修复2/null，旧计数不归零。详情及局限见REPORT.md和final/SYNTHESIS.md。
''',encoding='utf-8')
(ROOT/'runs/R23/REPORT.md').write_text('''# R23 自主设计探查已实际启动

R23-01已完成：计划、中性业务输入、角色读取边界及独立接收要求在原CSV审计前冻结。实际核对历史需求版本、训练原点可用性、42日固定未来范围及12店×8品×42日=4032键，并与原输入锁核对字节；没有拟合、读未来真值或旧设计/论文/结果。这是协调者真实输入审计，不算新工作流或独立设计通过。

当前R23-02 ready/not started，没有活跃生产者或后台调度。下一步交给新上下文C13、中性业务题和原始业务数据，自行设计可转交工作流、主张所需证据、执行分支与接收职责。协调者详细研究协议、审计结论、旧答案和接收答案不发给设计者。再由另一消费者执行一条有意义切片，新接收者从原件核查实际触发条件及界限。

[计划](PLAN.md)、[中性题目](brief/TASK.md)、[实际首步](audit/INPUT_AUDIT.json)、[冻结源](source-lock.json)、[实际审计锁](audit-lock.json)。原数据已知，此为定界的设计迁移探查，不称新盲科学样本、四层重跑或skill因果增益。切片也不自动接收完整论文；不强制模型/窗口/页数或两次重试配额。实质来源不足时保留未验证范围，不虚构完整通过。

C13仍九份Markdown，研发脚本不进入产品。既有失败、预算、正式十月比赛未知规则及前端宿主拒绝保留，actual model/token/cost均null。完成本定界问题后结束，仅有新的实质目标或具体缺口才另启任务。
''',encoding='utf-8')
(ROOT/'runs/R23/TODO.md').write_text('''# R23 TODO

- [x] R23-01 中性输入冻结与实际原CSV审计。
- [ ] R23-02 新上下文自主制作验证与执行工作流。
- [ ] R23-03 另一消费者真实切片与新上下文独立接收。
- [ ] R23-04 来源综合，确证源缺口才升级并作受影响前瞻验证。
- [ ] R23-next 完成本定界目标后明确结束；有实质新目标才真实启动下一阶段。

当前只有输入首步完成，工作流设计未开始。无活跃actor/后台调度；旧失败与预算保留。
''',encoding='utf-8')
summary='当前前沿 R23-02：R22三历史原点×两路线的42日回放及独立接收已完成；首判h1–h5通过/h6失败、v2作者金额自检失败均保留，第二次文稿修正后知情h6复审通过，原科学字节不变。C13仍九份纯Markdown、包内零脚本/测试。R23-01已真实核对中性输入与4032键固定交付范围；新工作流设计尚未开始，下一步检验新上下文能否自行推导验证范围与接收职责。不是Level1–4重跑、skill因果增益或获奖证明。旧失败、预算、R19 L3 partial、前端宿主拒绝及正式十月规则未知保留。'
links='当前入口：[C13技能](runs/R20/final/candidate/C13/forge-agent-flow/SKILL.md)、[C13纯文档包](runs/R20/final/package/Forge-C13-meta-workflow-candidate.zip)、[R22完整13页研究稿](runs/R22/execution/correction-v3/report/REPORT.pdf)、[R22证据综合](runs/R22/final/SYNTHESIS.md)、[R23真实首步与前沿](runs/R23/REPORT.md)。'
for rel in ['START_HERE.md','CODEX_HANDOFF.md']:
    p=ROOT/rel;text=p.read_text(encoding='utf-8');parts=text.split('\n\n');assert parts[1].startswith('当前前沿 R22-02')
    parts[1]=summary;parts[2]=links;p.write_text('\n\n'.join(parts),encoding='utf-8')
print(json.dumps(dict(current_frontier='R23-02',R22_complete=True,R23_real_first_step=True,source_changed=False),ensure_ascii=False))
