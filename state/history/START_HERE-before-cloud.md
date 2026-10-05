# 接续入口

1. 读取根目录 AGENTS.md、本文件、docs/PROJECT_STATUS.md 和 state/phase-todo.json。
2. 运行 `python3 scripts/verify_handoff.py`。读取 state/checkpoint.json，核对当前阶段和下一可执行项。
3. 按任务类型阅读 skills/forge-agent-flow/SKILL.md；涉及 UI/UX 时再读 skills/design-product-experience/SKILL.md。按需展开引用，不把全部参考文件塞进每个简单任务。
4. **继续 S01-02：完成 C1 尚未结束的离线独立审计。** 先读 runs/S01/audit-plan.json、evidence/c1/Study_Plan.md 和 docs/EVIDENCE_MAP.md。只读原始截止证据，输出写入 runs/S01/。不运行证据目录里的旧控制器命令，不对旧 ID 发新查询、创建、接收或提交。
5. 将实际结论、命令返回、证据路径、未解决项写回当前阶段 TODO 和 checkpoint。S01 最后一项要求启动 S02 的首个任务；先创建下一阶段 TODO，再真正执行首个任务并保存证据，才能关闭转换任务。

若缺少 Luna 或原生子 agent，可先完成 Root 可做的只读计算和资料整理，将独立验证标为待办。Root 自查不能标作 Luna 独立审计。现有 UI 阻塞不阻止离线审计、协议设计或 catalog 的结构工作。

Work 模式下，先确认仓库已被导入或 checkout 到 agent 可读写的目录。只有 GitHub URL、截图或会话摘要不足以保证代码执行能力。无执行工具时可以做审阅，但必须把运行验证保留为未执行。

历史记录中出现的个人宿主路径和原生 worker ID 只用于证明当时发生的事。新宿主应建立新 run；原宿主的待定调用若需要恢复，必须另行取得原调用者的真实状态证据，不能靠当前仓库推断。
