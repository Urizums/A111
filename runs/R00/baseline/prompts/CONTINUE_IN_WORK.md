# GitHub / Work 接续提示词

请在你可读写的 checkout 中继续这个 Agent Forge 项目。先读取仓库根目录 AGENTS.md、START_HERE.md、docs/PROJECT_STATUS.md、state/checkpoint.json 和 state/phase-todo.json，运行 scripts/verify_handoff.py。读取 prompts/CONTINUOUS_ITERATION.md 并据此持续推进。

先读取 runs/cloud/VERIFICATION_REPORT.md、runs/S01/final-review.md 和 runs/S03/validation.json；S01 离线审计、S02 修订及 S03 烟测已完成整合。以 state/checkpoint.json 的 lifecycle 与 next_task_id 判断是否还有本次交付任务。若已 delivered，等待新的用户目标，不重开旧阶段。新的方法使用 runs/S02/candidate/forge-agent-flow/SKILL.md；Root 负责架构/skill/修复，可用的 Luna 负责独立验证，只给它原要求与原材料，不给标准答案。

不重跑旧八个 worker，不读取后来 live 文件，不对历史 ID 新建查询/receive/commit。历史记录绝对路径用 docs/EVIDENCE_MAP.md 映射为当前证据；不要重写原件。

若用户授权新阶段，先冻结最小目标、验收、写域和预算，按仓库约束记录真实执行与证据。持续执行到该目标可核验的结果；目标完成就保存终态，不重复制造下一阶段。停止时保存能让下一 agent 直接继续的 checkpoint。
