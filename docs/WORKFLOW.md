# Skill 与研发工作流

## 任务分流

| 输入 | 执行方式 | 必要产物 |
| --- | --- | --- |
| 一次性抽取/总结/小修改 | 直接完成；按来源核验 | 结果与必要证据 |
| 完整应用/系统 | program/project 模式 | 可运行代码、分层设计、任务/案例、实际验收、交接 |
| agent infra | program 模式 + host/runtime 契约 | 状态、dispatch、receipt、资源与恢复、真实运行案例 |
| 明确要求可复用 agent flow | factory/package 模式 | 版本化输入输出、节点路由、错误恢复、包验收与复用案例 |
| 给定已有 package | 运行原包 | 不重建 factory；保持 invocation 与原验收 |
| UI/UX | 叠加 design-product-experience | 设计方向、参考/来源、布局/token、状态/motion、目标端交互验收 |

## 架构与设计

应用架构负责领域规则、权限、数据和业务边界；系统架构负责服务、部署、可用性、容量、运维与恢复；前端架构负责页面/路由/组件、状态与数据流、性能、错误和可访问性。产品体验贯穿这些层：视觉重心、分区、密度、色彩、寻找动作、导航退出、切换/加载和动效都必须对应使用场景及组件状态。

Root 根据目标形成最小可运行方案和验收；缺省行为写为可调整假设，真实审批规则和权限不凭空授予。Luna 可检索 Refero、Mobbin、Apple/Android 官方设计资料、Collect UI、Pageflows 或开源组件来源，整理出处、适用场景、交互状态、motion 和复用条款。只有截图并不等于可复用代码；来源未知不能假定许可。Root 决定哪些材料进入 skill 和预设。

## 从任务到证据

1. 核对当前源码/台账/真实能力，识别目标与未知项；简单任务直接走短路径。
2. 根据信息和风险推定可逆缺省，分阶段 TODO、依赖、写域和验收；不在每个阶段向用户询问继续。
3. 冻结本轮源码与案例；Root 实施，独立工作可交 Luna。独立验证者只拿原要求和原材料。
4. 本地 static/fixtures 验证后，用实际目标 runtime 运行相关案例。Host worker 链保留创建返回、accepted、running observe、completed receive、独立 review、decision preflight 和 commit/reconcile；只用当前公开接口。
5. 原始结果先留存，再修复；按候选预算继续。CLI 返回0、业务正确、协议合规、真实 UI、性能有效是不同结论。
6. 更新当前阶段和完整台账、checkpoint、证据引用。完成末项时实际启动下一阶段首项。

Host 的作用是调用原生工具并保存原件；本地 projectctl/factoryctl 不会凭状态文件自动创造 worker。字段校验不能代替业务审阅，写域声明不能代替 host allowlist。换宿主只迁移方法、源码和历史，不迁移旧活跃调用。

## 验证记录

每条要求附可复核的来源条款、实际证据、结果和局限。状态可区分 planned、static_checked、fixture_checked、runtime_checked、independently_checked；性能还需要可比条件与原始计时。缺失数据记 null，不猜 token/成本，不把 synthetic receipt 说成实际 native 返回。

关键源码入口：skills/forge-agent-flow/references/task-entry.md、system-architecture.md、project-execution.md、host-execution.md、host-resource-boundaries.md、host-observability.md、host-drafts.md、evaluation-plan.md；体验内容进入另一个 skill。先读 SKILL.md 并按需路由，避免每个任务背负整个资料集。

## 当前固定候选与发布约束

当前候选入口及哈希以 START_HERE.md 为准。C4/C5 分别将原字节丢失和修正次数漏记的反馈落实到 snapshot.py、bounded_run.py；原失败和新案例证据见 runs/R06/FEEDBACK_LOOPS.md。快照不能补回历史未保存的字节；本地 guard 不等于 provider 全局强制约束。

协调者先核对 lease 和原生未决状态，再串行整合共享台账。所有必需验收与最终候选冒烟通过之前，不提交或推送 dev。执行 check_publication_gate.py 并人工核对语义；该校验只检查本地证据完整性，不等于 GitHub 分支保护。
