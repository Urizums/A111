# 输入、时间与产物接口

所有时间为北京时间。当前实例 O=2026-09-30 18:00，H=10月1–14日；一次性发布14天计划，不每日补入新信息。索引为(d,s,k)，12店×8商品×14天=1344组合，每日96组合。需求/备货为件；c、a、b分别为元/件采购成本、缺货、浪费损失。采购只占预算。

## 快照函数必须有两个目的

`build_snapshot(origin, inputs, policy)`产生原点可用训练标签及当时可知特征；`build_evaluation_labels(target_dates, label_cutoff)`只供评价。禁止两个用途共用无原点全表。

1. 需求表原行保留；完全重复可去重并记录计数，不能把修订平均。先筛 available_at≤origin，再按(d,s,k)取最高可用revision；相同最高revision内容冲突隔离，禁止按文件末行任意胜出。检查版本时序及服务日期/到达时间；如出现非单调版本明确策略并留异常。来源记录至少原行号/内容hash、revision、available_at、origin和用途。
2. 训练target只能为原点前已登记标签；9/30日期出现并不表示9/30需求已知。settlement_yuan是随日报到达的结果，不能作为目标日期的先验特征。可用的历史滞后也须追踪其发布时刻与构造过程；设计默认排除结算字段，以减少不必要泄漏。
3. weather按(d,zone,kind,available_at)审计；预测目标只用该原点前forecast，不以observed补空或替换。空雨量为missing，不能默认为零降雨。训练/测试插补器及缺失指示仅在各训练折拟合；历史observed可做后验天气误差分析，不能进入原点未来输入。历史forecast/observed的比较须显式用途与可知性。
4. promotions按announced_at≤origin构造当时公开计划；若未公布，是未知计划而非已知零折扣。当前最终原点全部1344促销可用，但历史14天有未公布期；需要可知值+known indicator+冻结缺省/情景策略。重复键/多公告如出现先查来源与语义，禁止未解释多对多连接。
5. calendar为事先已知；stores唯一store→zone；items唯一item参数。连接后每原始组合的行数不放大。范围/主外键/日期/单位都要检查；非有限需求预测、成本、分位数、q在约束聚合前拒绝。

## 每条接口的必要字段

字段可以拆为表与元数据文件，不要求在每行重复全部hash。

| 接口 | 必要内容 | 消费方必须核对 |
|---|---|---|
| audit/snapshot | 原件hash、origin、timezone、用途、键、label/feature来源及可用时刻、去重/版本/缺失策略、异常 | 由raw抽样和边界行重建；输入无未来来源；完整日/序列标识 |
| experiment config | task/run id、输入身份、原点列表、训练/选择/校准/最终验证划分、horizon、特征availability策略、评价label cutoff、方法、参数、seed、指标/选择准则 | 生产前冻结；看过保留折则不能再自称未触碰；结果依赖配置可重跑 |
| prediction table | service_date/store_id/item_id、demand_point_units；不确定性方案的区间上下界及level或关联scenario表 | 点预测有限非负；区间非负、上下界有序、水平明确；必要分位数不交叉；1344键精确等于笛卡尔积 |
| predictive scenario | scenario_id、weight、逐组合需求、generation来源/seed/依赖结构、校准证据、用途 | 权重有限非负且和为1；需求非负；每场景完整键；仅边际区间不可冒充联合情景 |
| replenishment | service_date/store_id/item_id、q_units；origin、对应forecast/config/hash | q严格非负整数非bool，≤商品上限；逐日sum q≤1600、sum c q≤6000，由raw重算 |
| decision evidence | 每日量/金额及slack、按店/商品资源、期望或回测loss、shortage/waste分项、求解状态/bound/gap/时长、比较对象 | loss不加采购；评价是历史/情景/点估计哪一种；求解界不能推导真实未来最优 |
| figure/claim registry | claim_id、所答原题、result路径/hash、列/过滤/计算、figure/table位置、结论限制、状态 | 没有真实结果不写数值；纸面数字能返回到机器结果与raw |
| final run | 原件身份、代码/config/dependencies、命令、seed、原始起止/输出、失败/恢复、clean rerun对比、final hashes | 没有隐藏手工修表；CPU/库/求解及渲染未知如实；actual tokens/cost无则null |

CSV统一UTF-8、稳定排序，日期ISO，字段名与说明一致。需求点预测不要求整数；q必须整数。浮点计算允许预先声明合理数值容差用于目标/重跑比对；硬容量按整数，采购成本读原件精确值或约定货币精度，不能把超限容差变相放宽约束。
