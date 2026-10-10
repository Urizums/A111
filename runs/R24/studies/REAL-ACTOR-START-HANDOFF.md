# R24：真实候选来源冻结与独立执行交接

**这一步确实做了什么**：从 GitHub 分支固定提交 `5d06530ca8c72294299ec72cb8d37c55e0eae6ee` 读取真实 C13 与 C14-lean 各 9 份 Markdown；检查共 23 条内部相对 Markdown 链接，未发现缺失目标；两个入口均含 `forge-agent-flow` 元信息。六份文件的 Git Blob SHA 不同，三份一致（`frontend.md`、`iteration-and-recovery.md`、`modeling.md`）。逐文件来源见 [REAL-CANDIDATE-SOURCE-CATALOG.json](REAL-CANDIDATE-SOURCE-CATALOG.json)。

独立重跑的 V3 程序 `paired_experiment.py selftest` 在本地为 **27/27 通过**，这属于工具自测。当前容器无法直接检出私有 A111 完整仓库，并且这里没有调用真正独立 Agent 的宿主接口，**所以没有在完整真实候选树上运行 Python `prepare`，也没有真实 C13 / C14-lean 能力对照、版本赢家或独立接收结论**。切勿用来源核对、绿色 CI、程序样例充当该结论。

**V5 入口更新**：正式 `prepare` 的参数已增加 `--source-catalog runs/R24/studies/REAL-CANDIDATE-SOURCE-CATALOG.json` 和 `--trusted-catalog-git-blob c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0`。在任一试验目录产生前，CLI 会核对外部可信清单及 C13/C14-lean 原件的所有 Markdown Git Blob；不匹配则失败。优先阅读 [V5 具体操作](TRUSTED-CANDIDATE-PREFLIGHT.md)，以下早期示意命令若缺上述参数已经过时。

## 具备真实隔离能力的宿主，按此启动

1. 在有权限的完整 A111 checkout 中，检出上面的精确提交。对照 [候选来源清单](REAL-CANDIDATE-SOURCE-CATALOG.json)，用 `git hash-object` 验证 18 份 Skill 源码；若字节不一致，停止，另存新的研究版本，不能静默替换。
2. 在见到任何新任务结果之前冻结模型、工具权限、工作时间和预算、验收条件、停止标准；在正式运行时才选择未见新种子。公开样例种子不算正式盲测。先执行 `python runs/R24/studies/paired_experiment.py selftest`。
3. 以独立的新种子执行 `python runs/R24/studies/paired_experiment.py prepare --repo . --kind extract --seed <FRESH_SEED> --out <NEW_DIR>`，再以另一个种子分别准备 `--kind reconcile`。每个试验开始时，把输出的 `freeze_sha256_for_external_trusted_log` 写进只供主管读取、不可由参与者篡改的记录。
4. 在**真实隔离的两个新上下文**中分别只挂载 `participants/arm_a` 和 `participants/arm_b`。参与者不能读取 `reviewer_private`、对臂、随机版本映射或作者诊断；两组使用相同模型配置、权限和资源。仅以 `submission/` 交付，保存初次产物、失败、修复与真实运行记录，缺失的 token/cost 数据写 null。
5. 在独立评审环境运行 `python runs/R24/studies/paired_experiment.py grade --trial <TRIAL_DIR> --receipt <FRESH_RECEIPT.json> --trusted-freeze-sha256 <EXTERNAL_DIGEST>`。CLI 退出码 0 **只说明两组自动化交付检查通过且冻结哈希匹配**，不等于独立性已验证或有胜者。
6. 另启一个看不到作者诊断与隐藏真值的真实接收者，仅给原材料、约定交付及 `workflow.md`，观察能否在冷启动条件下重做工作，检查隐含步骤、遗漏、额外操作、失败恢复和实际维护开销。记录首次结论，与程序数值评分分开。

随后才能以交付质量、遗漏率、多余负担、资源消耗、独立接收成功率比较 C13 与 C14-lean；样本太小应写“证据不足”，不要预定 C14 领先。任何宿主隔离条件缺失，任务保持 `blocked`。

**项目边界**：当前 `state/checkpoint.json` 的正式活跃阶段仍是 R08，R24 仅为 PR #4 草稿研究。R24-03A（真实双执行者首轮）现仍 `not_run`；R24-03B（独立接收）现仍 `not_run`；R24-03C（证据判断）现仍 `not_run`；最后“启动下一阶段”需在前置验收完成后实际触发，不能标记成已启动。

无需再创建并行调度框架或新一批合成评测器来代替上述执行。
