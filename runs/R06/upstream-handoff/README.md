# R05 / R06 上游接手入口

本次交付代码、完整验证报告、原始失败与剩余工作，供上游继续研发。**完整验收仍未通过，不是通过验收的发布版本。** 用户最新明确指示：“那就不用了，直接提pr过去，让上游完成剩下的工作，注明剩下的内容”。授权记录在 [state/upstream-handoff.json](../../../state/upstream-handoff.json)。该指令允许将当前未完成版本提交到 `waw1w1/A111:dev` 更新上游 PR #1；没有合并上游，也没有将原失败改判通过或重置修复次数。

本入口和 checkpoint 的交接状态覆盖旧 START_HERE/报告中的“暂不推送、等待小时调度”说明。旧报告保留生成当时事实；严格验收检查仍会返回失败，不能将本次交接授权当作验收成功。原每小时 automation 已关闭并复查确认，取消回执见 [cancel 记录](../scheduling/cancel-20261004T074313Z/REPORT.md)。

## 已交付的实现与验证

- 版本化 C4 原始字节快照与恢复、C5 有界修复记录器，来自实际失败的两轮反馈改进；原始 skill、C1、C3、C4 和所有失败保留。推荐候选为 [C5](../candidate/C5/forge-agent-flow/SKILL.md)，SKILL SHA-256：`d1a062d34cc611addbfa84a54473ae21c770ff7c49f60cc384f1f22fb4a8a1c7`。
- 原预设页面 v2 的窄屏与焦点修复；审阅队列、盘点、文档批注三种目录预设及确认对话框修复。Root 补查与独立验证分别记账。
- provider-neutral 本地适配器；真实 HTTP 工单旅程及双客户端并发，一个 200、一个 409，历史保留。
- 新上下文简单 GeoJSON 任务与复杂示例审批任务；幂等、并发、进程崩溃回滚/恢复及本地后继复核记录。没有真实审批/通知副作用，也未证明原生子 agent 自主分工。
- Python 3.10/3.12 下原控制器各 368 项、C3/C5 各 376 项回归通过；最终辅助各 47 项通过。源码及解压归档安装各自的 17 项 CLI 冒烟通过，C5 快照 7 项、有界执行 8 项也在安装后运行。

上述既有测试绑定 [固定候选清单](../final/source-candidate.json) `8b82e835160fd8318ac0dd2e30c5f1cc32832af5b8cd3254f96decbee5bd60d1` 的 1446 个文件。本次交接保持这些文件原字节，新增交接说明、状态和证据；新提交的 CI 结果须另查，不能拿旧 Actions 当作新提交通过证明。

完整结果：[验证报告](../VERIFICATION_REPORT.md)、[问题清单](../issues.json)、[反馈闭环](../FEEDBACK_LOOPS.md)、[最终运行证据索引](../final/summary.json)、[修复次数审计](../final/repair-budget-audit.json)。原报告中的“未发布”描述为报告生成时的历史状态，远端是否收到本轮内容以 PR 的实际 head 为准。

## 留给上游的八项必需工作

