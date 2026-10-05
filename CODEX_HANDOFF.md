# Codex 当前研发交接

从 `Urizums/A111:main` 接续。用户授权持续研发、上传开发成果，不等待 ZCode。
先读 AGENTS.md、START_HERE.md、state/continuation.json、state/checkpoint.json。

2026-10-05 本次 desktop 工作保存 C7 短入口并冻结锁：
`runs/R08/candidate/C7-lock.json`。C6 保持原字节；入口 17498→7139 字节，
376 条继承回归通过。字节缩减不证明速度、性能或泛化改善。

R08-03 已从两个新 Luna/max 上下文实际执行冻结要求。
simple 对账内容和源数据检查通过；首业务文件约 195.194 秒（含工具往返与失败）。
complex 只有读取和 CLI 帮助记录，未写业务源码、未创建 reviewer、无业务后继首步。
其读域偏差及三次修正超过两次上限均保留：
`runs/R08/validation/complex-terminal.json`、`root-repair-ledger.json`。
这项保持 blocked，禁止转给新 worker、换样本或清零预算刷通过。
R08-next 保持 blocked；没有通过 continuation advance 归档 R08。

不同来源的 R09 环境诊断支线已实际启动并完成 R09-01，
不是重开 complex 样本。正式首步：`runs/R09/preflight/formal-first-step.json`。
只读 host_preflight.py 在 Windows 和 Ubuntu WSL 各通过 6 项相关检查，
原生 Windows 明确报告不兼容，WSL 核对冻结字节后可执行原控制器。
本次没有移植 Windows 控制器或证明恢复发布、provider、UI 或崩溃耐久。
支线依据见 runs/R09/PLAN_ADDENDUM.md；下一实际可执行项 **R09-02**，
从已发布提交的新 checkout 做独立验证，保留原验收与每 actor 两次预算。

原全部旧锁、历史失败和预算未改变；本轮原始 Git 基线为
`83f21cadfe895cbfd3d03075ba012359f670bb7a`，不是早期 PR#2 的旧基线。
审计核对 3811 个继承文件及29个原任务；9个原 blocked 包含旧八项与延期 ZCode。
PR#1 已关闭、原源提交保留；PR#2 已合并。完整产品门槛仍未通过。

当前无未决原生 worker，定时器未开启。原历史未决调用单独保留，不能复用旧 PID。
先运行 host_preflight、verify_handoff 和 continuation next，核对当前租约再持有；
当前 CLI 使用 Python3/Linux，Windows 本机用实际可用 WSL 并替换为当前 checkout 路径。
不存在 provider token/cost 数据时写 null。共享源码、TODO/checkpoint 由协调者串行整合。
报告与恢复动作见 runs/R08/REPORT.md；原交接字节在 runs/R08/design/entry-before/。
结束前提交原始证据、TODO/checkpoint，上传授权开发成果并释放租约。
