# GitHub / Work 接续提示词

请在你可读写的 checkout 中继续这个 Agent Forge 项目。先读取仓库根目录 AGENTS.md、START_HERE.md、docs/PROJECT_STATUS.md、state/checkpoint.json 和 state/phase-todo.json，运行 scripts/verify_handoff.py。读取 prompts/CONTINUOUS_ITERATION.md 并据此持续推进。

下一工作是 S01-02：根据 runs/S01/audit-plan.json 的冻结范围，对 evidence/c1/ 截止原件完成尚未结束的离线审计。遵守 C1 Study_Plan.md 的原要求。Root 负责架构/skill/修复，可用的 Luna 负责独立验证，只给它原要求与原材料，不给标准答案。若 Luna/原生工具不可用，先做可完成的 Root 工作并保留独立验证待办。

不重跑旧八个 worker，不读取后来 live 文件，不对历史 ID 新建查询/receive/commit。历史记录绝对路径用 docs/EVIDENCE_MAP.md 映射为当前证据；不要重写原件。

完成 S01 实质任务后，最后一项“启动下一阶段任务”必须创建 S02 TODO，并实际启动 Root 修订采集边界/receipt/写域合同的首项，记录证据。持续执行到可核验结果；不把常规阶段检查当作用户确认门。停止时保存能让下一 agent 直接继续的 checkpoint。
