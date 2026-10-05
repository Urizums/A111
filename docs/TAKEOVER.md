# 由所有者接手续研

原 PR：https://github.com/Urizums/A111/pull/1 。所有者按本轮指令关闭它，源代码完整保留在
`Urizums/A111:rd/takeover-r07`，基准提交为 `6f509c8dcb54f7864a49864e21061345dc4b2b9c`。
本轮原字节与授权范围见 `runs/R07/intake/provenance.json`。

## 成果入口

| 内容 | 入口 | 证据范围 |
| --- | --- | --- |
| 能力与待办索引 | `runs/R07/inventory/INVENTORY.md` / `inventory.json` | 来源整理，不是重新验收 |
| 原控制器与设计 skill | `skills/` | 不可变基线 |
| 原版本 C3/C4/C5 | `runs/R01/candidate/`、`runs/R06/candidate/` | 原快照、预算与失败保留 |
| 当前 C6 | `runs/R07/candidate/C6/forge-agent-flow/` | 快照恢复与跨宿主指引，按本轮结果判定 |
| 应用与 flow 挑战 | `challenges/`、`runs/future/`、`runs/R06/handoff/` | 本地业务与原运行记录 |
| 本轮结果 | `runs/R07/REPORT.md` | 新任务与旧验收分开 |
| 当前执行状态 | `state/continuation.json`、`checkpoint.json` | 同一长期目标、原历史及新任务 |

## 接续原则

原八项 blocked 不清零、不换样本刷通过。真实 provider、取消终态和全局观测需对应
服务；独立 UI、协议实验和超限需处理原验收记录与实验处置。新增快照缺陷可以
本地修复；具备原生子 agent 工具的宿主可以验证任务组织。各层证据分别判断。

旧 R05 留存于 `state/history/R05-todo.json`，没有伪造阶段完成。R07 按用户接手授权
增加新缺陷修复与新业务挑战，继续同一台账；它不是旧失败重跑。R07 后继首项必须
有真实启动证据，长期目标保持 active。

## 常用命令

```sh
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
python3 -m unittest discover -s runs/R07/validation -p 'test_snapshot_restore.py'
python3 -m unittest discover -s runs/R07/candidate/C6/forge-agent-flow/scripts -p 'test_*.py'
python3 scripts/check_publication_gate.py --root .
```

完整产品门槛保留原失败；本轮保存的是有明确范围的开发成果。停用调度保持停用，
历史 worker ID 不在新宿主重派。C6 发布后端为 Linux renameat2，能力不满足时明确
拒绝；没有声明跨平台测试、断电耐久、生产托管或性能改善。
