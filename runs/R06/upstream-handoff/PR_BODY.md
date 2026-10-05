本 PR 交付云端部署与 R05/R06 已实现的代码、完整测试报告、原始失败及接手材料。用户已明确要求将当前成果交给上游完成剩余工作；**本次是未完成工作的交接，完整验收仍未通过。** 原修复次数、失败结论和独立验证边界全部保留。

主要实现：
- 安装器精确校验文件/目录/字节，修复复用漂移、符号链接路径和独立 Python 3.10 venv 问题。
- C4 原始输入字节快照与 C5 有界修复记录器；保留两轮实际失败驱动的版本化改进与原案例/新案例证据。
- 原预设窄屏与焦点修复，三种目录预设及确认交互修复，本地 provider 适配器，真实 HTTP 工单及双客户端 200/409 冲突验证。
- 新上下文简单任务、复杂示例审批的幂等/并发/崩溃回滚恢复，以及本地后继复核记录。长期研发台账保持 12 done / 8 blocked。

验证范围：Python 3.10/3.12 的原控制器各 368 项、C3/C5 各 376 项、辅助各 47 项已有通过记录；源码/归档安装冒烟通过。本次交接包再次在两个 Python 版本安装，**各 17 项 CLI 冒烟通过**，3585 个归档文件及运行后的安装树均核对。固定候选 1446 个文件原字节保持不变。新提交的 CI 状态见 Checks，历史 Actions 不作为新提交通过证明。

待上游继续的八项工作：

| 原任务 | 剩余内容 |
| --- | --- |
| 原预设独立 UI 验收 | Root 原旅程复测通过，但独立验收额度耗尽，原 worker 最终回执未完整对账；不能用作者补查放行 |
| 目录预设独立验收 | v2 为 74 pass / 2 个 390px 焦点采样 fail；需定位与 Root Tab 遍历结果的分歧，保留已耗尽的独立修正次数 |
| provider-neutral 本地适配器 | Root 8 项测试通过，但独立验证实际修正 3 次，超出 2 次限制；须处理超限验收 |
| 协议开销实验 | 8 样本仅完成 4 个，package 配置与计时 marker 仍有问题，2/2 修正耗尽；结论保持 inconclusive |
| 真实 provider SDK 接入 | 配置获准使用的端点、模型和身份/凭据，补真实服务验收 |
| 真实任务故障恢复 | 补服务端取消终态、真实网络故障和获准的隔离外部效果测试环境 |
| 全局额度/超时 | 补 provider 全局 usage、任务准入及取消确认观测；本地并发限制不能替代 |
| 完整跨会话接续 | 已有真实调度恢复/读取状态证据，独立冷启动和实质后继执行未完整验证；定时续跑已按用户要求关闭 |

独立验证超限、部分原生回执未完整留存属于本次执行/记录缺口；不归结为功能通过。历史 R03 独立 UI 失败、C1 inconclusive 保留，未换样本或重置预算。复杂任务尚未证明原生子 agent 自主分工，所有审批规则和副作用仅为本地示例。

接手入口与证据：
- [上游接手说明：逐项结果、原 task ID、下一步和证据](https://github.com/waw1w1/A111/blob/dev/runs/R06/upstream-handoff/README.md)
- [本次交接包安装与冒烟](https://github.com/waw1w1/A111/blob/dev/runs/R06/upstream-handoff/validation.json)
- [R05/R06 完整验证报告](https://github.com/waw1w1/A111/blob/dev/runs/R06/VERIFICATION_REPORT.md) · [问题清单](https://github.com/waw1w1/A111/blob/dev/runs/R06/issues.json)
- [当前 checkpoint](https://github.com/waw1w1/A111/blob/dev/state/checkpoint.json) · [原始任务/验收/预算台账](https://github.com/waw1w1/A111/blob/dev/state/continuation.json)
- [本次未完成交接授权](https://github.com/waw1w1/A111/blob/dev/state/upstream-handoff.json)

`check_publication_gate.py` 仍如实返回严格验收未满足；本次推送依据用户随后明确给出的交接授权，并未改写它的判定。旧 START_HERE/报告中的“不推送、等待 hourly”是此前状态，以本接手说明和最新 checkpoint 为准。代码、截图、失败、原始报告均随分支提交；GitHub Actions 可生成源码/报告交付包。定时续跑已关闭，不自动重启；是否继续研发或合并由上游决定。
