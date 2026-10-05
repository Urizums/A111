# Codex 接续入口

继续 GitHub `Urizums/A111:main`，先读 CODEX_HANDOFF.md、AGENTS.md 和当前台账。
状态以 state/continuation.json 为准；state/checkpoint.json 是恢复点。

R08-02 已完成 C7 短入口，376 条继承回归通过。
R08-03 的简单新上下文样本通过；complex 样本因三次修正超过两次上限且无业务产物，
保留失败 blocked。R08-next 仍 blocked，R08 未归档为通过。
独立可做的 R09-01 宿主预检已实际运行并完成；下一可执行项 **R09-02**。
见 [本轮报告](runs/R08/REPORT.md)、[R09计划](runs/R09/PLAN.md) 与
[支线决定](runs/R09/PLAN_ADDENDUM.md)。不能换 worker 重跑耗尽的 complex 样本。

```sh
python3 scripts/host_preflight.py --root . --lock state/source-lock.json --lock runs/R08/candidate/C7-lock.json
python3 scripts/coordinator_lease.py probe --root .
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
```

Windows 原生 continuation/安全 POSIX 文件打开/计时 API 未支持；本次实际用 Ubuntu WSL。
按当前 checkout 的路径运行，先核对未决调用、再持有真实租约。Git 新 clone 使用
`git -c core.autocrlf=false clone`，避免自动转换破坏冻结字节；不要更改历史锁接受漂移。
原始入口字节保存于 runs/R08/design/entry-before/。
定时器保持停用，旧八项阻塞、ZCode 延期、原失败和已耗预算均保留；
没有完整产品发布或性能/泛化通过结论。C7 仍是仓库候选，未安装到个人 skill。
