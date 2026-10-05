# PR #1 审阅要求实施与验证报告

日期：2026-10-04 UTC。目标分支 `waw1w1/A111:dev`，上游 PR `Urizums/A111#1`。要求原文逐字保存于 [review-comments.json](review-comments.json)，冻结范围见 [requirements.json](requirements.json)。D00 历史交付、C1 原始试验、原 `skills/` 与 `evidence/` 不重写。

本轮实现安装完整性修复与持续研发机制，实际执行六种不同任务形态，并已启动 R05 原预设浏览器工作。长期目标保持 active；本报告仅交付当前可审阅批次。独立 UI 验证仍为 incomplete，不能把作者补查标成独立通过。

## 要求与实际结果

| 审阅要求 | 实施、结果与证据 |
| --- | --- |
| 已安装版本复用前核验完整目录树 | `scripts/delivery.py` 比对全部文件、目录、长度与哈希。拒绝额外/缺失/改写文件、符号链接及额外空目录；拒绝时 current、launcher、deployment 保持原样。原始失败与回归见 R00 delivery 日志。 |
| Git / manifest 路径穿越与父链接 | 只接受规范相对 POSIX 路径，拒绝父目录或叶子链接；打开时逐层 O_NOFOLLOW，验证普通文件。两种来源覆盖内外父链接、链接 manifest、重复项与错误长度。打包读取同一验证后的字节。 |
| 长期目标与交付分开 | `state/continuation.json` 独立记录 active goal、delivered milestones；`scripts/continuation.py` 提供 start/finish/block/advance/delivery，原 D00 状态保留在 history。交付不关闭就绪队列。 |
| 能力与挑战双队列 | 16 项包含优先级、依赖、owner、写域、输入、冻结验收、证据、失败额度、下一动作；锁保护单状态写入，派生 checkpoint 可 sync 恢复。不是安全沙箱、模型 SDK 或多文件事务。 |
| 真正启动下一阶段 | R01–R04 历史归档最后一项均绑定下一阶段真实命令。R05 当前首项已经 Chromium 渲染原预设、检查三条原记录、切换夜色，390px scrollWidth=390；完整预设旅程仍在进行。 |
| 多类型、渐进挑战 | 一次性日历、数据迁移、命令进程恢复、新 flow、完整 HTTP 应用、UI 交互均实际执行；后续新增同时更新工单挑战，不把循环文档修改算业务结果。 |
| 具体未知点调研 | Luna 保存 Python3.10 sqlite3、SQLite transactions、foreign keys 三份一手来源、访问记录与探针。Root 据此实施显式事务与外键检查；同批幂等与整批回滚实测。 |
| Root / Luna 分工 | Root 写核心、skill、应用与状态；三个新 Luna 分别调研、隔离 checkout 接续验证、浏览器独立验收。原生返回、preflight、Root 决定均保存。宿主内部模型身份和 token/cost 不可见。 |
| 新上下文交接 | Luna 从指定原材料和仓库副本读取入口，处理进程 exit73、核对数据库逐字节回滚、同批重试，并实际启动 successor。Root 严格复核七项，未给答案；一次状态提醒及一次证据位置修正保留。 |
| 方法迭代与效果 | C3 完整候选及哈希锁增加持续研发规范；UI 观察教训另存版本锁定补充协议。各 task-result 均列目标、假设、基线、条件、观察、限制与指标，没有把“代码能跑”当全局效能结论。 |
| 当前能力与持续执行 | 六个历史分支逐项映射；三个 live provider/global/network 分支保持具体阻塞，catalog、原 preset、本地 adapter contract、并发应用继续可做。小时接续检查实际配置，未来宿主是否能运行代码尚未验证。 |
| GitHub 交付与 CI | 直接更新 fork dev；现有上游 PR 绑定该分支，推送后应自动更新。CI 需实际 push/dispatch 结果，不能根据 settings API 的 403 推断。最终记录见下方发布复核。 |

