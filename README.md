# Agent Forge：可接续研发工作包

> **状态索引（2026-10-10 审查快照）**：首先阅读 [CURRENT_STATUS.md](CURRENT_STATUS.md)。历史段落的“当前”不代表最新候选；C13 为最近的九 Markdown 候选，R23 定界已结束，R08 历史门仍 blocked。R24 文档修改仅为候选，尚无新行为验收。


目标：让 agent 从自然语言需求完成软件或 agent flow 的设计、实现、验收和后续迭代，并把进度留在仓库中。这个仓库包含当前 skill 源码、项目历史、下一阶段任务、接续提示词，以及最近一次实验的原始截止证据。

**Codex 从 [CODEX_HANDOFF.md](CODEX_HANDOFF.md) 和 [START_HERE.md](START_HERE.md) 开始。** 不需要原聊天记录，也不需要原机器上的个人 skill 路径。用户已选择从 `main` 接续；长期目标保持 active，R08-02 已完成，R08-03 历史固定门仍受阻。双队列及真实证据见 [接续状态](state/continuation.json)，当前阶段见 [checkpoint](state/checkpoint.json)。ZCode 留作延期实验，不阻塞主线。

历史候选 [C6](runs/R07/candidate/C6/forge-agent-flow/SKILL.md) 修复了 C5 的 snapshot 恢复与重试缺陷，旧候选全部保留。开发基线经 PR #2 合并，结果见 [R07 报告](runs/R07/REPORT.md)，下一阶段见 [R08 计划](runs/R08/PLAN.md)。R05/R06 的预设、协议适配器与工单示例见 [原验证报告](runs/R06/VERIFICATION_REPORT.md) 和 [问题台账](runs/R06/issues.json)。原八项阻塞及 [完整发布门槛](state/publication-gate.json) 仍保留；开发成果合并不代表完整产品验收通过。

核心交付是 CLI 与研发工作包；工单挑战另提供可运行的 HTTP/SQLite 示例。已有云端 CLI 路径为 `/workspace/agent-forge-cloud`，本轮待验收安装使用独立前缀，实际路径及内容哈希见本轮报告。部署生命周期由当前宿主管理。

## 使用

```bash
python3 scripts/verify_handoff.py
python3 scripts/continuation.py --root . next
python3 -m unittest discover -s skills/forge-agent-flow/scripts -p 'test_*.py'
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/deploy_cloud.py --prefix /workspace/agent-forge-cloud
/workspace/agent-forge-cloud/bin/agent-forge --help
python3 scripts/smoke_cloud.py --prefix /workspace/agent-forge-cloud --out /tmp/forge-smoke-new
```

完整性检查不会执行旧 host 状态；本地回归和 CLI 冒烟不能替代真实 worker、浏览器或 provider 测试。CLI 与工单运行要求为 Python 3.10+ 标准库，浏览器验收另用 Playwright/Chromium。安装、工单启动、搬迁、打包方法见 [云端部署说明](docs/CLOUD_DEPLOYMENT.md)。

长期目标保持 active。R05 原预设和新增目录均有真实 Chromium 浏览器记录；Root 复测、独立验收、预算耗尽和 provider 缺口分别列明。历史调度的实际触发记录保留，但定时器现已按用户要求停用。独立冷启动接续尚未验证，不据此宣称永久后台研发。

把 [prompts/CONTINUE_IN_WORK.md](prompts/CONTINUE_IN_WORK.md) 发给能够读取并写入本仓库的 agent。需要通用持续迭代行为时，使用 [prompts/CONTINUOUS_ITERATION.md](prompts/CONTINUOUS_ITERATION.md)。宿主是否支持原生子 agent、Luna、浏览器或持久后台执行，需要现场核实。提示词不能自行提供这些能力。

## GitHub 托管与复用

上游仓库为 [Urizums/A111](https://github.com/Urizums/A111)，Codex 从 `main` 接续。[PR #1](https://github.com/Urizums/A111/pull/1) 已关闭且源历史保留；[PR #2](https://github.com/Urizums/A111/pull/2) 已合并。此前发布记录 `state/github-publication.json` 和 `runs/cloud/` 属于原始交接历史；后续成果与原始证据在 `runs/R07/`、`runs/R08/`。仓库访问权限以 GitHub 为准，原快照的私有描述不代表当前可见性。

若要复制到另一个 GitHub 仓库：

解压交接包，在 GitHub 创建空仓库，再在本目录执行：

```bash
git init
git add .
git commit -m "Add Agent Forge continuation workspace"
git branch -M main
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```

若使用提供的 git bundle，可先 `git clone agent-forge-handoff.bundle agent-forge-handoff`，然后将 origin 改成自己的仓库。本次已按用户明确授权发布到 Urizums/A111；上述命令用于后续复制到其他仓库。

## 文件入口

| 内容 | 入口 |
| --- | --- |
| 接续顺序与当前首项 | START_HERE.md、state/phase-todo.json |
| agent 工作约束 | AGENTS.md |
| 进度、局限与中断 | docs/PROJECT_STATUS.md |
| 下一阶段和长期路线 | docs/ROADMAP.md |
| skill 分流、架构与验证工作流 | docs/WORKFLOW.md |
| 原证据路径映射 | docs/EVIDENCE_MAP.md |
| 完整历史 TODO | state/project-todo.json |
| 便携 skill 快照 | skills/forge-agent-flow、skills/design-product-experience |
| C2 历史候选与锁定哈希 | runs/S02/candidate/forge-agent-flow、runs/S02/candidate-lock.json |
| C3/C5 历史候选 / C6 当前候选 | runs/R01/candidate/forge-agent-flow、runs/R06/candidate/C5/forge-agent-flow、runs/R07/candidate/C6/forge-agent-flow |
| 能力 / 挑战双队列 | state/continuation.json |
| 离线审计与原生复测 | runs/S01/final-review.md、runs/S03/validation.json |
| 云端部署与交付验证 | docs/CLOUD_DEPLOYMENT.md、runs/cloud/VERIFICATION_REPORT.md |

原 `skills/` 与 `evidence/` 文件是逐字节保留的基线。R06 当时待发布的方法使用 `runs/R06/candidate/C5/forge-agent-flow/SKILL.md`，固定文件哈希见同目录上一级 `C5-lock.json`；C2/C3/C4 及旧失败完整保留。自动注册为某个宿主的个人 skill，需要该宿主自己的安装机制。仓库不附带原宿主的凭据、插件会话或运行中 worker。

此快照未附新增开源许可。上传前可由仓库所有者选择适用许可；代码来源与快照哈希见 state/source-lock.json。
