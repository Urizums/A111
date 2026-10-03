# 云端接续、冒烟测试与修复验证报告

日期：2026-10-04（Asia/Shanghai）；原始命令时间保留 UTC。来源提交：
`550275d726485de6ad7ba49ae3b1231142edca04`。

## 交付范围与环境

代码在本次连接的云端环境 `/workspace/A111`，CLI 安装在
`/workspace/agent-forge-cloud`。该项目是 Python 控制器与技能研发包，无 Web
服务和公网 URL。部署不依赖用户电脑、第三方 Python 包或新增模型密钥。
Python 3.12.14 为主运行环境，另安装 Python 3.10.21 验证最低版本兼容性。
环境生命周期由宿主管理，不宣称永久后台调度或生产 SLA。

目标是完成 README 的近期接续：C1 离线收尾、C2 方法修订、真实 worker 烟测，
以及用户要求的云端安装、问题修复、代码/报告归档和 fork PR。长期 SDK、全局
资源、自然网络故障、外部业务效果、真实 UI 和性能实验有独立验收，不因本次
交付关闭。`skills/`、`evidence/`、原 source-lock 与历史失败字节保持不变。

## 实际验证结果

| 验证 | 结果 | 原始记录 |
| --- | --- | --- |
| 原控制器回归，Python 3.12 | 368 通过 | `baseline-regression.json` |
| C2 完整候选回归，Python 3.12 | 368 通过 | `../S02/candidate-regression.json` |
| 采集与交接辅助检查，Python 3.12 | 16 通过（原 8 项及新增 8 项） | `added-tests.json` |
| 原控制器回归，Python 3.10 | 368 通过 | `python310-regression.json` |
| 采集与交接辅助检查，Python 3.10 | 16 通过 | `python310-added-tests.json` |
| 安装后 CLI 冒烟 | 17 检查通过 | `smoke-revised/report.json` |
| 归档解压、换路径、无 Git 安装和运行 | 校验通过，17 检查通过 | `archive-integrity-fixed.json`、`archive-install-fixed.json`、`archive-smoke-fixed/report.json` |
| Python 3.10 安装后 CLI 冒烟 | 17 检查通过 | `python310-install-cli.json`、`python310-smoke/report.json` |
| C1 离线独立审计 | A01–A05 完成，Root 核对 336 个来源引用；保留历史缺口 | `../S01/final-review.json`、`../S01/cloud-audit/worker/report.md` |
| 新原生 worker 烟测及一次有界复测 | 两次业务结果均正确；首轮协调端采集不完整，修正后观察到的协议检查通过 | `../S03/validation.json` |

相同用例在多个解释器/候选上的运行是兼容性和回归重复，不累加成新业务样本。
C1 四份 package 原始闭环及业务行动与来源相符；B2 协调端三次分析修正超过
两次预算，另有两次 bridge 拒绝。八个样本的跨 boot、缺失 marker 和 wait 参数
缺口均保留，旧性能比较仍为 inconclusive。独立审计先冻结业务预期，但后续原
source-review 与 CLI 记录含旧结论，因此不声称全盲。审计中的公共来源路径映射
误判已修正，Root 逐条重核；原证据未修改。审计实际原生完成返回、receive、
Root decision preflight、commit 与 reconcile 已保存。

CLI 17 项检查涵盖安装完整性、帮助、未知命令拒绝、package 验证、启动、原
invocation 恢复、只读 next、过期 reply 拒绝且不改 state、无行动分支完成、
完成后读取复用、包内容漂移拒绝且不改 state。该部分使用明确的本地 fixture。

原生路径另有实际 `collaboration.spawn_agent` 返回、running/completed 快照、
原 bridge accepted/observe/receive、源数据复算、独立决策 preflight、commit
与 reconcile。请求设置为 Luna/max/fresh；这不证明内部 provider 身份。
两次均对同样的六行新 CSV 精确复算为 3630 分，退款和零金额 ID 均保留。
第一轮 11 个 worker targets；复测 13 个 worker targets、23 个协调端 targets。
复测 worker 自报一次 shell 启动前的 JavaScript 包装错误，Root 将重试计入
一次修正，而不是沿用 worker 的零修正计数。两次都保留，未替换 C1 旧样本。

## 问题、修复与复测

| ID | 原问题 | 修复及结果 |
| --- | --- | --- |
| ISSUE-001 | 命令不存在时记录器抛异常，不落盘失败记录 | 执行前独占占位，保留 started 状态，记录 OSError/127 及原始流；五项专项检查通过 |
| ISSUE-002 | 冒烟脚本从 CLI 摘要读取并不存在的 outputs 字段 | 改为验证真实 checkpoint 中的持久业务结果；17 项通过，产品行为未改 |
| ISSUE-003 | 推进 active phase 后，旧阶段转换被误判失败 | 按阶段 ID 解析归档 successor，验证阶段历史和候选哈希；错误复现与修复后检查均保留 |
| ISSUE-004 | 解压后的 delivery manifest 被误判为多余发布源码 | 将运输清单与发布清单区分；全包哈希仍由安装器校验；解压/异地安装与冒烟通过 |
| ISSUE-005 | 首轮协调端 source review 有未包裹的 shell 读取/写作，初始协议判定过强 | 保留原记录并明确改判；相同输入和验收下进行一次计入预算的协议复测，样本内协调端目标全部采集 |
| BLOCK-001 | 原仓库只读，目标分支和 fork 创建均被集成拒绝 | 用户建立 fork 后恢复；已验证 `waw1w1/A111` 可写并创建 `dev`，向原仓库 `main` 提 PR |

详细证据、首个失败和预算见 `issues.json`。记录器用一轮修复、交接验证器累计
两轮、CLI 测试脚本一轮、S03 协调端一轮；没有用新名称清空同一候选的预算。
首轮 S03 的完整采集失败不能追溯修复，后续通过只属于明确保留的复测。

## 验证边界与复现

Worker 读写与工具限制是指令约束；没有经验证的宿主 allowlist 或完整 worker
工具轨迹，不能据此声称安全隔离。阶段耗时包含工具、等待和协调端处理间隔，
不是模型活跃时间；token、成本及内部身份均为 null。本地时间和哈希不提供独立
授时或 provider 认证。C1 旧 A2 仍是原 cutoff 的未完成样本，未对旧 ID 发起调用。

S01 离线审计与独立的部署/C2/S03工作有时间重叠；最后才整合阶段台账。没有把
并行预备工作伪装成旧审计已完成，也不把旧性能比较改判为成功。

```bash
python3 scripts/verify_handoff.py --json
python3 -m unittest discover -s skills/forge-agent-flow/scripts -p 'test_*.py'
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/deploy_cloud.py --prefix /tmp/agent-forge-install
python3 scripts/smoke_cloud.py --prefix /tmp/agent-forge-install --out /tmp/agent-forge-smoke-new
python3 scripts/package_delivery.py --out /tmp/agent-forge.tar.gz
```

只运行新 state。不要把历史原生 worker ID、checkpoint 或绝对路径当作新环境的
执行配置。CI 工作流只运行本地回归与安装/打包测试，不重放真实 worker。
