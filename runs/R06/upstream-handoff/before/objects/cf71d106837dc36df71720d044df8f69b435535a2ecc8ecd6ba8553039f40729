# R05 / R06 验证报告（未发布工作区）

当前长期目标仍为 active。本轮代码和证据尚未提交或推送 dev；上游 PR #1 仍使用此前 head `e3f3d9771df00b669e119ac2f7571d24875e8afe`。全部必需验收通过才可发布，局部通过不能覆盖下列阻塞。最终门槛结果见 `final/publication-check.json`，问题及恢复条件见 `issues.json`。

## 真实环境与原要求

本轮从 GitHub 读取 fork dev 的 START_HERE、checkpoint、continuation 和上游审阅原文，保存在 `../R05/trigger-recheck/`。最新要求来自评论 `5977007477`。云宿主有实际可写 checkout、命令执行、Python 3.10.21 / 3.12.14、Chromium 151 和 Playwright；`environment-final.json` 显示 connected，但没有配置 provider 凭据、身份或全局资源接口。所有应用副作用限于本地示例数据库/文件。

固定候选是 `candidate/C5/forge-agent-flow/`，原始锁 `candidate/C5-lock.json`；C4/C5、应用和两个 UI 修复版本的完整性锁是 `revision-lock.json`。原 skills、evidence、source-lock、C1 inconclusive 和全部失败保留。安装器的既有两次修复预算没有重置，也未修改其源码。

## 结果索引

| 范围 | 已实际执行的结果 | 证据及限制 |
| --- | --- | --- |
| 原控制器 / C3 / C5 | Python 3.10、3.12 各 368 / 376 / 376 项通过 | `regression/original-*.json`、`c3-*.json`、`c5-*.json` |
| 新 C4 字节快照 | 两版本各 7 项通过；复杂任务 12 份分派前原文件成功恢复 | `snapshot/`；不能补回历史从未保存的字节 |
| 新 C5 修正记录器 | 两版本各 8 项通过；实际保留三种原故障，第三次修正/第四次运行被拒绝；新材料一次修正后输出 16 | `budget/`；约束本地合作调用，不是 provider 全局强制限制 |
| 本地适配器 | 两版本各 8 项 Root 回归通过；独立执行虽最终通过，但实际用了 3 次修正，超过 2 次限制 | `../future/provider-adapter/`；独立验收 blocked，不用超限结果放行 |
| 工单 HTTP 与并发 | 两版本完整 HTTP 旅程通过；真实双客户端同版本请求为 200/409，历史未丢失 | `regression/http-*/`、`../future/concurrent-ticket/`；保留首次 harness 失败和一次修正 |
| 原 UI 预设 | Root 修复后原 10 个旅程及 390/320/680/1440px 焦点/宽度复测通过 | `../future/preset_browser_acceptance/`；独立验证预算及原生终态对账仍阻塞，不改判旧 R03 |
| 三种新任务预设 | 原创审阅队列、盘点与文档批注；v1 真实确认交互失败、Root v2 修复后的 3 项定向回归通过 | `../future/versioned_preset_catalog/`；同一验证者 v2 为 74 pass / 2 个 390px 焦点采样 fail，2/2 额度耗尽，整体验收 blocked；Root 9 组完整 Tab 遍历通过保持单列 |
| 新上下文简单任务 | 原始 3 点 GeoJSON 正确，直接交付，没有套 factory | `handoff/simple/root-review.json`、`reconcile-final.json` |
| 新上下文复杂任务 | 原始 7 条示例审批/转人工；29 份进程结果；重试幂等、真实双进程冲突、提交前崩溃回滚并原请求恢复 | `handoff/complex/root-review.json`、保留 SQLite 和 processes.jsonl；首命令采集不完整，不宣称原生子 agent 自主分工 |
| 后继首步 | 本地后继复核 `manual-review-3273f785a7e4c995` 实际启动，生成 6 条缺失资料 | `handoff/complex/worker/outputs/manual-review-task.json`；没有通知、真实指派或审批权限 |
| 协议开销实验 | 计划 8 个样本，实际 4 个原生任务完成；协调端 2 次修正耗尽，另有 marker 顺序错误 | `../future/host_protocol_overhead_comparison/report.json`；blocked / inconclusive，不宣称提速 |
| 调度接续 | 已观察 06:16:44 UTC 的真实触发、活动 Root 执行和单 checkout 竞争锁测试 | `scheduling/`；不是独立冷启动，跨会话强验收 blocked |

## 失败、修复与预算

反馈闭环详见 `FEEDBACK_LOOPS.md`。两次核心修订来自实际字节缺失和修正次数漏记；保留前后版本、原失败以及新案例，不以任务编号或文档数量代替改进。

