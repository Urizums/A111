# Codex 接续入口

R19最新现场：L1/L2完整诊断done。L1首次a4 fail保留；L2首次首审6pass/实验partial保留，2616文件知情研究及499文件同一reviewer复审分别冻结，当前6pass/六维在有限实例和预算范围achieved，不证明原题最优/总体泛化。L2新版12页论文+2页报告/7图及所有原缺陷、资源中断、候选池修正保存。L3已完成中性原件身份检查与真实任务启动，新executor执行完整论文，独立reviewer的21文件源方法准备已终态冻结、21控制自测通过并等待正式生产接收，双方无其他层输出；L4仅设计冻结、论文未启动。四层C11保持不变，尚未汇总或升版。源a374e36已上传，实际后续源/CI观察以checkpoint/publication为准；仓库检查不能代替论文验收。旧失败/预算/锁不重置，见runs/R19/REPORT.md、TODO.md和state/checkpoint.json。

成品方向为Forge meta-workflow，当前候选C10是九份纯文档：
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
