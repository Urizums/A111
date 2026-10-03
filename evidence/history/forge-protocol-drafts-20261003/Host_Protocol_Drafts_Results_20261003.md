# Agent Forge 协议草稿与预检查：T1 已验证

本轮已加入 reply／decision 草稿和只读预检查，减少手写身份、SHA 与验收框架的工作。草稿始终保留未定 outcome；项目验收状态始终从 `not_run` 开始，已有 package 的内层响应由原控制器验证。Root 负责设计、实现和最终判定，Luna 负责来源材料、实际任务执行和独立审计。规范及代码已保存为 `c238b00`，实测期间冻结的七个修改文件与完整 83 文件清单一致。

| 验证 | 结果与范围 |
| --- | --- |
| 回归 | 368 项通过：原有 348 项加 20 项交互边界测试；skill 格式检查通过 |
| 实际 project 任务 | 新 Luna/max/fresh worker 汇总 6 行费用：design 1600 分、dev 946 分、ops 1464 分，合计 4010 分，全部 ID 正确；Root 从原 CSV 独立复算，原 project checkpoint completed |
| 已有 package 执行 | 另一个新 Luna worker 使用未改的 `forge-package/1`，提取 3 项明确行动，保留相对日期和 null 字段，排除配色建议；原 quotes/commitments 检查通过，原 package 单步 completed |
| 独立审计 | 两组共 31 条 CLI，本地 synthetic fixtures，覆盖身份／写域、未完成草稿、验收锁、内外协议分层及只读状态；所测行为未发现必修缺陷 |
| 原件复核 | Root 校验实际 artifact、decision、捕获回复和 bound refs 的 SHA，核验 CLI 索引及审计快照；保留原始输入、错误和回执 |

两个业务任务各创建一次实际 worker、查询一次自己的子树，共 2 spawn、2 query、0 interrupt；完成通知等待另计。材料、审计及 Root 的管理调用不在业务调用分母内。协调者记录了 38 条 CLI，其中 9 条调用草稿／预检查入口，4 条非零退出。子进程记录的 monotonic elapsed 合计约 2.47 秒，不能代表整轮时长或模型活跃时长。ledger 的请求导入到完成观察间隔分别为 105 秒和 47 秒，也不能代表 provider 运行时间。tokens、cost 未获得 telemetry，均为 null。

这轮实际执行包含修正：首次 driver 的 reply 路径在分配写域外，被拒绝后尚无 native claim；保留旧 driver，在同一个未开始的 project checkpoint 上换成正确配置的原 bridge 执行。随后一次草稿输出写域错误和一次对 completed 状态使用 observe 也被拒绝，分别修正路径、复用原完成回执调用 receive。派生的失败 driver 状态查询也保留。旧 driver 仍是未使用记录，不能算 driver 成功运行。Root 的流程提醒被披露，本轮不算无协助执行。

实际 coordinator 的 reply 预检查在 receive 后执行；worker 在报告完成前是否执行了预检查，没有独立捕获。这轮因此证明的是草稿辅助与原 receive／review／commit 的兼容性，不能据此声称完整执行顺序已经测全。实际 package 没有冻结 case 输入，这次新输入验收也不覆盖未执行的无行动分支。审计未抽测的边界由对应单元测试补充，不把 fixtures 算成实际 host 事件。

实现本身在冻结后的功能修复数为 0，预算为 2。另行保留一次 Root 单元 fixture 路径冲突修正、一次 Root 捕获比较误将新草稿当状态变化的修正，以及 Luna 审计的字段／快照路径标注纠正；这些都不改运行时代码。原 O3 的两次修复历史和证据缺口继续保留。

下一轮计划用同一候选、原材料和验收做手工构造／草稿辅助配对比较，分 project 与 package 共八个实际 worker，完整记录失败、协助、阶段观察跨度和调用。当前没有完成这个对照，尚无提速结论。若初始化 work／driver 占主要工作量，再由 Root 设计最小启动辅助。简单一次性任务继续直接完成；现有两项浏览器验收 blocker、provider SDK、全局资源与外部效果恢复的未完成项保持原状态。

使用说明、冻结要求、下一轮方法和全部原始证据已保存。项目 TODO 沿用原文件身份与历史，草稿辅助项完成，新增工作量对照项等待下一轮执行。
