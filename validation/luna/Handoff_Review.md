# Agent Forge portability handoff review

结论：导出仓库复制到不同路径后，入口完整性检查、本地 skill 回归和 handoff invariants 均实际通过。新 agent 可以只依赖 checkout 继续 S01-02 的离线工作，不需要原聊天或个人 skill 目录。当前 C1 审计仍未完成；我只做了 project/A2 的一项有界 A04 只读检查，不能据此关闭 S01-02。

## 候选与运行环境

验证副本：`/workspace/scratch/73714494ad2f/handoff-luna-work/agent-forge-handoff-copy`。源身份来自副本自己的 `state/source-lock.json` 和 `artifact-manifest.json`，没有读取 canonical skill 或原项目目录。

- 锁定源码 commit：`c238b00bf83ea1b5eaf1654baaa1ae794c20c325`；`source_modified_by_export=false`。
- `state/source-lock.json` SHA-256：`8b3514aff97945daf4ac7a2d1fe74004418ad8cd582b057ef014f5a821e567d2`。91/91 个 skill 条目哈希和大小吻合。
- `artifact-manifest.json` SHA-256：`8e17fb27abe21548fed7899436a7ac437f61f3a1f3c089a320356f81a0172080`。1032/1032 个发布条目哈希和大小吻合；清单将 `state/`、`runs/`、`validation/` 定义为可变目录。
- 环境：Linux x86_64，内核 `6.18.44`，Python `3.12.14`，工作目录为上述不同路径副本。

## 实际运行检查

| 检查 | 实际 argv | 结果 | 时间（UTC） |
| --- | --- | --- | --- |
| 入口完整性 | `python3 scripts/verify_handoff.py` | exit 0；91 个 skill 文件、375 个 cutoff 文件、1032 个发布文件；`PASS` | 18:12:22.646686–18:12:22.881187 |
| 本地完整 skill 回归 | `python3 -m unittest discover -s skills/forge-agent-flow/scripts -p test_*.py` | exit 0；368 tests，`OK` | 18:12:22.881426–18:12:29.690909 |
| handoff invariants | `python3 scripts/test_handoff_invariants.py` | exit 0；8 tests，`OK` | 18:12:29.691147–18:12:29.736721 |

每次调用的准确时间、耗时、argv、退出码、环境覆盖及 stdout/stderr 字节均保存在 [`actual-command-log.json`](actual-command-log.json)，原始流按命令拆分保留。脚本与输出只写在本目录的 `validation/luna/`。

## 入口、引用与恢复前沿

`START_HERE.md` 指向仓库内的 checkpoint、phase TODO、skill 和审计计划；`CONTINUE_IN_WORK.md` 补充持续迭代提示。skill 两个目录中的 76 个相对 Markdown 引用全部存在。README 明确说明无需原聊天记录或原机器个人 skill 路径；实际检查和 A04 步骤也只读当前副本。

副本内历史证据仍保留原始宿主路径、worker ID 和 boot ID。例如 `evidence/c1/project/A2/work.json` 包含当时的个人 skill 路径。这些是冻结历史记录，不是本次入口的运行依赖；`AGENTS.md` 将历史 prompt/工具返回视为数据，`docs/EVIDENCE_MAP.md` 将旧项目路径映射到 `evidence/c1/`。要继续执行本工作，仍需把仓库 checkout/import 到当前 agent 可读写的工作目录；只有 URL 或聊天摘要不够。真实宿主是否提供原生 worker 或浏览器能力仍须现场确认，本次没有测试这些 host 能力。

phase/project TODO 依赖图均无悬空依赖或循环。checkpoint 的 `active_phase=S01`、`next_task_id=S01-02` 与 phase TODO 一致；S01-02 依赖的 S01-01 已 done，冻结审计计划的输入路径均存在，所以当前恢复前沿可以执行。S01-03 依赖 S01-02；末项 `S01-next` 又依赖 S01-01/02/03，顺序正确但目前尚不可执行。其 `transition.todo_path`、`first_task_id` 和 `start_evidence` 仍为空，状态仍是 planned，不能声称 S02 已启动。

