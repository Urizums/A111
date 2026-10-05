# R07 接手、修复与实际任务验证

PR #1 已关闭、未合并。所有者分支 `rd/takeover-r07` 从对方原提交
`6f509c8dcb54f7864a49864e21061345dc4b2b9c` 接续，源代码和旧八项阻塞保留。
仓库访问范围没有改变，定时器没有重新开启。本批是开发成果，完整产品验收仍未通过。

## 本批结果

| 内容 | 实际结果 | 可复核证据 |
| --- | --- | --- |
| 收集整理 | 固定 11 项原文件；Luna 编制能力、预算与入口索引 | `intake/`、`inventory/` |
| C6 快照恢复 | 写入或发布失败不残留部分最终目录；原路径可重试；已有目标不覆盖 | `candidate/C6-lock.json`、`validation/restore-tests-command.json`，8 项通过 |
| 独立恢复核验 | 新上下文 Luna 的 23 项检查通过，3 个预期注入错误留存 | `validation/independent/result.json`、`outcomes.json`、`commands.jsonl` |
| C6 原控制器回归 | 当前 Python 3.12，376 项通过 | `validation/c6-regression-command.json` |
| 安装/交接辅助回归 | 当前 Python 3.12，47 项通过；原两次集成失败保留 | `validation/auxiliary-final-command.json`、`integration-repair.json` |
| 原生任务组织 | Luna 实际创建独立 Luna 子 agent，复核固定 7 条器材申请及清单内容 | `flow-challenge/worker/native/`、`reviewer/report.json` |
| 业务结果与后继首步 | 3 条可调配、2 条库存冲突、2 条需补资料；工具和补资料清单都实际运行 | `flow-challenge/worker/results/allocation.json`、`evidence/commands.json`、`successor/` |

C6 增加跨宿主接续指引，区分缺少外部服务的支线与本地可继续的工作。
它是仓库版本候选，本轮没有替换已安装的个人 skill。

## 必须保留的失败和限制

原自主尝试超过约五分钟的指导窗口，截止时没有实现产物或子 agent 回执。
Root 中断并提供同任务收束指令后才完成；业务验收与独立内容核验成立，
**自主限时完成没有通过**。不能据此宣称速度提升、完整自迭代或泛化能力已获证明。
详见 `flow-challenge/host/cutoff-and-recovery.json` 和 worker 的 `history.md`。

worker 初版检查器误将 CSV 字段 `requests` 判成网络导入，且一份命令信封错报退出码。
原失败、错误信封及修正记录都保留；检查器修正不等于业务源码修正。
Root 集成先因原测试符号链接夹具被加入安装树而失败，后因修改 `.gitignore` 后
发布清单未刷新而失败。两次修正计为本批集成 2/2；不修改旧预算。
独立夹具原字节与链接目标封装为已核对的 `.tar` 数据，原日志路径不伪造改写。

恢复发布需要 Linux `renameat2(RENAME_NOREPLACE)`；不支持的宿主明确拒绝。
没有跨平台或断电耐久保证，进程被杀可能留下私有临时目录。
业务挑战是单日期、固定七条数据的本地建议，不包含真实审批、通知或 provider。
原生调用创建及最终通知按实际返回留存；完整服务端计时、全局用量和费用仍未知。
历史 Python 3.10 结果属于原批次，本轮本地没有运行 3.10。

## 后续优先级

1. R08-01：实际探测宿主与 checkout 能力，明确哪些步骤可本地重放、哪些需要原生调用或服务。
2. R08-02：Root 编制下一版短启动路径；按简单任务、系统任务、可复用 flow 分流，只读必要引用，先产出最小真实首步。
3. R08-03：新上下文 Luna 用新冻结原材料验证短路径；分别报告内容正确性、分工真实性、首产物耗时、干预次数与后继动作。原 R07 超时结论不改判。
4. 原八项阻塞继续保留；有条件时逐项处理环境、记录缺口或超限处置，不换样本清零刷通过。

接手入口：`START_HERE.md`、`docs/TAKEOVER.md`、`state/checkpoint.json`。
当前任务状态和下一阶段是否实际启动以台账及真实命令记录为准。
