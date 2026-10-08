# L4 完整练习成果与程序附件

最终中文论文：paper/paper.md 和 paper/paper.pdf（12页）；企业报告：paper/enterprise_report.md 和 paper/enterprise_report.pdf（3页）。results/selected.json是最终坐标目录索引。选中T1整批20辆9000元、T2整批10辆7000元、混型10辆（1T1+9T2）6750元；均是经过作者逐件自检的可行上界，原题最优未知。正式算法比较、17参数实验、64附件2区间几何和所有失败保留；不把作者自检称独立验收。

## 运行

在本execution目录打开终端。既有Python 3.12.8，核心程序只需numpy 2.5.3、scipy 1.17.1。无联网、无安装、无交互输入。

```powershell
py -3.12 -X utf8 -B code/solve.py --data data/instance.json --config configs/refined.json --out results/new_run --method maxrects
```

可选method为shelf、maxrects、improved；共用可行域和预算。refined.json固定96偏好模式/车型、12整批起点/车型、每次整数主问题90秒；seed1904。墙钟限时可能使其他机器候选不同，保留最好可行方案和真实状态。失败产生非零退出，几何拒绝时保留rejected_check.json和rejected_placements.csv。没有将程序退出0视为几何验证。

```powershell
py -3.12 -X utf8 -B code/validator.py --data data/instance.json --config configs/refined.json --placements results/new_run/Q2_min_cost/placements.csv --out results/new_run/Q2_min_cost/coordinate_check.json
```

单车CSV检查追加--single，整批不得追加。校验器独立于求解代码，从每件坐标恢复边界、正交分離、许可姿态、唯一父支撑、易碎封顶、定向重心、累计外载与接触压力，重算库存、UV、UW和费用。

## 输入和换数据

复制data/instance.json为新的文件，保持两种车型、五类数据合同，修改dims（cm）、mass/capacity（kg）、quantity（非负整数）与cost（元/趟）；至少有一件货物，所有尺寸/质量/额定载重/费用为正。cargo.class为standard/fragile/oriented，ID保持唯一。新输入不是官方附件，需标注合成或实測来源；使用新的输出目录，不覆盖已检结果。config记录gap_cm、pressure_kg_m2、易碎姿态解释和完整单件支撑。新输入无法在任何车中放一件时会报错，不无限新开车。当前接口是给定JSON合同，官方评测CLI未提供，不声称兼容。

实际外部文件改变库存为750件的CLI已经运行，结果变化为5辆T1、3辆T2等可行候选，证据checks/input_change.json。附件2缺批量/单重/类别/载重/距离，不把区间文件当完整实例默默补齐。

## 结果字段

placements.csv每行一件，truck_id/vehicle_type/item_id/cargo_type/x/y/z/l/w/h/orientation/support_ids/column_id。xyz是右后下O为原点、x向前/y向左/z向上的最小角，cm；LWH等方向编码表示原长/宽/高置换。FLOOR是地板。support_loads.csv给外载kg、顶面积m²、限载kg。summary.json为status、valid及违约、类型计数、车数/成本、总重/总体积、UV/UW、逐车统计、config、合法下界及受限MILP状态。UV分母原LWH；usable_UV另外用H-gap；全批指标总量/总容量。单车允许未装库存，整批恰好一次。

results/selected_single下四个有限非支配档案方案，不能视为完整真实Pareto前沿。results/classic_refined的四个整批场景为最终坐标。

## 实际检查和复现

checks/smoke.json：五类真实小切片、堆叠链、六类实际非法输出拒绝、合法边界接受。checks/acceptance.json：12正式整批候选/4最终单车/17参数案例完整重算。checks/clean_rerun.json：从起初不存在的清洁目录，仅复制核心代码/data/config完整重跑；4正式场景车数、费用、UV/UW和坐标CSV哈希全部一致，实际215.732秒。checks/reading_review.json：12+3页全部渲染，字体字符、图表、页码、边界和阅读自检。

原科学库版本见checks/audit.json。图表与论文由真实表消费，来源见checks/figure_provenance.json与paper_numbers.json。clean_workspace是此次实际复跑证据，保留完整输出；正式旧失败位于results/improved及logs/events.jsonl，尺寸小数拆分失败在parameter_failure_dimensions_095.json，不删除。初始失败坐标因当时校验先于保存而没有保存，具体错误/输入/修复均保留。

参数实验：code/experiments.py（共同24偏好/4整批起点/8秒混型主问题，17组）。它保留已完成表行并只续跑未完成场景；如需全新复跑，请复制程序/data/config到另一个空目录再运行，避免把已完成旧表当新运行。不要删除此试验已有结果。

## 压缩程序附件与范围

program_attachment.zip包含可运行核心求解/校验/参数代码、data/config、此README、选中全部逐件方案；可解压到新目录运行第一条命令。完整工作域另含全部实验、论文、图表与检查。原PDF/DOCX/XLSX只读来源未打包改写，哈希在审计中。

数学限制：保守单父完整支撑和一至两段柱；易碎可旋转主假设及原高固定敏感性；均质静态重心；无多支撑受力、轴载/绑扎/装卸/振动实測。车数下界15/7/混7、费用下界4900与上界未闭合。正式规则、AI/上传/匿名格式/评测CLI未给，未联网、未安装、未上传或投稿。接收时需按原题与文件独立复核，而非接受本作者的pass标志。

## 身份与终态

任务R19/C11/L4，作者/root/r19_l4_executor。仅本execution写域；本轮未另开agent。result.json记录终态、实际预算、仍待接收事项；manifest.json逐文件path/size_bytes/sha256相对工作根且不含自身。未知实际model/token/cost保持null。终态后停止写入。
