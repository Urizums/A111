# Codex 接续入口

用户已决定从 GitHub `main` 改用 Codex 继续研发。
首先读 [CODEX_HANDOFF.md](CODEX_HANDOFF.md) 和 [AGENTS.md](AGENTS.md)，再从原台账执行。
ZCode 连接是延期支线，不阻塞当前主线，也不要求你配置或调用它。

当前首项是 **R08-02：制作分流与最小真实首步的短启动候选**。
随后 R08-03 做新上下文验证；阶段末项“启动下一阶段任务”需要下一阶段的真实首步。
状态入口是 state/checkpoint.json、state/phase-todo.json 和 state/continuation.json。

```sh
python3 scripts/coordinator_lease.py probe --root .
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
```

确认租约空闲并核对未决原生调用后，持有租约再串行更新台账。
旧宿主 worker/PID/绝对路径仅作历史；使用当前 checkout 的相对路径。
定时器保持停用，会话结束保存 checkpoint，不宣称后台自动继续。

当前候选是 [C6](runs/R07/candidate/C6/forge-agent-flow/SKILL.md)，锁为
runs/R07/candidate/C6-lock.json。新 C7 写 runs/R08/candidate/，保存旧版和全部失败。
需要产品界面时按需读 skills/design-product-experience；简单任务直接做，系统用 program，
明确可复用 flow 才用 package。原 skills、source-lock、失败验收和已耗预算不改写。

历史索引见 [接手记录](docs/TAKEOVER.md)、[R07 结果](runs/R07/REPORT.md) 和
[R08 计划](runs/R08/PLAN.md)。R07 业务内容通过，但自主限时完成失败；原八项阻塞仍保留。
本次 Codex 角色与延期支线调整见 [R08 补充](runs/R08/codex-handoff/PLAN_ADDENDUM.md)，原计划证据保持原字节。
check_publication_gate.py 保留完整产品门槛，本次开发成果合并不代表完整验收通过。