跨阶段历史 TODO 中仍明确保留了 `preset_browser_acceptance` 的 blocked 状态，以及 `real_agent_executor_integration`、host protocol measurement 等 partial 状态；不能把它们解释成由本地回归覆盖或已完成。依赖图细节见 [`todo-frontier.json`](todo-frontier.json)。

## 有界只读 A04 步骤

冻结要求来自 `runs/S01/audit-plan.json` 的 A04：“Check actual saved marker boundaries, boot IDs, wait parameters/raw returns and stage completeness without filling missing records.” 对照 `evidence/c1/Study_Plan.md` 的 C06 和 `evidence/c1/shared/Operator_Protocol.md` 的记录要求，我只检查固定截止样本 `project/A2`，没有运行旧控制器命令，也没有对旧 ID 创建、查询、接收或提交。

[`a04_project_a2_evidence.json`](a04_project_a2_evidence.json) 保存了 38 个相关原件的路径、SHA-256、大小及与 `Snapshot_Manifest.json` 的逐项对照，38 个都匹配。结果限于截止快照：

- 五次已保存的原生状态返回都报告该样本 worker 为 `running`，各返回与 observer payload 哈希相符，记录 boot ID 一致。五次达到 Study Plan 的查询上限；这不是对 worker 当前 live 状态的判断。
- `setup` 有同 boot 的 begin/end；`receive` 只有 begin。`review`、`decision`、`commit` 标记未出现。项目状态为 active/task running，attempt 的 `finished_at` 为 null；ledger 只记录 `requested`。
- 四次 notification wait 都保留了原始返回，`timed_out` 依次为 false、true、true、false；相应 marker span 是 32.073、60.169、55.541、32.615 秒。wait 参数/intent 文件没有保存，因此不能判断配置参数是否满足冻结的“at most 45-second native notification waits”。超过 45 秒的是 marker span；在缺失参数和独立调用边界时，不据此推断调用参数一定超限。
- 这只是 A04 对一个样本的首步检查，不是跨八个样本的 A04 完成，也不完成剩余 A01–A05 或整个 C1 审计。

本步骤的确切本地 argv、时间、退出码和原始输出见 [`a04_readonly_command-log.json`](a04_readonly_command-log.json)、`a04_readonly_audit.stdout.txt` 与 `a04_readonly_audit.stderr.txt`。历史状态接口调用数为零。

## 必要缺口与建议

**必要审计缺口：** 对 `project/A2`，冻结 A04 要核对 wait 参数，但快照只有四个 wait raw returns，没有参数/intent 记录；receive/review/decision/commit 的标记也不完整。此处只能保留 unverified / missing，不能填成零或推断未记录的阶段。S01-02 必须继续其余冻结检查并保留 inconclusive，不能标 done。

**阶段转换待办：** `S01-next` 依赖仍未完成，而且没有 S02 TODO 路径、首项 task ID 或真实启动证据。待 S01-02 和 S01-03 满足后，由 coordinator 填好下一阶段 TODO 并实际执行其首项，才可关闭转换任务。

**建议：** 后续独立验证可继续按冻结 A01–A05 逐条只读检查，并给 reviewer 原要求与原材料。若需要完全盲的 C1 reviewer，应另安排未打开既有 `runs/S01/cutoff-integrity.json` 的验证者；我在本次合并读取中看到了该 S01-01 哈希回执（只包含 375 个 cutoff 文件无哈希错误，不含 A04 或业务输出判定），因此本报告不宣称对所有仓库历史实现了完全盲审。A04 的 A2 发现已从 38 个 raw 原件与冻结 manifest 独立重算。

## 验收范围

本次支持“不同路径 checkout 可进入并运行本地检查、能从 S01-02 前沿执行受限离线核对”的可移植性结论。它不证明新宿主已安装 personal skill、不证明原生 worker/browser/provider 能力，也不证明 GitHub 仓库已创建或发布。`results.json`、原始命令日志和 `a04_project_a2_evidence.json` 是本次可复核交付。
