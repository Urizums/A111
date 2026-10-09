# R23 独立消费者切片记录

## 结论与覆盖范围

我独立实现并计算了一个历史日期的双方法点预测切片：以 `2026-10-14 18:00 Asia/Shanghai` 为信息截点，预测 `2026-10-15` 的96个门店—商品键；训练标签只取截点前已经公布、且服务日期早于截点日期的需求版本。评分标签取自 `2026-10-31 18:00` 前已公布的该日最新版本。两个方法为冻结的 `shared_ridge10` 迁移参照和 `weekly_median56`。

切片实际运行成功，源表身份与 R21 input-lock 一致，键数、可用时间边界和两个模型均通过代码内断言。实际时间边界被触发：166行训练报告在原点后才公布，44个可见训练键另有原点后才公布的报告；模型输入没有纳入这些迟到行。96条目标评分标签均在原点后公布。此结果支持这一个日期上的 point-in-time 切片执行与计算，不支持模型排序或普遍性能结论。

冻结后发现并保留了三类实现/命令问题：最初的冻结 JSON 序列化尾部错误、天气源 hash 的人工抄录错误，以及 v1 初始实现未把“服务日期早于原点日期”直接写成严格筛选。另有 v2 文件构造换行、输出目录和仓库根路径问题。每次失败均保留各自收据；v1 源码与结果保存在 `attempt-v1/`，修正实现先冻结后运行于 `v2/`。没有根据结果更换日期、方法或指标。

## 实际数值

| 方法 | MAE（件/键） | RMSE（件/键） | 平均有符号误差（件/键，预测减实际） |
| --- | ---: | ---: | ---: |
| shared_ridge10_consumer | 2.3346 | 2.8713 | 1.5008 |
| weekly_median56_consumer | 2.5104 | 3.0414 | 1.1667 |

这是同一目标日上的描述性结果。两条路线只在这一个日期上比较；差异不构成选择胜者的依据，也不表示跨期泛化。

## 方法与接收边界

参照路线按冻结业务定义重新实现：169列设计矩阵、Ridge alpha 10、无截距、非负预测截断；促销只用原点前公布的值，缺失时用训练期前56日的商品均值，再回退为零；天气与结算额不进入特征。替代路线按最近56个日历日、门店—商品—星期分组计算中位数；空分组的冻结回退为同店同商品中位数，再回退为商品—星期跨店中位数。本切片两个回退计数均为零。

为检验迟到修订边界，先按 `available_at <= origin` 筛选原始需求行，再按键和修订号选可见最新版本，并要求训练服务日期早于 `origin` 的日期。所有96个目标标签仅在预测和拟合完成后、按评估截点读取。目标促销在原点均已公布；本例没有触发促销回退。日期范围、标签覆盖与模型输出都来自 R21 原始 CSV 的重算，没有引用作者探针的数值或结果。

独立复核适用范围：此记录由新消费者上下文独立编写并实算，但这份报告本身不是另一个接收代理的 verdict，也不是 R23 acceptance。工作流提到的 producer self-check 文件及其收据没有打开或作为证据；未读取作者 probe 输出。`design-lock.json` 用于确认冻结身份；本次身份转录同时包含了锁清单中的文件名/hash，但没有读取锁清单列出的自检、诊断或输出文件内容。

## 未覆盖、仍待处理

- 没有完整历史折、后续 untouched holdout 或预先定义的多折候选比较，因此**模型排名 pending**。
- 没有完整的96维残差场景、区间覆盖率/宽度校准或90%区间有效性结果。
- 没有运行整数备货优化、重算缺货/报废目标、对照现行政策或检查每日采购/容量约束。
- 没有未来42日的4,032行预测/备货表、敏感性分析、结果图表或中文论文。
- 没有独立接收代理的原件复算与验收意见；所有全流程验收与42日可靠性仍 pending。
- 本次未按声称数据开放日期之后的真实业务预测进行评价；目标是离线历史切片，不能代表部署表现。
- 仅使用所列离线输入；没有外网搜索。文件夹写域是协作约定，不是操作系统隔离。

## 原件来源、读取域与身份

