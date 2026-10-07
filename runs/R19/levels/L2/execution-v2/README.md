# R19-L2 知情质量修订 v2
同一原题、同一作者的新研究版本；原首次独立首审a1–a6全pass、实验充分性partial永远保留。本版作者实质检查完成，待同一审查者知情复审；不替代初审，也不宣称原题最优/获奖。

## 先读及当前结论
- paper/paper.md与paper/paper.pdf：完整中文论文12页；report.md/report.pdf：企业报告2页；figures/7幅实际科学图。
- result.json、DIFFERENCES.md、TODO.md及claim_evidence.csv说明问题覆盖、实际范围、差异与未闭合事项。
- 四个完整全运目录在results/final/selected：仅V1为22辆9900元；仅V2为12辆8400元；混合车数目标12辆8400元（全V2）；混合费用目标13辆7850元（5V1+8V2）。绝不是12辆7850元。
- results/final/single包含V1两个、V2一个离散搜索非支配点及完整位置。V1数量向量63,300,0,0,0：空间91.0173%、载重52.6000%；63,264,18,0,0：95.8874%、52.3000%。V2向量0,0,0,0,408：94.0408%、73.4400%。非完整Pareto前沿。
- 高度量化q=50mm必要界：16辆V1、8辆V2、混合8辆/5350元，证明research/bound_proof.md。原更宽正交域也适用，但聚合界不是可装证书，主相对界差距33.33%车数、31.85%费用仍未闭合。

## 真实研究与时间口径
计算前计划/窗口/锁在research；原始9调用按19、7、41配对A同型柱/B固定平台/C新增保护块，均同22随机+3固定权重、45秒每MILP、300秒外层。raw原始输出不改；guarded为同等追加的候选保护，包含重生成完整候选/验证/导出秒，模式与原库逐字段完全一致。B→C三对费用节省1000/1600/1150元，平均1250元/13.71%；B实耗均值72.07秒、C78.45秒，各种子快慢不同。不能把组合几何收益归给一个独立机制或省略认证成本。

36个当前参数在experiments/，35合法+1必要极低车高失败；每例5启动/8秒MILP/120秒外层，与主22启动不同。所有维度完整重求解；严格固定/地板分支、低预算种子波动和反常费用保留。低预算参照13/9100，四种子费用7850–9650，不称稳定。原36案例完整保存在history/execution/experiments，Q3追溯32纠正为旧36+新36，另有9主方法调用。

限时incumbent较差触发两项实质修正：统一保护已有候选、跨目标留存原始incumbent。第一raw复跑114.4569秒及其8050结果原样保存research/guard_correction_1_result、clean_replay_package；第二修正raw复跑115.9038秒产生上述主结果。共享池修正不影响原9组guard，因为其先池化所有raw四场景及fs，再分别评价；checks/guard_pool_reconciliation.json真实复算36组合。参数单select局部已经比较raw，只新增池side effect不改数值，未无效重复36例。详见failure_history和各实际代码hash。

## 离线重放（先复制包/解压至新目录，保持冻结证据）
已用Windows现有Python3.12、numpy/scipy/python-docx/openpyxl，未安装/联网。最稳妥：解压algorithm.zip，进入新目录执行：
~~~powershell
py -3.12 -X utf8 -B code/main.py --raw raw --config configs/main.json --output results/full
py -3.12 -X utf8 -B code/check_cases.py
py -3.12 -X utf8 -B code/validate.py --placements results/full/selected/q2_cost/placements.csv --items data/items.csv --vehicles data/vehicles.json --output results/full/recheck.json
~~~
ZIP不预装答案。已真正从解压原件运行3000件all流程118.8388秒，再独立构造路径核11套新布局，四目标与交付主结果相同；检查证据checks/zip_full_validation.json、logs/zip_full。仅单场景--scenario q2_cost少了其它目标带来的候选，可得到更差合法上界；推荐全流程。正式官方I/O未知。

当前完整研究包复制后可用：
~~~powershell
py -3.12 -X utf8 -B code/main.py --items data/items.csv --vehicles data/vehicles.json --config configs/main.json --output results/user_replay
py -3.12 -X utf8 -B code/check_patterns.py
py -3.12 -X utf8 -B code/audit_v2.py
py -3.12 -X utf8 -B code/check_guard_pool.py
py -3.12 -X utf8 -B code/build_v2.py
py -3.12 -X utf8 -B code/check_manuscript.py
~~~
check_patterns/audit/build针对已保存results/final及完整研究证据。build_v2会按其数据重新生成7图及PDF，使用Windows已有SimSun和reportlab/fitz/matplotlib。运行比较/参数包装器会拒绝重写已完成receipt；要复现研究，请在新副本指定清洁输出域，不能混写冻结原结果。具体设置均有JSON和完整代码，无隐含网络服务。

## 输入输出/模型
原三官方文件在raw，original_request.md保留用户原层级文本；data逐件唯一ID、类型、类别、原整数mm尺寸、质量kg；vehicles JSON内部mm、kg、元/趟、间隙mm。每车位置为右后下原点的最小角，x朝前/y朝左/z朝上，orientation_id为原长宽高轴置换。标准允许六置换，定向012，易碎原底面xy转向；全支撑、易碎只地板/标准共面顶面，任何货物不压易碎，逐下件定向局部质心；面积比例累计传载每接触/平均顶压≤500kg/m²，地板 exempt，30mm间隙。假设/公式在assumptions.md/model.md/正文。

输出每场景placements.csv、vehicles_summary.csv、supports.csv、validation.json、run.json。库存严格等式、不重不漏；单车子集不超库存；原件重算源字段、指标和高度界。受限库mip_gap与原问题界差距分开，status1限时不升级，ε数学主次排序不保证有限容差下次级库内最优。

## 检查、继承及限制
checks证明：225主模式全部真实核；主8全运/3单车与35成功参数布局及36变更输入逐字段重算；16边界+C smoke15+真实保护块正/负；实际非法CLI exit2；九guard池36组合；7论文表82行；14页渲染/目视无页外文本。源码和派生文件清单在artifact_manifest。完整旧691文件按字节复制history/execution，首审公开report/result/lock在history/review_initial；末尾再次核旧691、9引用hash和3原件未变。未读取其余reviewer实现、其他层或root科学观察。

尚未知：原三维全局最优/完整Pareto、宽域部分支撑/力矩、真实材料刚度及动态装卸/轴荷/门口/路径、附件2完整订单、跨实例总体泛化、官方I/O/投稿/AI规则。面积分担与全支撑仍工程/保守假设。旧作者失败/中断与初审失败账不清零，旧全任务资源总数不可完整恢复；新前瞻窗口及实耗单列。真实model/token/cost均null，协作写域不是OS隔离。未上传/投稿。