原预设 Root 使用 2/2 次修复；目录 Root 使用 1/2（最终以预算审计为准）。原预设独立 harness 用完 2 次，之后还发生 reply CLI 修正，不能升级为完整独立通过。适配器独立验证的第三次修正经原执行顺序复核确认，已否决。协议开销协调端 2/2 耗尽后停止剩余样本。新上下文复杂任务业务验证一次通过，但保留冻结前字段检查调整与后续过期草稿；Root 对账脚本及结果提交格式各修正一次，原返回均保留在 `handoff/`。

辅助回归首次在新证据未加入索引、旧导出清单未刷新时运行，安装副本缺失证据，两版本各有 5 个安装准备失败，原输出保存在 `regression/aux-*.json`。这是实际失败。按原源码补齐交付文件和清单后才能复测；不修改安装器、不丢弃首次失败。随后实际发现全阻塞状态的校验缺陷：校验器误拒绝已启动后阻塞的阶段和没有就绪项的 active 目标。已保存旧源码、先运行 2 个失败回归，再修复状态判断，14 项状态不变量通过；完整辅助套件增至 47 项。交付整合 Root 两次修正已用完。最终辅助回归、安装及归档冒烟记录见 `final/`。

## 安装与归档核验

本轮使用独立云端前缀 `/workspace/agent-forge-review-R06-py312` 与 `/workspace/agent-forge-review-R06-py310`。最终安装内容哈希及每项检查由 `final/summary.json` 索引；该文件不存在或检查不是 pass 时不得推定已通过。安装后的 C5 快照/记录器另外运行实际测试，不把旧 launcher 的通过当作新工具验证。

代码归档及其交付 manifest 固定具体字节。归档自己的复测结果只能保存在包外的伴随报告中；最终审阅包同时包含该代码归档和后验报告，避免把事后证据回填成归档前事实。用户拿到的审阅包不是 dev 已发布证明。本轮没有新的 GitHub Actions 运行；此前已发布 head 的 Actions 成功只属于历史版本。

## 发布与恢复

`state/publication-gate.json` 绑定完整候选文件哈希、验收状态和实际证据。发布脚本先执行只读门槛检查，blocked/not_run/fail、证据漂移、超额修正和未对账调用都拒绝；本地检查不是 GitHub 分支保护，也不自动证明语义正确。

缺少 provider 接口/身份/凭据、全局额度及取消终态观测；原独立验收与协议实验存在耗尽预算；旧预设终态回执无法完整对账；独立冷启动未发生。这些不能通过换样本、换验证者、重置预算或作者补查自动解除。保留同一台账和恢复条件，继续真实就绪分支。所有当前就绪项结束后，等待具体条件变化；状态不变不重复提醒。

既有 hourly automation 只复用一个；当前 Root 持有 checkout 租约，退出时释放并保存 checkpoint。后续真实触发必须重新核对 checkout、能力、提交及未决任务，才能声明冷启动接续已经执行。交付、PR 更新或合并都不关闭长期目标。

## 本轮最终核验记录

最终候选身份：`8b82e835160fd8318ac0dd2e30c5f1cc32832af5b8cd3254f96decbee5bd60d1`，覆盖 1,446 份固定文件。源码安装与解压归档安装，均在 Python 3.10 / 3.12 分别通过 47 项辅助回归、17 项 CLI 冒烟及 C5 快照 7 项 / 有界执行 8 项运行测试；运行后 exact-tree 再校验通过。原控制器 368、C3/C5 各 376，以及局部协议/应用回归的原记录也完整保留。

源码安装内容 ID：`50869f19eafb9f139c863de2ad7f76024994661d93eb1add85dd9af7507b1977`（3,430 文件）。加入安装证据后生成的代码归档内容 ID：`c9949853d1db92769195d22853d80dc04c81a39da1582b4a13a7dd0b866e9303`（3,459 文件）；代码候选哈希保持相同。归档 SHA-256：`6f670dd77fd4e1f17cd440aaa21b44927811a73c15cefb1da1cfcc190f924a02`。归档解压后的两个安装前缀为 `/workspace/agent-forge-archive-R06-py310`、`/workspace/agent-forge-archive-R06-py312`。完整索引见 `final/summary.json`。

本轮源文件 `git diff --check` 通过。原网页快照、抽取日志和修正 diff 保留原空白，整体 raw-evidence diff check 会报告空白警告；完整输出保存在 `final/preserved-source-whitespace.txt`，不为格式检查改写原证据。

当前 GitHub PR 仍 open、未合并，head 仍为 `e3f3d9771df00b669e119ac2f7571d24875e8afe`；实际只读返回在 `final/pr-status.json`。本轮仅暂存，未 commit、未 push。发布检查预期拒绝且实际拒绝；不要把测试通过摘要当作全部验收已通过。
