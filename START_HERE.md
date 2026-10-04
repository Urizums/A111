# 接续入口

1. 读 AGENTS.md、本文件和 state/checkpoint.json。长期目标仍为 active；D00 delivered 只表示前次交付，不能停止就绪研发。
2. 运行 `python3 scripts/verify_handoff.py` 和 `python3 scripts/continuation.py --root . next`。state/continuation.json 是能力队列与挑战队列的当前执行状态，state/phase-todo.json 是当前阶段；state/project-todo.json 保留完整历史映射。
3. 新工作使用 runs/R01/candidate/forge-agent-flow/SKILL.md，按需读引用。UI 还需 skills/design-product-experience/SKILL.md 及 runs/R03/workflow/C3-ui-observation-v1.md（保留耗尽验证与作者观察的边界）。简单任务直接做，系统走 program，明确可复用 flow 才走 package。
4. 从 next 选出的任务及原输入/验收开始实际工作。用 scripts/record_command.py 保存真实首步，再用 continuation.py start 绑定输入和验收；完成后用 finish 提交逐条证据及效果记录。失败保留，最多两轮修复，禁止替换样本或降低验收。
5. 当前阶段的实质任务完成后，读取 state/phases/ 中的后续计划。实际启动首项，再执行 `continuation.py --root . advance --next-phase state/phases/下一阶段.json`。最后一项固定为“启动下一阶段任务”。无需用户再次说 continue。
6. Root 负责核心、架构、skill 和共享状态。Luna 做调研、边界脚手架及独立验证，只给原要求/材料。若原生能力不可用，只阻塞相关分支，继续其他就绪任务。不能把命令进程恢复说成 provider 故障恢复。

本轮要求原文在 runs/R00/review-comments.json；已执行证据从 state/continuation.json 各任务定位。历史 D00 报告在 runs/cloud/VERIFICATION_REPORT.md，原状态在 state/history/D00-todo.json；C1 效能仍 inconclusive。不要重新操作任何旧 worker ID，原绝对路径只作历史证据。

会话结束前同步 checkpoint，记录未决调用、额度、阻塞及真实下一动作。控制器选择任务但不自动调用模型；后台是否已配置、是否真执行，以 execution 和真实宿主返回为准。只有网页 URL 的宿主不能声称做过代码或浏览器验证。部署见 docs/CLOUD_DEPLOYMENT.md。
