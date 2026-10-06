# Codex 接续入口

成品方向为Forge meta-workflow，当前候选C9是八份纯文档：
[技能入口](runs/R14/candidate/C9/forge-agent-flow/SKILL.md)、
[可分发包](runs/R14/package/Forge-C9-meta-workflow.zip)、
[八层实际诊断](runs/R14/REPORT.md)、
[真实原题检查点](runs/R16/REPORT.md)。
包内无脚本、测试或执行器，尚未完整行为验收。

先读AGENTS.md、CODEX_HANDOFF.md、state/checkpoint.json和state/continuation.json。
R14独立诊断38项通过、2项失败：L3原案例3/2，L7改变目标；不修复或掩盖。
前端真实浏览器及两领域联合验收仍blocked，R15未启动。

R16取得上半年2026 MathorCup官方修订D题，子agent没有读取既有论文或解法。
求解actor完成材料读取，但两次恢复耗尽原案例2/2；未运行模型，未完成论文。
仅等待用户明确是否提高该原案例累计上限，保留已用2与原失败；不能自动视为授权。
原38任务、R08/R10/R11/R13失败与预算保留，主阶段仍R08，不等待ZCode。

恢复时实际执行scripts/host_preflight.py、scripts/coordinator_lease.py probe、
scripts/verify_handoff.py --json及scripts/continuation.py next。
它们是研发恢复工具，不是C9运行依赖；先核对真实租约和未决调用。
保持core.autocrlf=false，Windows显式UTF8，研发控制器实际经Linux/WSL运行。
旧入口字节在runs/R16/entry-before/；未安装个人skill，未投稿，定时器停用。
