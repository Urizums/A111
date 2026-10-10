# Forge R24 — 深层多余交付统计审计（V7 候选修订）

日期：2026-10-11。按「先规划与审计、复现真实缺陷、限定修补、完整复测、暂不晋级」执行。

当前 R24 的实验目标之一是比较 C13/C14-lean 是否增加不必要文档。检查 `paired_experiment_v7_candidate.py` 发现 `grade()` 的 `nonrequired_artifacts` 仅通过 `submission.iterdir()` 枚举**顶层普通文件**。在两个正确的 extract 输出中，把无用文档放进 `arm_a/submission/unused-reports/appendix/long-notes.md`，旧评分返回 `arm_a_extra: []`；它无法识别嵌套多余报告，可能低估流程负担。

修复限定在可选额外交付统计，使用 `submission.rglob("*")` 枚举深层文件和空目录，返回相对路径；仍遵守**多余报告不自动使正确的业务数据失败**。若有符号链接，不改变原 `check_submission()` 的拒绝规则。原 V7 候选保持历史不动，新增 [修订候选](paired_experiment_v7_overhead_fix_candidate.py)，未替换现役 V6。

## 实测记录

- 原 V7 Git Blob：`5128e41921196417e39e68759c05c9edadf3040a`；修复版本 Git Blob：`1640ca7d968c68167c1589244d396eda60c2eeff`。两段修改与本地文件比较，提交的整个文件哈希与测试版本相同。
- 原缺陷已在完整实际 CLI 样例中复现，`arm_a_extra=[]`，尽管多余 Markdown 在嵌套路径中。
- 修复后 `python -m py_compile` 通过，完整 `selftest` **46/46 PASS**，新增项明确检查嵌套报告和空文件夹被计入，且 `artifact_passed=true`。
- 12 种子配对受控 CLI 准备和评分重新完成，A/B 正反归属均出现六次；无提交拒绝，篡改预检 Skill 拒绝且未产生半成品。
- [可复验 ZIP](https://github.com/Urizums/A111/pull/4) 在当前会话单独交付，ZIP 解压 CRC/文件有效。详见 [机器回执](OVERHEAD-DEPTH-RESULT.json)。

**范围限制**：上述仍是受控 Skill 的整份 V7 回归，**不是**真实 C13/C14-lean 18 文件的本地 Python `prepare`；也没有真正独立的 Agent 行为对照，亦未完成 `workflow.md` 冷启动接收。远端 Git Blob 双排列复制仍只证明 Git 对象身份。当前容器无法直接认证克隆仓库，不能把远端对象当成本地 Python 源树。V7 两版均属于 R24 草稿，严禁据此宣布 C14-lean 胜出、覆盖正式 Skill 或合并 PR。

**下一步**：唯一优先验收仍是可信完整 checkout 中用真实十八文件跑 V7 `prepare` 和复制后 SHA 校验；然后才是不同真实 Agent 上的配对业务试验及独立接收。停止用更多伪 Skill 自测替代真正门槛。
