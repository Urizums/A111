# 接续入口

1. 读 AGENTS.md、本文件和 state/checkpoint.json。长期目标仍为 active；D00 delivered 只表示前次交付，不能停止就绪研发。
2. 先运行 `python3 scripts/coordinator_lease.py probe --root .`。有持锁 Root、正在创建或状态未知的原生任务时先核对，不另起协调者。空闲时用 `hold --root . --owner <当前协调者标识>` 在持续打开的终端持锁，结束输入 `release`。再运行 `python3 scripts/verify_handoff.py` 和 `python3 scripts/continuation.py --root . next`。state/continuation.json 是当前执行状态，phase-todo 是阶段，project-todo 保留完整历史映射。
3. 当前待发布候选为 [C5 SKILL.md](runs/R06/candidate/C5/forge-agent-flow/SKILL.md)，文件锁为 [C5-lock.json](runs/R06/candidate/C5-lock.json)，SKILL SHA-256 为 `d1a062d34cc611addbfa84a54473ae21c770ff7c49f60cc384f1f22fb4a8a1c7`。按需读引用；C3、C4 与所有失败保留。UI 还需 skills/design-product-experience/SKILL.md 及 runs/R03/workflow/C3-ui-observation-v1.md。简单任务直接做，系统走 program，明确可复用 flow 才走 package。候选身份不代表全项目验收已通过。
4. 从 next 选出的任务及原输入/验收开始实际工作。用 scripts/record_command.py 保存真实首步，再用 continuation.py start 绑定输入和验收；完成后用 finish 提交逐条证据及效果记录。失败保留，最多两轮修复，禁止替换样本或降低验收。
5. 当前阶段的实质任务完成后，读取 state/phases/ 中的后续计划。实际启动首项，再执行 `continuation.py --root . advance --next-phase state/phases/下一阶段.json`。最后一项固定为“启动下一阶段任务”。无需用户再次说 continue。
6. Root 负责核心、架构、skill 和共享状态。Luna 做调研、边界脚手架及独立验证，只给原要求/材料。若原生能力不可用，只阻塞相关分支，继续其他就绪任务。不能把命令进程恢复说成 provider 故障恢复。

本轮要求原文在 runs/R00/review-comments.json；已执行证据从 state/continuation.json 各任务定位。历史 D00 报告在 runs/cloud/VERIFICATION_REPORT.md，原状态在 state/history/D00-todo.json；C1 效能仍 inconclusive。不要重新操作任何旧 worker ID，原绝对路径只作历史证据。

最新审阅原文在 runs/R05/trigger-recheck/pr-comments.json；R05/R06 当前结果见 runs/R06/VERIFICATION_REPORT.md。严格发布门槛在 state/publication-gate.json：全部必需验收、最终候选的独立验收及安装/归档冒烟通过，新增问题修复复测通过后，才能提交或推送 waw1w1/A111:dev。先运行 `python3 scripts/check_publication_gate.py --root .`；任何 blocked/not_run/fail、证据缺失、超额修正或未对账调用均禁止发布，不能按单批完成推送。上游 PR #1 随 dev 更新，不擅自合并上游。

现有每小时调度曾于 2026-10-04 06:16 UTC 触发到正在工作的 Root，已核实能执行代码，但尚无独立冷启动交接证据。只复用已有调度；没有可执行 checkout 时仅记录条件，状态未变不重复提醒。不能把旧预算归零、换验证者或将 Root 的复测改标为独立通过。

会话结束前同步 checkpoint，记录未决调用、额度、阻塞及真实下一动作。控制器选择任务但不自动调用模型；后台是否已配置、是否真执行，以 execution 和真实宿主返回为准。只有网页 URL 的宿主不能声称做过代码或浏览器验证。部署见 docs/CLOUD_DEPLOYMENT.md。
