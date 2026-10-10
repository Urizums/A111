# R24 — C13 / C14-lean 实验暴露协议修正（V4）

日期：2026-10-10。范围：`runs/R24/studies/paired_experiment.py` 的研究实验入口，**不修改** C13、C14-lean 及正式 Forge Skill。

## 发现的问题

以前的 `START_HERE.md` 使用「按需参考 skill/SKILL.md」。如果参与者完全忽略其候选 Skill，也能完成输出并被评测；这时比较结果可能仅反映通用模型本领或任务难度，而不是 C13/C14-lean 的影响。原工具的 V3 27 项自测没有验证候选 Skill 必须被告知要阅读。此问题属于**干预暴露不确定性**，不等价于已经发现模型真的跳读。

## 修正方式

现在两个臂都获得相同的入口要求：开始前完整阅读本臂 `skill/SKILL.md`，`references/` 按实际任务选读，不机械执行所有示例。确保输入要求相等，但不强迫多余角色、阶段和文件。

冻结实例版本升为 `forge-r24-paired-trial/3`；含 `protocol: skill_entry_read_required/1`，评分时严格检查。旧 `/1`（臂归属有错误）和 `/2`（Skill 阅读仅为可选）均不能进入新的候选归因集合。评分回执另升为 `forge-r24-paired-grade/3` 并带 `trial_schema`。接收结果新增 `skill_read_observed_in_independent_host_trace: false`，避免把文本指令或产物正确性当作实际阅读轨迹。

## 实际验证

1. 从旧 V3 受测 Git Blob `622deed823278519fb12a305737c707c3e4ebdfc` 开始修改；本轮受测新源代码 Git Blob 见 `PAIRING-EXPOSURE-V4-RESULT.json`。
2. Python 3.13.5：`python -m py_compile paired_experiment_v4.py` 通过；`python paired_experiment_v4.py selftest` 共 **31/31** 通过，增加两臂相同的必读入口检查、冻结协议字段、拒绝 `/1` `/2` 和非法协议等回归。
3. 分别在随机分配 `arm_a=C13` 和 `arm_a=C14-lean` 的两个种子里，执行真实 CLI `prepare` 与带外部冻结 SHA 的 `grade`；已测试的两边使用作者生成的正确 JSON 交付，命令退出码均为 0。回执独立阅读标记仍为 false；**这里是模拟产物，不是两个 Agent 的独立执行。**
4. 从 GitHub 固定提交 `5d06530ca8c72294299ec72cb8d37c55e0eae6ee` 只读检查真实候选：双方各九份 Markdown、23 条相对链接未发现失效，六份内容不同、三份内容相同。真实目录的 `paired_experiment.py prepare` 未在当前无私库 checkout 的容器完整执行；详细来源在 `REAL-CANDIDATE-SOURCE-CATALOG.json`。

## 严格保留的剩余验收

- **必须由实际 Agent 宿主工具轨迹**确认两个执行者真实读取各自的 SKILL.md；不能只凭提示词、模型自报、正确答案或 CLI 成功来认定干预已经发生。
- 真正独立执行者的上下文、资源预算、另一臂与私有真值隔离必须另行验证。需使用新冻结、尚未曝光的样本；此前测试种子只用于程序回归。
- 独立的自然语言工作流接收者仍没有运行；不存在 C13/C14-lean 优劣结论。避免为缺少真实宿主而继续制造虚假独立性测试。
- 原始 V1/V2/V3 问题和第一次失败证据保留在 Git 历史；**不要事后把旧版 `/2` 的试验提升为已正确暴露 Skill 的 V4 试验**。

下一次行动：在 ChatGPT Work / 实际允许独立 Agent 的执行宿主，按 `REAL-ACTOR-START-HANDOFF.md` 用 V4 重新冻结任务，保存真实阅读轨迹、每臂首次交付、评分和独立冷启动复现。主 checkpoint 仍 R08；R24 为草稿研究。