## 实际验证

| 目标 | 实际结果 | 原始证据 |
| --- | --- | --- |
| 原控制器 | Python3.10.21 / 3.12.14 各 368 项通过 | `original-regression-310.json`、`original-regression-312.json` |
| C3 候选 | 两版 Python 各 376 项通过 | `c3-regression-310.json`、`../R01/candidate-regressions.json` |
| 辅助回归 | 3.12 首轮 37 项通过；3.10 首轮一项失败，第二轮修复后 37 项通过 | `aux-regression-312.json`、`aux-regression-310.json`、`aux-regression-310-repair-2.json` |
| 安装安全回归 | 基线 12 个测试产生 13 个失败子项；修复后 12 项通过。稳定源最终复测 12 项通过，见 delivery-stable-final-312.json | `delivery-before.json`、`delivery-after.json` |
| 接续与交接约束 | 新接续控制器 8 项、handoff guard 12 项通过 | `continuation-tests-initial.json`、`../R01/handoff-guards.json` |
| 一次性日历 | 原 Europe/Paris 输入转 UTC、时长、字段、转义及 CRLF 共 8 项 | `../R01/calendar/result.json` |
| 迁移工具 | 两版 Python 各 6 个实际 CLI 案例：行与关联、同批重试、内容冲突、后期 FK 回滚、序号冲突回滚、重开完整性 | `../R01/import/validation/report.json`、`../R01/import/validation-310/report.json` |
| 独立新上下文恢复 | 原 worker exit73，6 次未提交写入回滚、数据库字节一致、原材料导入和重试，下一项实际启动；Root 7 项复核通过 | `../R02/handoff/worker/handoff-report.md`、`../R02/handoff/root-review.json` |
| 续借 flow | 四个原业务案例与 12 次错误协议拒绝通过；真实本宿主 Root 响应，非独立 provider | `../R02/flow/report.json`、`../R02/flow/task-result.json` |
| 工单应用 | 两版 Python 实际 HTTP 各 1 个完整旅程 / 9 项状态检查，SQLite 重启、409 冲突不覆盖、非法输入与转换拒绝 | `../R03/app/api-cases/report.json`、`../R03/app/api-cases-310/report.json` |
| 独立 UI | 最终脚本完成 6 项早期检查及 open→in_progress，后续等待条件错误；两次修正耗尽，Root bridge 判 blocked。API 后查另记，不冒充 UI | `../R03/ui-independent/worker/results.json`、`../R03/ui-independent/root-review.json` |
| 作者 UI 补查 | 同一最终数据库逐字节副本、同一源码，观察此前未执行的 8 项：冲突、状态循环、历史、键盘、减少动效、390px、空态和搜索恢复；全部通过 | `../R03/ui-followup/observations.json`、`../R03/ui/root-visual-review.json` |
| 后续阶段实际首步 | 原 preset 在真实 Chromium151 首次渲染并切换色板；未声称完整历史 UI 通过 | `../future/preset_browser_acceptance/first-step-command.json` |

截图已实际打开审阅。工单桌面有清楚的冲突反馈与当前状态；窄屏单列卡片、中文内容、焦点轮廓及历史可读且无横向溢出。搜索按钮两个汉字竖向换行作为扫描性建议保留，不虚构必需功能缺陷。无完整无障碍审计或用户研究。

## 问题、失败与额度

完整索引见 [issues.json](issues.json)。安装候选用完两轮功能修复：第一轮修完整树与路径边界；第二轮将 POSIX venv 改为解释器链接，解决独立 Python3.10 拷贝二进制找不到标准库。原失败均保留，不做第三轮。

`delivery-final-312.json` 的四个 setup 失败来自 Root 在测试进行时修改 CLOUD_DEPLOYMENT.md、manifest 暂时失配。校验器正确拒绝；该轮标为协调失误导致的无效产品复测，不删除、不算通过。稳定文件冻结后 12 项全部通过，另存 `delivery-stable-final-312.json`。

