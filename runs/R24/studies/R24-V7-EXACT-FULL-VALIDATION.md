# R24 V7 — 精确源码全量自测、CLI 双排列及解压复跑

日期：2026-10-11。本条是先前 [V7 阶段审计](R24-PLANNED-AUDIT-V7.md) **之后**的新验证结果；原审计当时写的「完整 V7 尚未运行」是真实历史，不能追溯改写为当时已通过。

## 规划与验证

本轮计划是：先确认 GitHub 上最新 V7 源码身份 → 将完整源码与已有研究依赖带入 Python 环境 → 在全新环境依次 `py_compile`、整份 `selftest`、12 种子真实 CLI 的 prepare/grade → 解压 ZIP 复跑 → 保留未完成的真实候选/独立 Agent 试验。

**精确源码**：GitHub `paired_experiment_v7_candidate.py` Git Blob `5128e41921196417e39e68759c05c9edadf3040a`，Python 本地重建后 `git hash-object` 一致。真实依赖 `reconciliation/rehearsal.py` Git Blob `f1b14b5caf04e1a7d9a1a37bb93675d1237a0a55`；`reconciliation/public_producer.py` Git Blob `691cb6d234e099911580edd4d5b94310ea101dfd`。

**实际运行结果**：
- Python 3.13.5，对完整 V7 和两份依赖 `py_compile` 成功。
- `python paired_experiment_v7_candidate.py selftest` 结果 **45/45 PASS**、exit 0。完整每项结果保存在本轮 ZIP 的 `v7_full_selftest.json`。
- 由单独的 `cli_smoke.py` 通过子进程调用 **12 次 prepare + 12 次 grade**：arm_a 为 C13、C14-lean 各六次，传入自建外部可信 freeze SHA，12 次自动化产物检查均通过，且未生成 winner。
- 负例：两臂完全未提交时 `grade` 返回 2；已审计来源被改动时 `prepare` 返回 2，未创建残缺试验目录。
- ZIP 将八项源码/回执文件实际解压到新临时目录，校验 ZIP CRC、ASCII 文件名、UTF-8 文本和各文件字节，重新运行 `py_compile`、45 项自测和 CLI 演练均通过。ZIP SHA-256 `c8e5df7a3aa9cdfbafa9d00511c7d6a3ff4c2f8232fd4be6e62601a6de45a7ff`。

## 首次失败及限制

第一次直接启动整份 V7 自测，因最小本地环境缺少 `public_producer.py`，遇到 `ModuleNotFoundError` 并退出。后来恢复具有正确 Git Blob 的依赖才通过。不要把首次失败标为通过，也不要把重复演练计算成独立实验样本。

本轮使用的 C13 / C14-lean 文件是**受控测试样本**，并非真正九文件各一套的原件。完整 GitHub 源码原件已在先前阶段逐项远程审计，但这不等于已经在本机完成真实 18 文件的 Python prepare。没有真实独立 Agent 阅读、没有独立冷启动接收，也没有性能赢家。使用 ZIP 复跑也不建立任何宿主级安全隔离。

## 阶段决策

V7 的 **完整语法、自测和受控 CLI 程序门**现在获得实测通过。仍**不能直接覆盖**当前 `paired_experiment.py`，也不能提升 C14-lean。

下一项只能是 **R24-03A1 的真实候选源树准备**：在可信完整检出的原始 C13 / C14-lean 九文件目录上检验 V7 的外部目录身份、最终复制字节、两种臂分配和冻结签名。之后才是 R24-03A2 双隔离 Actor、R24-03B 独立接收与 R24-03C 版本判断。
