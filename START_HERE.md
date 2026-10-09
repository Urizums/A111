# Codex 接续入口

当前前沿 R22-02：C13派生完整13页中文论文及独立g1–g5接收已完成，首锁后42日实测R/W覆盖86.73%/84.42%，总损失29936.25/34625.90元，低于名义覆盖的限制保留；新R22同期限历史证据审计已真实完成，模型实验尚未启动。当前C13仍九份纯Markdown、包内零脚本/测试；R20完整11页中文论文及独立首判、C13受影响小案三门首接收保留，不称C13的四层重跑或优于旧版的因果证据。R19 L3 a6 partial、旧失败/预算不变。正式赛事专项AI/提交规则仍未知；实质进度见runs/R22/REPORT.md、R21结果附录和checkpoint。

当前技能与新实测入口：[C13技能](runs/R20/final/candidate/C13/forge-agent-flow/SKILL.md)、[C13纯文档包](runs/R20/final/package/Forge-C13-meta-workflow-candidate.zip)、[完整13页论文](runs/R21/execution/paper-final-v4/paper.pdf)、[首锁后结果附录](runs/R21/final/APPENDIX.md)、[R22当前状态](runs/R22/REPORT.md)。

成品方向为Forge meta-workflow。历史C12及四层实测入口：
[C12技能入口](runs/R19/final/candidate/C12/forge-agent-flow/SKILL.md)、
[C12纯文档包](runs/R19/final/package/Forge-C12-meta-workflow-candidate.zip)、
[四层论文与独立诊断](runs/R19/final/PAPERS.md)、
[来源综合及受影响行为验证](runs/R19/final/SYNTHESIS.md)、
[当前R20前沿](runs/R20/REPORT.md)。

前阶段C10九份纯文档和政策交付原件仍保留：
[技能入口](runs/R17/candidate/C10/forge-agent-flow/SKILL.md)、
[可分发包](runs/R17/package/Forge-C10-meta-workflow.zip)、
[政策与验证](runs/R17/REPORT.md)、
[八层实际诊断](runs/R14/REPORT.md)、
[真实原题检查点](runs/R16/REPORT.md)。
包内无脚本、测试或执行器。C10增加分类恢复、进展管理、搜索规划和来源绑定的上下文整理；受控政策判断和单次真实研究分开记录，完整产品验收仍未完成。

先读AGENTS.md、CODEX_HANDOFF.md、state/checkpoint.json和state/continuation.json。
R14独立诊断38项通过、2项失败：L3原案例3/2，L7改变目标；不修复或掩盖。
前端真实浏览器及两领域联合验收仍blocked，R15未启动。

R16取得上半年2026 MathorCup官方修订D题，子agent没有读取既有论文或解法。
旧C9尝试在两次读取恢复后停止，2/2且未运行模型，原判定保留。前瞻R18现已由同一R16-02/actor实际运行floor-only baseline并完成producer自检；见runs/R18/PLAN.md及runs/R16/prospective-20261007/checkpoint.md。这不是最优解证明或独立验收，完整论文仍未完成。
用户已要求调整业务任务通用两轮规则，2→6提议被新政策取代；不再等待该数字确认。旧R16停止结果及2/2不改判；同一任务/actor的前瞻接续必须另存修订、保持原题和实质验收。
原38任务、R08/R10/R11/R13失败与预算保留，主阶段仍R08，不等待ZCode。

恢复时实际执行scripts/host_preflight.py、scripts/coordinator_lease.py probe、
scripts/verify_handoff.py --json及scripts/continuation.py next。
它们是研发恢复工具，不是C10运行依赖；先核对真实租约和未决调用。
保持core.autocrlf=false，Windows显式UTF8，研发控制器实际经Linux/WSL运行。
旧入口字节在runs/R16/entry-before/；未安装个人skill，未投稿，定时器停用。