其他修正分别记录：flow 的 factory deliver 字段错误一次；新上下文证据目录修正一次；research/UI 的 Root bridge 决定格式各一次。独立 UI 两次修正后第三次运行仍失败，已终止该分支。作者后续观察不改它的结论，也没有重跑耗尽的脚本。当前 task-result 的产品修复数与独立 harness 修正数分列，不能只看前者推断零干预。

部分 flow/app/R04 准备与新上下文验证并行进行。原始命令有实际 begin/end，queue start 时间是 Root 登记时间，不倒填成命令起始；目录白名单是协作边界，不是系统强制隔离。新上下文副本输出已导出并附哈希，重复整个 checkout 不进入交付包。

## 未完成与恢复

- C1 仍为 partial/inconclusive；没有补跑旧样本以改变评分。
- 独立工单 UI 验收未完整通过；作者补查不能替代独立结论。原预设的完整旅程属于 R05 当前任务。
- 当前没有配置 provider identity/credential，也没有 provider 全局预算、自然网络、外部业务效果沙箱；对应三个 live 分支保留具体恢复条件。离线 adapter contract 和其他可执行任务不受牵连。
- 每小时接续检查已经启用；工具返回不证明未来拥有 checkout/exec/native 能力，后台代码运行仍未验证。未来运行先探测，仅在有实质进展、新问题或需要解除具体阻塞时通知。
- 云部署是当前托管云环境中的 CLI；工单示例默认 loopback，可运行但无公网域名、生产身份认证或永久托管 SLA。

## 发布复核

稳定源安装回归 12 项通过（`delivery-stable-final-312.json`）。Python3.12 安装到 `/workspace/agent-forge-cloud`、Python3.10 安装到 `/workspace/agent-forge-revision-310`，各 17 项 CLI 冒烟通过（`cloud-smoke/report.json`、`cloud-smoke-310/report.json`）。已安装 continue 命令正确选择仍在进行的 R05 任务。

初始新上下文输入 1698 个文件中，1695 个原字节可由 `../R02/handoff/reconstruction-map.json` 和 baseline-delta 重建；当时三个派生状态文件原字节未另存，明确标注不可精确重建，最终状态与完整过程证据已导出。不能把这称为完整可重复的原宿主快照。

候选归档包含 2082 个文件，SHA-256 为 `d0d4f213e1782d6d00dacab7c9dad259f259a85813430745abe3fc6d66671203`。从不含 Git 的新解压目录安装，完整性和 17 项 CLI 冒烟通过（`package-candidate-command.json`、`archive-install-command.json`、`archive-smoke/report.json`）。最终交付包在报告整合后生成；候选及其失败/成功记录均保留。

代码已直接推送 fork dev，远端提交 `d830f521f29533199fded1e2fded7f7d74b16cce` 的树与本地逐字节一致，上游 PR #1 自动更新且保持 open/unmerged。真实 Actions [run 37180110023](https://github.com/waw1w1/A111/actions/runs/37180110023) 已由 push 触发；Python3.10 和3.12 两项 job 均成功，原回归368、C3回归376、辅助37、真实HTTP旅程、安装17项烟测及归档上传全部成功。记录见 `ci-success.json`、`ci-jobs-success.json`、`ci-artifacts.json`、`publication-verification.json`。旧 settings API403 不影响本次真实运行。报告/checkpoint 收尾提交会再次触发 CI，最终 head 状态以 PR Checks 为准。

最终代码和报告包输出到 `/workspace/deliveries/A111-review-20261004-final.tar.gz`，旁附 SHA-256；CI Artifacts 同样提供分 Python 的源码报告包。最终包在本报告整合后生成，不能将包自身哈希嵌入其内容；候选归档回放记录已经纳入仓库。
