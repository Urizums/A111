# v2 实际事件账（不清零旧历史）
原作者失败完整冻结在 ../execution/logs/failure_history.md，hash见 research/prior-lock.json；初审历史保留在原首审，不复制伪造重演。

1. 工具/物流恢复：读取误用 runs/R19/QUALITY_FOLLOWUP.md，GetContent路径不存在exit1。root随后明确同层 levels/L2/QUALITY_FOLLOWUP.md，实际读取成功。未枚举根域。
2. 观察输出容量：初读350文件initial锁连同result造成显示截断。随后定向完整读取report/result及锁头/计数；未因显示截断重复求解。
研究调用结果（包括失败）随后写各原始receipt及研究表，不删除。

3. 观察输出容量：一次读取自有构建脚本、文件清单及口径同批结果显示截断。后续只提取需要的代码段作为文本，不为截断重跑求解。

4. 实质选择质量缺陷：原A19费用限时10200高于已知车数候选9800；原C19混合13車高于已知单车型12车、费用8050高于已知7850。全部原run/receipt保留。修正对所有方法统一比较完整合法候选，重新生成未保存的完整构造车队并断言模式库一致，另计实际追加成本；不重跑原MILP、不追认限时Optimal。

5. 遥测持久化增强：参数18前后给main.solve增加块证书落盘语句。参数入口调用library/select而非solve，搜索路径/数据/结果不改变，各真实receipt仍记录其启动代码hash。所有36参数块证书另由审计按同配置确定性重建，明确标注post-run，非追认原进程日志。fragile_floor缓存键另补该布尔，防止同进程切换口径误取模板，未改变非地板主比较。

6. 实质跨目标候选保护缺陷：第一当前代码raw复跑114.4569秒全布局合法，但混合车数select将raw13车换成已知12辆V2时，没有把raw留下供费用目标；费用主答案8050元劣于本尝试已知7850元。整个114秒调用/代码/结果保留（research/clean_replay_package、guard_correction_1_result）。修正select把原始可行incumbent保留在共享known池，再按各目标选择；参数每例仅一次select，局部已比较raw，其数值不受新增side effect影响，因此不重跑36。另前瞻声明300秒主raw复跑。
