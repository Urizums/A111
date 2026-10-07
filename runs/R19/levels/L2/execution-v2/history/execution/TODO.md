# 同一执行尝试终态台账

owner均为L2执行上下文，写域均execution/；所有done指实际作者执行/重算，不指独立外部验收。

| task_id | 依赖 | 状态 | 接收断言及证据 | 下一动作/限制 |
| --- | --- | --- | --- | --- |
| L2-E00 | 冻结设计 | done | preflight原raw/C11/design三锁hash一致、API实际调用；requirements | 未核实官方投稿规则，材料缺失保留 |
| L2-E01 | E00 | done | 从PDF/DOCX/XLSX原件抽取，5类3000件、两车单位一致；data/ | 附2缺重量/数量/类别/载重，仅资格审计 |
| L2-E02 | E01 | done | 统一几何、接触并集、局部重心、累计压力；validate.py、16真实边界 | 作者不同实现，不是独立上下文 |
| L2-E03 | E02 | done | 15件五类原子集到布局/指标真实smoke；CLI非法返回2 | smoke不是全量质量通过 |
| L2-E04 | E03 | done | 四全运基线+两车型单车，所有ID/布局检查；results/main与final/baseline | 基线可行上界 |
| L2-E05 | E04 | done | 易碎地板瓶颈→标准网格平台、213模式MILP；results/improved、final/selected | 库内最优，原问题未证最优，保留界差距 |
| L2-E06 | E05 | done | 原32参数终态，严格地板同高1例、seed3例前瞻扩展，36例35合法1失败；experiments | 合成规模与参数，不是附2真实通用验收 |
| L2-E07 | E04-E06 | done | 完整中文论文/企业报告/6图、PDF实际渲染逐页查看；paper与report | 正式投稿版式/AI规则未知 |
| L2-E08 | E07 | done_self_checked_ready_for_external_review | 从源重算7最终方案与界，干净3000件复跑指标/坐标/代码身份一致、算法ZIP解压smoke；checks | 外部首审未开始，不伪造独立接受 |
| L2-E09 启动下一阶段任务 | E08 | cancelled_in_executor_scope | 原题研究交付达到终态，不创造无意义执行阶段；交物流root冻结首审 | 外部审查由root后续启动，不声称本executor已启动 |

## 不重置的失败/恢复与资源

原设计两次工具构造失败留在不可变design。执行事件：观察输出截断；一次numpy导入误缩进（运行前读回发现）；一次补丁上下文拒绝，之后单hunk修复；低质量竖列结果保留，平台为研究迭代；账号/会话中断后旧session未知，进程核查无本任务，原13完成案例保存并checkpoint续跑；极端车高10%真实失败保留。PDF首次页末标题孤立，修复keepWithNext；长表随后分段，重新渲染逐页复查。日志failure_history.md及原stdout完整保留。

实验主参数32例→严格解释1例→种子3例为前瞻研究扩展，不抹除原失败、计数或时限。MILP8/60秒只约束求解，不含模式生成/检查；总耗时真实保留。没有任务总截止或通用两轮纠错上限。model/token/cost均null。终态前所有本任务Python子进程须实际结束；以result.json与日志记录。
