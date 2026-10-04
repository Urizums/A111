# 同一目标的恢复条件

当前代码宿主实际可执行。所有本批就绪工作及云安装/归档冒烟已结束；队列为 12 done、8 blocked，长期目标 active。无新 commit 或 dev push。完整证据索引见 VERIFICATION_REPORT.md、final/summary.json、issues.json；发布门槛仍拒绝。

恢复时先通过 GitHub 读取 dev 的入口与最新审阅，随后核对云端 `/workspace/A111` 的未发布 checkpoint。远端仍是 e3f3d97；不得用远端旧状态覆盖云端 R05/R06 成果。若本工作区丢失，从本轮审阅包恢复候选源码与随附的最新 state 覆盖层，核对各 manifest；不要执行任何历史 worker ID 或把旧绝对路径当作活任务。

先探测 coordinator lease；有真实持锁者或创建结果未知时只核对等待，不另建 Root/worker。元数据中的旧 PID 不是跨宿主证明，文件锁必须在实际当前 checkout 检查。当前已完成的所有新 worker 均有终态；原预设 `/root/luna_forge_ec0ef35b347f` 只有保留的终态通知和随后空状态查询，原 bridge 的终态对账仍未完成，不能补造回执或重派同一任务。

| 分支 | 能恢复的具体条件 | 仍保留的限制 |
| --- | --- | --- |
| provider SDK | 在环境/连接设置配置有权使用的服务端点、模型、身份/凭据，再读取实际 readiness | 不在聊天中传密钥；模型原生协作不是独立 SDK 证明 |
| provider 故障/资源 | 有真实取消终态、usage/admission 观测契约和获准的故障/外部效果测试环境 | 本地进程 crash、cancel intent、null tokens 不能替代这些观测 |
| 独立 UI / adapter / 协议实验 | 必须先解决原验收分支耗尽预算及缺失回执的处置；当前不能自动重试 | 禁止换人、换样本、换判定或重置预算；Root 补查保持单列 |
| 真正跨会话 | 当前 Root 退出后，已有调度产生新的真实触发；新执行者能读写同一状态并持有空闲租约 | 记录实际 commit、checkpoint 字节、能力、选择、命令、状态变更与后继首步；只读检查不等于完成实质后继任务 |

只有条件实际变化才将相应 blocked 项恢复到 planned，并在原 task 中追加条件变化事件/证据，保留原 attempts、输入、验收和 repair counters，再用原 continuation start/finish 协议执行。不能把耗尽修复预算的原项改成 planned 来绕过限制。没有满足条件的新 ready 项时仅保存实际观察，状态不变保持安静；不要为“持续”造无意义的新任务。

下一真实调度复用 ID `6ac1e1f6159081919cd571f6fa15d397`。2026-10-04 06:16 的触发只证明活动 Root 内接续与代码执行，未证明独立冷启动。没有更多代码执行宿主时，只记录不可执行条件，不假称测试或持续后台研发。PR 随 dev 更新，但这次无权在必需阻塞仍存在时推送，也不合并上游。
