# Codex 研发交接

从 `Urizums/A111:main` 接续。用户最新决定是上传成果、合并应合并的开发工作，然后改用 Codex。
不等待原协作者或 ZCode，也不需要再问“是否继续”。当前可执行首项是 **R08-02**。
执行状态以 state/continuation.json 为准，当前阶段视图是 state/phase-todo.json，恢复点是 state/checkpoint.json。

## 长期目标与已知结果

Agent Forge 要能从自然语言需求制作并执行 agent flow、软件系统与可复用工作流，
覆盖应用/系统/前端架构、交互、视觉与动效、可靠性和实际效果验证。简单一次性任务直接完成，
系统任务走 program，明确要求可复用 agent flow 时才走 factory/package。
Codex 协调者负责架构、skill、核心实现与整合；可用 Luna 承担资料、脚手架和独立验证。
没有 Luna 时用实际可用的独立新上下文，记录真实模型与限制。

PR #1 已关闭，原源提交 `6f509c8dcb54f7864a49864e21061345dc4b2b9c` 保留。
PR #2 已合并，开发基线是 `7fd80faad93bb454a3bdfa1cff10f0fa0c6bbbca`。
R07 的 C6 修复 snapshot 恢复原子性和失败后重试：376 条继承回归、8 条恢复回归、
23 条独立 snapshot 检查、47 条辅助检查和17条安装 CLI 冒烟通过；CI 的 Python 3.10/3.12 通过。
7行设备请求试验在协助后完成，原自主限时窗口失败，不能当作效率或泛化成功。
C6 是仓库候选，尚未提升为已安装个人 skill；见 runs/R07/REPORT.md。

旧八项阻塞、原失败、锁定原材料和各候选已耗预算全部保留。完整产品发布门槛仍未通过，
开发成果合并只建立可继续研发的基线。不得清零预算、换样本改判或把本地模拟当成真实 provider 执行。

## 当前任务顺序

1. 读 AGENTS.md、START_HERE.md 和当前台账。探测当前宿主，不复用旧宿主 PID、worker ID 或绝对路径。
   运行下方检查；租约空闲且未决调用核对后持有租约，再更新共享状态。
2. **R08-02**：以 runs/R07/candidate/C6/forge-agent-flow 为基线保存 C7 到 runs/R08/candidate/，
   写明分流、最少引用、真实首步与必要独立核验的边界，再冻结文件锁。
   缩短加载路径，保留架构、质量和可复用能力；不要在普通小任务前强制扩展长计划。
3. **R08-03**：先冻结新样本、版本、验收与最多两轮修正预算，分别测试简单任务和需要独立核验的任务。
   从新上下文实际执行，记录首产物时间、正确性、干预、真实子 agent 和后继首步。
   有 Luna 时优先用 Luna，否则用宿主可用的独立 Codex 上下文；作者自检不能冒充独立验证。
   没有独立执行能力时继续可做的代码与回归，独立验收保持未验证。
4. 完成上述验收后，**实际执行 R09 的首项**，再通过 continuation advance 归档阶段。
   最后一项“启动下一阶段任务”不能只写一份计划。新阶段从真实观察选择有价值的不同类别/复杂任务，
   不为延续而制造空任务。具体标准见 runs/R08/PLAN.md、runs/R08/codex-handoff/PLAN_ADDENDUM.md 和原台账。

```sh
python3 scripts/coordinator_lease.py probe --root .
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
python3 scripts/continuation.py --help
```

新任务保留原材料字节、实际命令和首步证据，再用 continuation start/finish 绑定验收与结果。
共享 TODO、checkpoint 和核心源码由单一协调者串行整合；worker 只写分配目录。
独立验证者不接收标准答案或作者诊断。不存在用量数据时 token/cost 写 null。
测试随改动选择；界面效果必须实际运行检查，不能只给静态计划或推断成功。

## 延期支线与停止点

R08-ZCODE-01 保留在长期台账，状态仍 blocked，未调用真实账号。
用户当前选择 Codex，所以它已从 R08 阶段依赖移除；原冻结任务、回执、失败和预算未改变。
integrations/zcode/ 是可选 CLI 原型，尚未证明真实账号接通，不是主线启动前置。
当前没有需接管的活跃代码 worker，旧未决历史在 checkpoint 单独记录；定时器保持停用。

持续做到阶段结果与下一真实首步。遇到真实阻塞只暂停受影响支线，继续其他可做任务。
结束前提交代码、原始证据、TODO 与 checkpoint，按用户授权上传/提 PR，释放协调者租约。
提示词不提供无限后台执行能力；会话结束明确记录未决调用和下一动作。

## 可直接交给 Codex 的任务

```text
在 Urizums/A111 的 main 分支接续 Agent Forge。先读 CODEX_HANDOFF.md、AGENTS.md 和当前台账，核对运行能力，然后实际实施 R08-02，再推进 R08-03 和下一阶段真实首步。不要等待 ZCode；用宿主实际支持的工具与独立上下文。保留旧版本、原失败、验收和预算，不把作者自检冒充独立验证。持续执行并做相关运行测试，提交代码、证据、TODO 和 checkpoint；遇到真实阻塞只暂停受影响支线，继续其他可做任务。
```
