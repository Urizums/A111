# R24 V5 — 实际候选源码身份前置验证

## 这一轮解决的问题

V4 会冻结从本机 `--repo` 读取的候选文件；但**准备之前没有证实文件就是已审计的 C13/C14-lean 原件**。因此，执行宿主可能因误检出旧分支、文件被替换、目录多出文件，而生成内部哈希自洽但不具备候选身份可信度的实验。

V5 在 `prepare` 命令增加两个必填参数：`--source-catalog` 和 `--trusted-catalog-git-blob`。程序先验证**清单本身**匹配外部可信 Git Blob SHA，再比较真实候选目录的全部相对 Markdown 路径、数量和每份文件的 Git Blob SHA；只有全部一致才创建试验目录。由此生成的新实验格式为 `forge-r24-paired-trial/4`，评分回执为 `forge-r24-paired-grade/4`，拒绝较旧的未钉死源码身份的实验格式。数据回执里另行保存本次检查的清单身份和比较文件数。

GitHub 先前独立来源审计的清单文件为 `runs/R24/studies/REAL-CANDIDATE-SOURCE-CATALOG.json`，固定 Git Blob 为 `c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0`。真正的实验**需要由宿主从独立可信位置核对这个固定值**，不能只读取参与者提供的新哈希然后相信它。Git SHA-1 对象身份属于来源一致性检查，不是权限或组织签名保证。

## 执行步骤（在具有 A111 完整检出与独立 Agent 的环境）

```bash
python runs/R24/studies/paired_experiment.py selftest
python runs/R24/studies/paired_experiment.py prepare \
  --repo . --kind extract --seed <NEW_UNSEEN_SEED> --out <NEW_TRIAL_DIR> \
  --source-catalog runs/R24/studies/REAL-CANDIDATE-SOURCE-CATALOG.json \
  --trusted-catalog-git-blob c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0
```

`reconcile` 同理另取新种子。将输出的 `freeze_sha256_for_external_trusted_log` 写入不共享给任一执行者的可信日志；只挂载各自 `participants/arm_*`。对臂和 `reviewer_private` 必须由宿主权限真正隔离。评分仍要求外部冻结清单的 SHA-256，且任何自动评分通过都不能代表执行者独立、阅读 Skill 或冷启动接收成功。

## 实际范围和复核记录

2026-10-10：V5 源代码 `py_compile` 正常，**38/38 项内部自测通过**，包括原 V4 的回归和新加入的来源校验反例；真实 Python CLI 有 **7/7 项测试通过**（使用受控模拟候选目录），覆盖正确清单、错误清单哈希、缺失/增加/修改 Skill、没有执行者交付时不返回成功、冻结记录源清单证据。额外以 GitHub 实际审计清单的字节（Git Blob 与远端 `c8a6…` 一致）运行 CLI，在没有完整仓库候选文件的环境中返回退出码 2，并且**没有创建残缺试验**。

**未完成且不能转写为通过：** 当前容器无法联网获取完整私有 A111 checkout，无法在原 C13/C14-lean 九文件目录上完成真正的 `prepare`；也没有可调用的独立 Agent 宿主。此次来源清单存在并经过 Git 身份核验，不等于真实候选文件已经进入容器、双执行者已运行、接收者已验收或存在版本胜者。旧版 V1–V4 实验工具的首次失败/修复记录全部保留。

这是一处直接影响**实验结果归属有效性**的必要修复，不是新的通用 Skill 规则。若已在真正隔离宿主运行，优先开始 R24-03A 的首次未见任务，而不是继续添加测试工具。