本消费者读取：`AGENTS.md`；R23 brief 中的 `TASK.md` 与 `INPUTS.json`；R23 冻结的 `WORKFLOW.md` 与 `probe.py`（只用于理解要求和接口，未执行作者 probe）；C13 Forge 的 `SKILL.md` 与八份 reference 文档及 C13 lock；R21 原始 CSV/decision.json 与 `BASELINE.md`、`experiment.json`；以及 R21 input-lock 的身份清单。R21 input-lock 指到的 `REQUEST.md`、`PROBLEM.md` 内容没有打开。没有读取 R21 `run.py`。

R23 design lock SHA-256：`83a599b90637fb2befe6e47e00ee16568785b1cd8bbfb61e29cecbf3d3ee55c4`。C13 lock SHA-256：`860caeec761028fa47723410c99ef2f48db2f61fa16405c8929a0005e158af7a`。R21 input-lock SHA-256：`dcd4f9ffd67097e6dc53cc919ed0333f9340f7dc938d7c6ea3694af7f33d53d7`。R21 七个原始文件的逐项 hash 和完整运行元数据见 [run-manifest.json](run-manifest.json)。

本消费者只写 `runs/R23/execution/**`，其中包含冻结配置、版本化源码、结果、消费报告与 `scripts/record_command.py` 生成的原始终态收据。读域和写域只是本地协作边界，不构成 OS 安全隔离。

## 运行与失败清单

使用 Python 3.12，命令形态为 `py -3.12 -X utf8 -B`，经 `scripts/record_command.py --out <unique receipt> -- <command>` 捕获。以下收据均保留，包括失败和恢复；它们的完整终端内容以文件为准：

- 原料与身份/工作流读取：`receipts/r23-consumer-01-sources.txt`、`02-identities.txt`、`03-method-sources.txt`。
- 切片资格与边界选择：`04-eligibility.txt`、`05-boundary-window.txt`（命令构造语法错误）、`06-boundary-window-retry.txt`、`07-revision-boundary-eligibility.txt`。
- v1 冻结和执行：`08-freeze.txt`；`09-compute.txt`（冻结 JSON 解析失败）；`10-inspect-freeze-error.txt`；`11-freeze-repair.txt`（第一次修复仍未去掉转义尾缀）；`12-freeze-repair-retry.txt`；`13-compute-retry.txt`（输入 hash 不匹配）；`14-source-hash-diagnosis.txt`；`15-source-fix-and-refreeze.txt`；`16-compute-final.txt`（新的冻结 JSON 序列化错误）；`17-freeze-serialization-repair.txt`；`18-compute-retry.txt`（v1成功，结果被保留于 `attempt-v1/`）。
- v2 严格原点日期边界修正与实际重算：`19-version2-freeze.txt`（命令字符串构造语法错误）；`20-version2-freeze-retry.txt`（代码换行转义错误）；`21-compute-v2.txt`（语法错误）；`22-v2-source-repair.txt`（修复脚本的展示表达式出错，源码已有写入）；`23-source-check.txt`；`24-v2-condition-fix.txt`；`25-compute-v2-final.txt`（输出路径仍指向根目录，未覆盖结果）；`26-v2-rootpath-fix.txt`；`27-compute-v2-retry.txt`（冻结 hash 不匹配）；`28-freeze-hash-diagnosis.txt`；`29-v2-output-path-fix.txt`；`30-compute-v2-final.txt`（成功）。
- 最后将运行清单中的源身份与 v2 结果报告对齐：`receipts/r23-consumer-31-manifest-consistency.txt`。
- 源码版本、输出 hash 和执行计数转录：`receipts/r23-consumer-32-final-artifact-identities.txt`、`receipts/r23-consumer-33-manifest-versions.txt`。
- 最终运行清单一致性检查：`receipts/r23-consumer-34-final-manifest-audit.txt`。

共保留34条唯一收据。实际计算命令共8次：6次失败、2次完成；完成的 v1 输出和严格修正后的 v2 输出都保留。源码版本及每版 SHA-256、两个结果文件的 SHA-256 与计数见运行清单。

失败归类：原始命令构造/冻结元数据序列化属于工具或环境恢复；天气 hash 抄录和训练日期筛选属于实现修正；没有开展模型研究迭代。恢复和修正次数按收据记录保留，不套用两次失败的停止规则。最终程序、配置、结果 hash 和软件版本以 run manifest 与 v2 输出报告为准。未知实际模型、token 与成本均为 `null`。
