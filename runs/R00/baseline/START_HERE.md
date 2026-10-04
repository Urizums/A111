# 接续入口

1. 读取根目录 AGENTS.md、本文件、docs/PROJECT_STATUS.md 和 state/phase-todo.json。
2. 运行 `python3 scripts/verify_handoff.py`。读取 state/checkpoint.json，核对当前阶段和下一可执行项。
3. 新任务按类型阅读 runs/S02/candidate/forge-agent-flow/SKILL.md；涉及 UI/UX 时再读 skills/design-product-experience/SKILL.md。原 skills/ 保留为不可变基线，新候选有独立哈希锁。按需展开引用。
4. **先读本次交付结果**：runs/cloud/VERIFICATION_REPORT.md、runs/S01/final-review.md、runs/S03/validation.json。S01 离线审计、S02 修订和 S03 烟测已整合；S03 首轮采集失败及同输入复测均保留。不要重新执行证据目录里的旧控制器，不对旧 ID 发查询、创建、接收或提交。
5. 当前阶段是用户要求的 D00 云端交付。若 checkpoint.lifecycle 为 delivered，本次目标已经完成，无自动启动任务。后续性能实验或长期支线须按新目标冻结范围、输入、预算和新 run；不要把路线图当作后台执行授权。若发布仍在进行，按 checkpoint.next_task_id 接续。

云端 CLI 的部署与打包见 docs/CLOUD_DEPLOYMENT.md。原阶段计划及此前入口原文保存在 state/history/，完整跨阶段历史仍在 state/project-todo.json。

未来任务若缺少 Luna 或原生子 agent，可先完成 Root 的只读计算和资料整理，将相应独立验证标为待办。Root 自查不能标作 Luna 独立审计。现有 UI 阻塞不阻止协议设计或 catalog 的结构工作。

Work 模式下，先确认仓库已被导入或 checkout 到 agent 可读写的目录。只有 GitHub URL、截图或会话摘要不足以保证代码执行能力。无执行工具时可以做审阅，但必须把运行验证保留为未执行。

历史记录中出现的个人宿主路径和原生 worker ID 只用于证明当时发生的事。新宿主应建立新 run；原宿主的待定调用若需要恢复，必须另行取得原调用者的真实状态证据，不能靠当前仓库推断。