| 原 task ID | 实际结果 / 缺口 | 上游下一步与原证据 |
| --- | --- | --- |
| BACKLOG-preset_browser_acceptance | Root v2 原 10 个旅程及多宽度补查通过；独立验收额度耗尽，原 worker 的终态回执未能完整对账 | 保留原标准、原 worker 记录和历史失败，先处理原验收额度与回执；不要用 Root 补查替代独立验收。[原结果](../../future/preset_browser_acceptance/root-final-review.json) |
| BACKLOG-versioned_preset_catalog | 独立 v2 结果为 74 pass / 2 fail，失败是 390px review/stock 焦点采样；Root 完整 Tab 遍历通过，二者仍须区分 | 定位页面行为与采样方法之间的分歧；独立 harness 已用完 2 次修正，继续前须明确原预算的处置，不换样本。[原结果](../../future/versioned_preset_catalog/root-final-review.json) |
| CAP-sdk_adapter_contract | Root 本地 8 项协议测试通过；独立验证实际用了 3 次修正，超过 2 次限制，最终通过不能放行 | 处理超限独立验收并保留全部原执行顺序。它不等于真实服务接入验证。[次数核对](../../future/provider-adapter/independent/budget-clarification.json) |
| BACKLOG-host_protocol_overhead_comparison | 冻结 8 样本只完成 4 个；package 配置仍无效，并有 P2B marker 顺序错误；Root 2/2 修正耗尽 | 保留 inconclusive/失败结论；先处理原样本和剩余额度，不能替换样本得出提速结论。[原报告](../../future/host_protocol_overhead_comparison/report.json) |
| BACKLOG-real_agent_executor_integration | 未配置独立 provider 的端点、模型与授权身份/凭据 | 配置获准使用的真实服务并运行原 SDK 验收；Codex/Luna 原生协作不能代替独立 SDK 证据。[台账](../../../state/continuation.json) |
| BACKLOG-real_worker_failure_recovery_trials | 本地命令进程崩溃已测；服务端取消终态、真实网络故障及外部效果试验缺失 | 提供取消完成的观测契约和获准测试的隔离环境，再执行原案例；不执行真实业务副作用。[台账](../../../state/continuation.json) |
| BACKLOG-bridge_budget_timeout_validation | 当前宿主缺少 provider 全局 token/admission/cancel-ack 数据 | 增加真实服务端观测，核对全局额度与终止状态；本地并发限制、取消请求、null usage 不能替代。[台账](../../../state/continuation.json) |
| R06-scheduled_handoff | 已观察活动 Root 内触发，以及上轮退出后真实触发/读取状态；独立冷启动上下文与实质后继工作未完整验证 | 在有真实就绪任务时取得恢复、选择、命令、状态和后继首步证据；定时任务已由用户取消，不擅自重建。[后一次实际观察](../scheduling/resume-20261004T072138Z/observation.json) |

修复次数是实验约束，不是账户余额。当前 12 done / 8 blocked 不表示项目完成。历史 R03 独立 UI 失败、C1 效能 inconclusive、缺失原字节等历史限制继续保留；本轮交接没有替换这些结论。具体输入、验收、attempts、依赖和剩余额度以原 [continuation](../../../state/continuation.json) 为准。

## 接手与复核

先读本入口、checkpoint、continuation 和各原结果。旧 worker ID / PID / `/workspace/...` 路径是历史证据，不是新宿主的活任务；不要据此重派或恢复外部效果。恢复时先在自己的 checkout 核对实际租约和能力，保留全部失败及原输入字节。

```sh
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
python3 scripts/check_publication_gate.py --root .
```

前两条用于完整性和真实队列检查；第三条当前预期退出 2，说明严格验收仍未满足。交接授权没有修改检查器，也没有伪造 green 状态。

如需复现代码与安装检查，可使用现有 `.github/workflows/validate.yml` 的原命令（Python 3.10/3.12）。CI 的 Artifact 包含源码、报告及运行输出；CI 成功仍不能覆盖上述独立验收、服务能力和历史次数限制。

完整本地审阅包 `A111-R06-complete-review-20261004.tar.gz` 的 SHA-256 为 `bbe6179b9f39089e16dd00c77bbc897a7ddf2c47b356a25f8c4e6ab59d4bdf12`，生成时间早于本次交接状态更新；元数据见 [complete-review.json](../final/complete-review.json)。原包不含之后的取消调度和本次说明，因此以本 PR checkout 的最新 state 为接手入口。所有代码、报告、截图、原失败均随本分支提交，不依赖该本地压缩包才能接手。

本次另生成 `A111-upstream-handoff-20261004.tar.gz`（3585 个文件），SHA-256 为 `440c3185021c429933eb82040ba700f8281dcf5a12baeb3d3a05c0e36b0e526c`。逐文件核对解压字节后，Python 3.10/3.12 各自实际安装并通过 17 项 CLI 冒烟，运行后安装树再次通过核验。归档后产生的验证结果与此补充说明作为包外伴随记录提交，不回写旧包。见 [本次验证](validation.json)、[3.10 原始结果](smoke-py310/report.json)、[3.12 原始结果](smoke-py312/report.json)。这些通过结果不替代上表中的未完成验收。
