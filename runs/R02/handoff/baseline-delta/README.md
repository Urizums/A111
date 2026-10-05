# Agent Forge：可接续研发工作包

目标：让 agent 从自然语言需求完成软件或 agent flow 的设计、实现、验收和后续迭代，并把进度留在仓库中。这个仓库包含当前 skill 源码、项目历史、下一阶段任务、接续提示词，以及最近一次实验的原始截止证据。

**新 agent 从 [START_HERE.md](START_HERE.md) 开始。** 不需要原聊天记录，也不需要原机器上的个人 skill 路径。长期目标保持 active；前次 D00 已交付，当前继续处理 PR 审阅要求。双队列及真实证据见 [接续状态](state/continuation.json)，当前阶段见 [checkpoint](state/checkpoint.json)。

当前已具备任务分流、分层架构方法、独立产品体验 skill、本地 project/package 控制器、host bridge/driver、审阅与有界恢复。Python 3.10/3.12 原控制器回归各 368 项、辅助检查各 16 项通过，安装后的 CLI 冒烟 17 项通过。C1 八个旧样本的性能比较仍为 inconclusive；SDK、全局资源保证、自然网络故障、外部业务效果和真实 UI 验收保持独立未完成状态。

本项目提供 CLI 与研发工作包，没有 Web 服务。云端安装路径为 `/workspace/agent-forge-cloud`，生命周期由当前宿主管理。完整结果见 [验证报告](runs/cloud/VERIFICATION_REPORT.md) 和 [问题及修复记录](runs/cloud/issues.json)。

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

完整性检查不会执行旧 host 状态；本地回归和 CLI 冒烟不能替代真实 worker、浏览器或 provider 测试。运行要求为 Python 3.10+，仅使用标准库。安装、搬迁、打包方法见 [云端部署说明](docs/CLOUD_DEPLOYMENT.md)。

把 [prompts/CONTINUE_IN_WORK.md](prompts/CONTINUE_IN_WORK.md) 发给能够读取并写入本仓库的 agent。需要通用持续迭代行为时，使用 [prompts/CONTINUOUS_ITERATION.md](prompts/CONTINUOUS_ITERATION.md)。宿主是否支持原生子 agent、Luna、浏览器或持久后台执行，需要现场核实。提示词不能自行提供这些能力。

## GitHub 托管与复用

上游仓库为 [Urizums/A111](https://github.com/Urizums/A111)。本次已按用户指令提交到 [waw1w1/A111 的 dev 分支](https://github.com/waw1w1/A111/tree/dev)，并创建 [上游 PR #1](https://github.com/Urizums/A111/pull/1)，目标为 `main`，未合并。此前发布记录 `state/github-publication.json` 属于原始交接历史；本次记录保存在 `runs/cloud/`。仓库当前访问权限以 GitHub 为准，原快照的私有描述不代表当前可见性。

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
| C3 持续研发候选 | runs/R01/candidate/forge-agent-flow |
| 能力 / 挑战双队列 | state/continuation.json |
| 离线审计与原生复测 | runs/S01/final-review.md、runs/S03/validation.json |
| 云端部署与交付验证 | docs/CLOUD_DEPLOYMENT.md、runs/cloud/VERIFICATION_REPORT.md |

原 `skills/` 与 `evidence/` 文件是逐字节保留的基线。当前方法使用 `runs/R01/candidate/forge-agent-flow/SKILL.md`（C3）；C2 及旧失败完整保留。自动注册为某个宿主的个人 skill，需要该宿主自己的安装机制。仓库不附带原宿主的凭据、插件会话或运行中 worker。

此快照未附新增开源许可。上传前可由仓库所有者选择适用许可；代码来源与快照哈希见 state/source-lock.json。
