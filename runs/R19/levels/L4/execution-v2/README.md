# L4 同一作者知情修订版 v2

本目录可独立消费和运行。中文数学论文在paper/paper.md、paper/paper.pdf（12页），企业报告在paper/enterprise_report.md、paper/enterprise_report.pdf（3页），程序附件为program_attachment.zip。results/selected.json用本目录相对路径索引最终坐标。论文、报告、核心源代码和ZIP均属于v2；现有研究结果及图表通过base-binding.json绑定原版字节，复用证据与本轮实际检查在下文分别说明。

同一原作者/root/r19_l4_executor在首审后知情修订。首审结论仍为a1/a2/a3/a5 pass、a4 fail、a6 partial：合法单件仅把x改成NaN，旧接收CLI实际exit0/VALID，而独立检查拒绝。原版execution及review/initial冻结不改；历史result/manifest/README/TODO和获准首审文件副本在history。v2作者自检完成，仍待同一独立接收者知情复审，没有将首审失败覆盖成通过。

## 运行与数值接收

在本目录（或ZIP解压根）打开终端。既有Python 3.12.8，核心依赖numpy 2.5.3、scipy 1.17.1；离线、不安装、无交互输入。

```powershell
py -3.12 -X utf8 -B code/solve.py --data data/instance.json --config configs/refined.json --out results/new_run --method maxrects
py -3.12 -X utf8 -B code/validator.py --data data/instance.json --config configs/refined.json --placements results/new_run/Q2_min_cost/placements.csv --out results/new_run/Q2_min_cost/coordinate_check.json
```

可选method为shelf、maxrects、improved。refined.json固定96偏好模式/车型、12整批起点/车型、每次整数主问题90秒、seed1904。墙钟停止可能影响其他机器的搜索点；不能将程序exit0当作所有外部输入都合法。单车CSV校验追加--single，整批不得追加。

新增code/numeric_contract.py在优化和几何/指标计算前接收数值。JSON中的尺寸、质量、额定载重、费用及数值配置必须是有限JSON数，不能用NaN、±Inf、字符串或布尔值代替；尺寸/质量/载重/费用及压力阈值为正，quantity是非负整数且总库存为正，安全间隙非负且小于每种车的内高，容差非负，模式/起点/seed及时间窗口有相应整数/正值范围。体积、批次体积和质量也检查有限性。CSV的x/y/z/l/w/h必须可解析为有限实数，l/w/h为正，xyz不得小于负容差；然后继续按车厢边界、原物件尺寸/许可姿态、库存、交叠、唯一父支撑、累计荷载、易碎封顶等原约束接收。拒绝非法值，不将NaN改成0，也不计算貌似成功的利用率。

接收器非法输出exit1，JSON为valid=false及具体invalid_numeric/invalid_range等错误。求解器非法输入exit2并保存failure.json；合法数值但某件在所有车型/允许姿态及载重下都不可装时exit3、INFEASIBLE_INPUT，并说明具体货物与约束，保存failure.json。1001×1001×1001cm单件已实际走这一分支，无矩阵traceback、无成功summary。请始终使用新的输出目录，以免把旧summary误当本次成功。其他求解异常/几何失败保留实际拒绝证据；这里没有声称证明所有可行实例均可由受限算法找到。

## 输入、坐标与方案

data/instance.json是附件1的规范化实例，configs/refined.json记录语义假设。换数据时复制JSON并保留两车型、五类货物的合同和唯一ID；dims用cm，mass/capacity用kg，quantity用整数，cost用元/趟，class为standard/fragile/oriented。新输入标明合成或实测来源。官方评测CLI未提供，不声称兼容。

placements.csv每件一行，含truck_id/vehicle_type/item_id/cargo_type/x/y/z/l/w/h/orientation/support_ids/column_id。xyz是车厢右后下O为原点、x向前/y向左/z向上的最小角，单位cm；LWH等方向编码是原边置换，FLOOR是地板。support_loads.csv给累计外载kg、顶面积m²和限载kg。summary.json给实际目标、库存、体积/质量、逐车统计、config、下界和受限MILP状态；UV用原LWH，usable_UV另用H-gap；整批率按总货量/总容量。

