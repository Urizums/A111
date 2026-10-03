# Agent Forge：可接续研发工作包

目标：让 agent 从自然语言需求完成软件或 agent flow 的设计、实现、验收和后续迭代，并把进度留在仓库中。这个仓库包含当前 skill 源码、项目历史、下一阶段任务、接续提示词，以及最近一次实验的原始截止证据。

**新 agent 从 [START_HERE.md](START_HERE.md) 开始。** 不需要原聊天记录，也不需要原机器上的个人 skill 路径。当前的下一项工作是完成 C1 的离线审计；不是重跑八个旧 worker。

当前已具备任务分流、分层架构方法、独立产品体验 skill、本地 project/package 控制器、host bridge/driver、审阅与有界恢复。T1 历史回归为 368 项；实际 host 路径已有运行证据。C1 调用了八个真实 Luna，七个原流程提交，一个截止时未完成；采集和协议缺陷使性能对比不成立。SDK、全局资源保证、自然网络故障、外部业务效果和真实 UI 验收仍有未完成项。

## 使用

```bash
python3 scripts/verify_handoff.py
python3 -m unittest discover -s skills/forge-agent-flow/scripts -p 'test_*.py'
```

第一个命令检查交接完整性，不会执行旧 host 状态；第二个命令运行本地回归，不能替代真实 worker、浏览器或 provider 测试。运行要求为 Python 3.10+，回归运行过的具体环境记录在 validation 中。

把 [prompts/CONTINUE_IN_WORK.md](prompts/CONTINUE_IN_WORK.md) 发给能够读取并写入本仓库的 agent。需要通用持续迭代行为时，使用 [prompts/CONTINUOUS_ITERATION.md](prompts/CONTINUOUS_ITERATION.md)。宿主是否支持原生子 agent、Luna、浏览器或持久后台执行，需要现场核实。提示词不能自行提供这些能力。

## 上传 GitHub

解压交接包，在 GitHub 创建空仓库，再在本目录执行：

```bash
git init
git add .
git commit -m "Add Agent Forge continuation workspace"
git branch -M main
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```

若使用提供的 git bundle，可先 `git clone agent-forge-handoff.bundle agent-forge-handoff`，然后将 origin 改成自己的仓库。这里没有替你创建或发布 GitHub 仓库。

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

skill 文件是已保存版本的逐字节导出。读取这些文件即可遵循其方法；自动注册为某个宿主的个人 skill，需要该宿主自己的安装机制。仓库不附带原宿主的凭据、插件会话或运行中 worker。

此快照未附新增开源许可。上传前可由仓库所有者选择适用许可；代码来源与快照哈希见 state/source-lock.json。
