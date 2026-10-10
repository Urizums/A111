# R24 — 真实 C13 / C14-lean Git 文件级配对复制与审计

日期：2026-10-11。此处的实际进展是**原始文件对象的 SHA-256 身份校验与 Git 树复制**；没有使用假 Skill 原件，但尚不是独立 Python `prepare` 或真实 Agent 比赛。

## 前置审计

- 固定真实来源于 commit `1e17fa9b321ad420b6413ac19fd451f215abcd7c` 的 [18 文件 catalog](REAL-CANDIDATE-SOURCE-CATALOG.json)，本轮核对它的 Git Blob SHA 为 `c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0`。
- 通过已连接 GitHub 读取 C13、C14-lean 各 9 份 Markdown，共 18 份；逐文件原始 Blob SHA 与 catalog 全部相同。另在隔离的代码执行环境以独立 SHA-256 实现对 82,299 字节原文求散列，生成每版九文件的 `sha256_by_variant`。已用 `abc` 和空串标准向量自检 SHA-256 实现。
- 两版共通的三份是 `references/frontend.md`、`references/iteration-and-recovery.md`、`references/modeling.md`；其他六份不同。

## 实际复制与回读

使用 GitHub Git Trees API，**直接引用真实 Git Blob SHA 而非模型重新生成文本**，分别为两个种子构造 `participants/arm_a/skill/`、`participants/arm_b/skill/` 树，随即从 GitHub 递归回读两个树并检查每个对象的 SHA 和路径：

| 种子（公开程序烟测） | A | B | 递归回读校验 |
| --- | --- | --- | --- |
| 12345 | C14-lean | C13 | 18/18，缺失 0，额外 0 |
| 314159 | C13 | C14-lean | 18/18，缺失 0，额外 0 |

树 ID 分别为 `b8561c576de48ff17a50b138c2bad325597fd3f7`、`f0f356a26249472f4139f83645865b90de19987c`。这两个 Git 树对象并未挂入正式分支目录；即使未来它们被清理，也可以根据固定来源 Blob 身份重新构造，不能把树对象的临时存留当作长期安全担保。

本轮也从已存在且字节精确的本地 V7 源码重新运行 `selftest`：**45/45 PASS**。源文件 `git hash-object` 为 `5128e41921196417e39e68759c05c9edadf3040a`，与 GitHub 候选 V7 一致。此项与 GitHub Git 树测试是两个**不同环境/不同层次**的检查，不能声称已经执行“本地 V7 + 全部真实 18 文件的 Python CLI”。

## 分层验收状态与下一步

**已通过**：真实来源的 18 个 SHA1 Git Blob/18 个 SHA-256 身份快照；真实 Git 对象两种排列的复制与 SHA 回读；本地整个精确 V7 的 45 项受控自测。

**未运行**：在可访问真实九文件 Skill 完整目录的 Python 环境中，直接调用 V7 `prepare` 生成真实参与者目录；随后才可以进行真正隔离的两组 Agent 阅读与执行、独立 `workflow.md` 接收及 C13/C14-lean 胜负判断。没有隔离宿主就不能晋级。

**下一次唯一优先动作**：在有权限的 A111 完整 checkout 上，冻结本报告记录的 18 个 SHA-256，执行 V7 `prepare` 两种随机分配，并逐文件核对 `participants/*/skill` 的 SHA-256 是否对应各自候选。若不一致保存第一次失败，禁止默认覆盖当前 V6。通过后才对新任务作真实双 Agent 运行，不使用本轮公开的烟测种子。

审计的机器可复核数据保存在 [REAL-CANDIDATE-GIT-OBJECT-STAGING.json](REAL-CANDIDATE-GIT-OBJECT-STAGING.json)。文件复制检查不等于宿主权限控制。
