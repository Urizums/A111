# C1 离线审计最终整合

本次完成冻结的 A01–A05 离线审计；历史 C1 性能结论仍为
**partial / inconclusive**。审计完成表示已检查并列明缺口，不表示旧实验全部通过。
原 `evidence/c1/` 的 375 个截止文件均保持原字节，没有重新调用旧 worker。

独立审计见 [worker/report.md](cloud-audit/worker/report.md) 与
[worker/audit.json](cloud-audit/worker/audit.json)；Root 的来源核对及哈希绑定见
[final-review.json](final-review.json)，复核脚本为 `review_audit.py`。

- A01：四个 package 样本各有独立的 receive、源数据审阅、decision preflight、
  commit 和 reconcile 原始记录。Root 核对原控制器绑定的材料、receipt 与产物哈希。
  `controller_compatible` 只证明协议预检查，不被当成业务验收。
- A02：验证者先从原会议记录与原 package 规则保存三条预期行动，再查看四份产物。
  Root 另核对赵宁/周五、许静/2026-10-09 及日志告警的 null 字段和逐字引文。
  四份 CSV 的分组金额与全部 ID 也通过独立 Decimal/整数分复算；A2 保存的输出
  正确仍不代表其原生流程完成。
- A03：B2 worker 保留记录内的业务/reply 修正为 0；协调端分析/索引至少有
  3 次修正，超过冻结的 2 次预算。两次被拒绝的 bridge 操作另行保留；采用包含
  这些错误的宽口径时至少 5 次。控制器内部 `repair_attempts: 0` 不能代替总分母。
- A04：八个样本全部保留，跨 boot、重复及缺少 marker、原始 wait 返回或参数
  缺失均保持缺失。Project/A2 第五次查询仍 running，非原子 cutoff 不证明最终状态。
- A05：只按原 C01–C10 给出 pass/partial/unknown。C07 的 pass 指失败保留和
  不替换样本，**不代表修正预算合规**。C10 历史 TODO 超出独立验证者输入范围，
  由 Root 对照 `state/history/project-todo-before-cloud.json` 保留原三个 partial、
  browser blocker 和其他历史身份；不是独立验证者已完成 C10 的声明。

验证者在产物预期冻结后检查原 source-review 及含旧索引结论的 CLI stdout，
因此独立来源复算成立，但不能声称全盲。初版分析将公共材料的历史绝对路径按
样本子目录查找，产生假阴性的引用匹配；已按保存的路径映射检查原 SHA，Root
再次逐条核对。这是本次审计代码的修正，不是对历史证据或历史失败的修复。

描述性耗时只统计有效的同 boot 阶段跨度，包含工具、等待与协调间隔，部分组
样本数不足二；不作提速或因果结论。token、成本、内部 provider 身份及模型活跃
时间未知。后续 C2/S03 是独立版本与新运行，不能追溯补齐 C1。新研究应另行冻结，
本次用户要求的云端交付完成后不自动启动性能实验。
