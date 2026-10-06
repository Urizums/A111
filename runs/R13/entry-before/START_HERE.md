# Codex 接续入口

当前用户定位为 Forge meta-workflow。C8 是纯方法开发候选：
[技能入口](runs/R10/candidate/C8/forge-agent-flow/SKILL.md)、
[五文件独立包](runs/R11/package/Forge-C8-meta-workflow.zip)、
[研发报告](runs/R10/REPORT.md)。包内不含脚本、测试或执行器。

先读 AGENTS.md、CODEX_HANDOFF.md 和 state/checkpoint.json；state/continuation.json 保存完整任务历史。
R10-01 源码/结构通过；R09-02 新checkout独立核验完成；R11-01 实际独立包装与解包完成。
R10-02 同一actor接续后累计3次纠正超过2次预算，三份业务草稿未完成原材料检查，保持blocked。
R10-next、依赖已验收批次的R11-02/R11-next保持blocked，不换样本或worker刷通过。
R08-03/R08-next、旧产品门槛、失败和预算仍保留；R08没有归档为通过。

```sh
python3 scripts/host_preflight.py --root . --lock state/source-lock.json --lock runs/R10/candidate/C8-lock.json
python3 scripts/coordinator_lease.py probe --root .
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
```

以上是研发恢复工具，不是C8运行依赖。原生Windows控制器仍不兼容，实际用Linux/WSL。
新clone保留core.autocrlf=false，避免冻结字节改变；先核对真实租约与未决调用再写共享台账，不复用旧PID。
旧入口字节在 runs/R10/resumption/entry-before/，更早备份也保留。定时器停用，未知token/cost为null。
C8未安装个人skill，没有独立行为或完整产品通过结论。
