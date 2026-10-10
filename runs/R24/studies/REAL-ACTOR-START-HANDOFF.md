# R24：真实候选来源冻结与独立执行交接

**这一步确实做了什么**：从 GitHub 分支固定提交 `5d06530ca8c72294299ec72cb8d37c55e0eae6ee` 读取真实 C13 与 C14-lean 各 9 份 Markdown；检查共 23 条内部相对 Markdown 链接，未发现缺失目标；两个入口均含 `forge-agent-flow` 元信息。六份文件的 Git Blob SHA 不同，三份一致（`frontend.md`、`iteration-and-recovery.md`、`modeling.md`）。逐文件来源见 [REAL-CANDIDATE-SOURCE-CATALOG.json](REAL-CANDIDATE-SOURCE-CATALOG.json)。

独立重跑的 V3 程序 `paired_experiment.py selftest` 在本地为 **27/27 通过**，这属于工具自测。当前容器无法直接检出私有 A111 完整仓库，并且这里没有调用真正独立 Agent 的宿主接口，**所以没有在完整真实候选树上运行 Python `prepare`，也没有真实 C13 / C14-lean 能力对照、版本赢家或独立接收结论**。切勿用来源核对、绿色 CI、程序样例充当该结论。

**V5 入口更新**：正式 `prepare` 的参数已增加 `--source-catalog runs/R24/studies/REAL-CANDIDATE-SOURCE-CATALOG.json` 和 `--trusted-catalog-git-blob c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0`。在任一试验目录产生前，CLI 会核对外部可信清单及 C13/C14-lean 原件的所有 Markdown Git Blob；不匹配则失败。优先阅读 [V5 具体操作](TRUSTED-CANDIDATE-PREFLIGHT.md)，以下早期示意命令若缺上述参数已经过时。

## 具备真实隔离能力的宿主，按此启动

1. 在有权限的完整 A111 checkout 中，检出上面的精确提交。对照 [候选来源清单](REAL-CANDIDATE-SOURCE-CATALOG.json)，用 `git hash-object` 验证 18 份 Skill 源码；若字节不一致，停止，另存新的研究版本，不能静默替换。
2. 在见到任何新任务结果之前冻结模型、工具权限、工作时间和预算、验收条件、停止标准；在正式运行时才选择未见新种子。公开样例种子不算正式盲测。先执行 `python runs/R24/studies/paired_experiment.py selftest`。
3. 先使用本分支真实来源清单 `runs/R24/studies/REAL-CANDIDATE-SOURCE-CATALOG.json`；其**外部已核验 Git Blob** 为 `c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0`，不是旧 ZIP 中名为 `source_catalog.json` 的摘要。以未公布的新种子运行 `python runs/R24/studies/paired_experiment.py prepare --repo . --kind extract --seed <FRESH_SEED> --out <NEW_DIR> --source-catalog runs/R24/studies/REAL-CANDIDATE-SOURCE-CATALOG.json --trusted-catalog-git-blob c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0`。另选新种子准备 `--kind reconcile`，参数相同。若使用尚未晋升的 `paired_experiment_v7_candidate.py`，须在受控研究环境先完整执行其 45 项自测和真实源树准备。每次准备后将 `freeze_sha256_for_external_trusted_log` 记入主管独立日志，并逐文件核对两个 `participants/*/skill/` 目录与来源 SHA-256。
4. 在**真实隔离的两个新上下文**中分别只挂载 `participants/arm_a` 和 `participants/arm_b`。参与者不能读取 `reviewer_private`、对臂、随机版本映射或作者诊断；两组使用相同模型配置、权限和资源。仅以 `submission/` 交付，保存初次产物、失败、修复与真实运行记录，缺失的 token/cost 数据写 null。
5. 在独立评审环境运行 `python runs/R24/studies/paired_experiment.py grade --trial <TRIAL_DIR> --receipt <FRESH_RECEIPT.json> --trusted-freeze-sha256 <EXTERNAL_DIGEST>`。CLI 退出码 0 **只说明两组自动化交付检查通过且冻结哈希匹配**，不等于独立性已验证或有胜者。
6. 另启一个看不到作者诊断与隐藏真值的真实接收者，仅给原材料、约定交付及 `workflow.md`，观察能否在冷启动条件下重做工作，检查隐含步骤、遗漏、额外操作、失败恢复和实际维护开销。记录首次结论，与程序数值评分分开。

随后才能以交付质量、遗漏率、多余负担、资源消耗、独立接收成功率比较 C13 与 C14-lean；样本太小应写“证据不足”，不要预定 C14 领先。任何宿主隔离条件缺失，任务保持 `blocked`。

**项目边界**：当前 `state/checkpoint.json` 的正式活跃阶段仍是 R08，R24 仅为 PR #4 草稿研究。R24-03A（真实双执行者首轮）现仍 `not_run`；R24-03B（独立接收）现仍 `not_run`；R24-03C（证据判断）现仍 `not_run`；最后“启动下一阶段”需在前置验收完成后实际触发，不能标记成已启动。

无需再创建并行调度框架或新一批合成评测器来代替上述执行。

## 2026-10-11 操作勘误与真实文件复制回读

旧版下载材料 `forge_r24_real_candidate_handoff.zip` 内的 `source_catalog.json` 是摘要，缺少现行 CLI 所需的 `candidates/*/root` 与 `file_blobs` 结构，不得再拿它调用 `prepare`。应使用仓库中逐字节冻结的 [真实来源清单](REAL-CANDIDATE-SOURCE-CATALOG.json)。已制作一份新的可下载交接包，包含字节相同的原始清单和精确 V7；参考当前会话交付链接。该修正不改变 C13/C14 本体及旧包历史。

参阅 [真实两版十八文件 SHA-256 与 A/B Git Tree 复制回读](REAL-CANDIDATE-GIT-OBJECT-STAGING.md)。这能证明远端 Git 对象引用原件，**不等于真实文件已装入本地 Python 环境**。曾使用公开种子 `12345` 和 `314159` 完成两种分配的 18/18 Git Blob 回读，正式模型试验应选择未见新种子。V7 精确源码已在本地单独通过 45 项回归；用修复后 ZIP 缺少原始 Skill 完整目录调用 `prepare` 时正确拒绝并不产生半成品。完整真实 Python `prepare` 与独立 Agent 试验仍标记 `not_run`。
