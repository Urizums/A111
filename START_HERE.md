# 接续入口

本分支由仓库所有者接手。对方源提交 `6f509c8` 和全部旧失败已保留，PR #1 已关闭。
当前状态见 `state/checkpoint.json`；接手索引见 [docs/TAKEOVER.md](docs/TAKEOVER.md)。
关闭 PR 不表示长期目标完成。

R07 收集/修复批次已归档；R08-01 能力首步已实际执行。
当前首项为 R08-02：由 Root 制作短启动候选，再交新上下文 Luna 验证。
见 [R08 计划](runs/R08/PLAN.md)。R07 业务结果通过，但自主限时完成失败，后续不得改判。

1. 读 AGENTS.md、checkpoint、state/phase-todo.json。
2. 运行 `python3 scripts/coordinator_lease.py probe --root .`，仅空闲时持有租约。
   旧宿主 worker/PID/路径只作历史证据。
3. 运行 `python3 scripts/verify_handoff.py --json` 和
   `python3 scripts/continuation.py --root . next`，从同一台账接续。
4. 当前候选为 [C6](runs/R07/candidate/C6/forge-agent-flow/SKILL.md)，文件锁为
   runs/R07/candidate/C6-lock.json。C5/C4、原 skills、失败全部保留。
   普通任务直接做，系统用 program，明确可复用 flow 才用 package。
   Root 写核心/skill，Luna 做资料、脚手架和独立验证。
5. 新任务先保存原材料字节和真实首步，再用 continuation start/finish 绑定验收与证据。
   原八项阻塞保持原标准和已耗额度，不能清零换样本。
6. 阶段最后一项“启动下一阶段任务”需要下一计划和真实首步；会话结束保存
   checkpoint、未决调用和下一动作。停用定时器保持停用。

新结果见 runs/R07/REPORT.md，原交接见 runs/R06/upstream-handoff/README.md。
check_publication_gate.py 保留原完整产品门槛；单批开发保存不代表它已通过。
实际提交和发布状态以 GitHub 与本轮记录为准。