所选可行上界不变：全T1为20辆9000元；全T2为10辆7000元；两个混型目标选1T1+9T2、10辆6750元。四场景坐标在results/classic_refined，四个单车有限档案在results/selected_single。全局车数/费用最优未知，档案不等于完整真实Pareto前沿。总量松弛车数下界15/7/混7，混型费用下界4900元。

## 本轮实际操作与证据复用

1. checks/revision-checks.json：保留旧版NaN误接收及1001cm矩阵traceback的真实重现回执；新增67个主要CLI控制（包括合法对照、坐标NaN/±Inf和范围、输入非有限及范围、配置范围）以及24个输入非有限接收CLI检查。非法值非零拒绝，合法对照接受；每次命令/退出/stdout/stderr/耗时在checks/revision-receipts。1001cm新非零说明另列。
2. 对既有结果重验：33组坐标（12正式整批、4所选单车、17参数实验）由新版接收核心完整重算；四所选整批又实际运行新版接收CLI。这里重验坐标，没有重复全部历史优化研究。
3. 实际重新求解：checks/revision-clean起初不存在，只复制三个新版核心文件及data/config，按相同96/12/90、seed1904运行正式全量maxrects路线。实际132.564872秒，四场景12,000件行重新产生并接收，车辆数/费用/UV/UW/总量与所选方案一致，四份CSV字节哈希也相同。证据为checks/revision-clean-receipt.json及revision-clean/results。这是本轮全量重跑。
4. ZIP实际检查：checks/revision-archive-receipt.json记录CRC、三个核心字节一致性、解压后750件合成库存/12模式/2起点/8秒的求解烟测及解压版NaN/合法接收对照。ZIP烟测不是官方全量再跑，官方全量使用上一项清洁目录。ZIP含新版核心、data/config、本README、base-binding和所选全部逐件方案，可解压运行以上命令。
5. 最终图文：本轮重新生成两份PDF并渲染全部12+3页；checks/revision-reading-review.json记录实际阅读自检。新增论文7.4及企业报告6说明首次接收失败、校验范围、修订与未复审状态。历史研究数字、单位、假设及最优性主张强度保持不变。

复用原版的算法比较（共同96/12/90）、17参数/规模/种子实验（共同24/4/8）、64附件2几何区间实验、所选坐标与图表。历史checks/acceptance.json、clean_rerun.json、reading_review.json、archive_cli_test、clean_workspace及原结果JSON的valid标志均是原版记录；本轮效力以revision-*证据为准。base-binding.json逐文件绑定原execution，history保存原始终态，logs/events.jsonl累计全部历史和新增attempt，不归零。

原最早小数尺寸截断失败的坐标当时没有保存，不能事后补造；错误、输入与真实修复仍在parameter_failure_dimensions_095.json及日志。历史初版扰动候选费用较差、配额资源接续、字体和路径失败同样保留。code/experiments.py只续跑未完成参数表；若要全新参数研究，请复制代码/data/config到空目录，不能把已有行算作新运行。

## 适用边界和身份

保守单父完整支撑、一至两段柱、易碎可旋转主假设及原高固定敏感性、均质静态重心仍相同。没有多支撑受力、轴载/绑扎/装卸/振动实测数据。附件2缺批量/单重/类别/载重/距离，未补造完整运输实例。正式规则、AI披露/匿名封面/上传格式未提供，未联网、未安装、未上传或投稿。

任务R19/C11/L4，同一原作者，本次仅execution-v2写域，未另开agent。result.json保留原身份/目标/历史研究预算和失败，区分新版作者自检与待独立复审；未知实际model/token/cost为null。manifest.json逐文件path/size_bytes/sha256相对A111工作根、payload排除自己。终态后作者停止写入；下一步由协调者安排同一接收者在另域知情复审。
