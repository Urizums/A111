# Agent Forge 本轮研发与验证结果

执行概览、按原 run 的有界续跑、错误本地验收回执的显式恢复已完成并保存。当前候选 O3 的 80 个已保存文件与验证版本一致；348 项回归检查通过，其中新增 20 项覆盖只读状态、事务恢复、身份守卫、预算及验收恢复边界。

现在可以用 `inspect` 查看原 run、当前动作、下一步、剩余额度、本地容量与截止状态；它不创建任务、不发放调用许可、不回放事务。`resume --expect-run` 在原配置、原 attempt 和原预算内推进一次。`retry-review` 只允许保留并拒绝确定无效且尚未提交的本地验收回执，之后仍需独立核验实际原材料；有效回执、未知 IO、native 动作、已提交验收和待恢复事务均被拒绝。

Root 负责设计、核心修改与最终判定；Luna 负责实际普通任务、材料整理和独立 CLI 验证。新父线程与 worker 请求均为 Luna / max / fresh。新一轮两项任务都按原 run 和 attempt 经 source review 完成，未修正协议、重试创建或中断：

| 任务 | Root 独立复算结果 | 实际 native 调用 | 原 checkpoint |
| --- | --- | --- | --- |
| events 按团队汇总 | design：1 条 / 16 分钟；dev：2 条 / 19 分钟；ops：2 条 / 17 分钟，全部 ID 正确 | 1 次创建、2 次查询 | completed |
| measurements 秒转毫秒 | `[80, 1125, 3600, 9]`，合计 4814 毫秒，中文说明正确 | 1 次创建、1 次查询 | completed |

每项最初两次 inspect 的 driver、checkpoint 与 registry 字节均未变化。真实 completed 回执在本地截止之后被观察到，仍按原 source review 接受；这说明 observe 行为正确，不代表自然网络迟到。共享 registry 最终 held=0。

本轮另有一次真实 running → native interrupt → command 返回仍非终态 → 实际 interrupted 的控制验证，以及两项 baseline 数据任务。当前可复核业务证据合计 5 个 worker、15 次 native 调用（5 次创建、9 次查询、1 次中断）、4 次成功源验收提交。5 次 review claim 中有一次错误提交被保留；父线程管理调用、通知等待和合成 fixture 不计入业务 native 调用。

Baseline 保留了真实问题：readings worker 回复多了不支持的 invocation_id，父线程只移除该字段并记录协助；tickets 第一次 source-review 的 SHA 写错，bridge 拒绝后私有回执锁定。Root 在原 attempt 中用明确恢复入口保留旧错误回执，新增一次独立验收完成提交，没有新增 native 调用。该 baseline 不算无协助通过。

两轮功能修补已用完并完整保留。第一轮解决确定无效、未提交的本地 review 无法纠正；第二轮解决被包装的缺失证据 IO 错误必须保持 unavailable，不能误判为可丢弃的 invalid。旧候选、实际失败和反例都在证据包中；本轮结束后不继续混入新功能。

独立资源审计保存了 40 项 CLI 捕获；概览审计的两次运行各有 55 项完整命令捕获，覆盖五组抽样场景。它们使用合成 host 回执，不计为真实 worker。概览原始索引分别只有 49 和 47 行，原因尚未确定；原索引保持原样，单独生成的索引已与每项 argv、stdout、stderr 和退出码核对。Root 按 O01–O09 整合独立抽样、单元/故障 fixture 与实际任务；时钟异常和 pending journal 等条款依赖明确标识的 fixture，并未宣称全部由独立实测覆盖。

上轮 R2 的临时原始证据目录没有恢复。原有 9 个 worker、27 次 native 调用、7 次验收只保留为历史摘要，未计入本轮证据。已保存 skill 和当前新证据均已重新核对。原 TODO 的 41 个任务、历史、目标与两个 UI/browser blocker 保留，追加 2 个本轮完成项和 1 个下一轮计划项，共 44 项；provider 执行、全局限额、自然网络事件与外部业务幂等性继续保持未完成范围。

下一轮优先实现 host reply / decision 草稿：复制原请求身份、计算真实文件哈希、生成待填写验收框架，复用现有 validator；业务结果与通过结论由实际执行和独立验收提供。随后再用相同材料与边界测量准备、执行、验收、恢复开销。本轮没有证明速度提升，token/成本仍为 null。设计 preset 整理可以并行，实际界面与动效验收保留原浏览器依赖。

使用步骤见 Forge_Continuation_Runbook_20261003.md；冻结条款、Root 验证映射、源版本哈希和完整本轮捕获分别保存在配套 verification、source 与 evidence 文件中。
