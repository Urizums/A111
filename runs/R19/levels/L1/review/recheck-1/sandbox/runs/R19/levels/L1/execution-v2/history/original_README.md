# L1执行交付与复现

这是官方D题的完整离线练习论文及算法产物。设计原件保持只读；所有执行调整、失败和迭代在本目录留痕。没有联网、历史题解、其他层或外部验收表输入，没有安装软件。单一执行代理完成，不把角色名作为真实子代理分工。

## 主要交付

- paper/paper.md：完整可编辑中文论文。
- paper/paper.pdf：可读中文成稿，字体嵌入；paper/qa保存全部页渲染与视觉核查。
- results/final/*_placements.csv：四个全数量任务每件坐标、姿态、车号、重量；单车候选有完整JSON。
- review/full_check.json：每车支撑、承重、重心核算；review/check_report.json为逐要求作者自检，独立验收另行进行。
- results/sensitivity：32个冻结情景的实际全部布局、两个目标、检查及耗时。
- inputs/source_audit.json、normalized.json、attachment2_geometry.json：原件身份/全文、规范字段、XLSX区间与缺字段审计。

## 一条命令重建已选方案

在包含runs/R19/inputs/raw官方三份原件的仓库根执行；输出目录必须为新目录：

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L1/execution/src/reproduce.py --out runs/R19/levels/L1/execution/results/reproduction_new
```

命令从DOCX/XLSX读规范数据、按已选可重复算法配方重新摆放七项任务、独立核算全部约束，输出逐件CSV、汇总表、图与比对报告。程序对原三源件SHA256检查版本，原件移动时需保留同一相对结构。推荐配方是T1模块变体1、T2模块变体0、单车T1策略6与质量锚点、T2G5锚点；两个混合目标此次推荐与T2车队完全一致，原99模式两个主目标的最优收据另存，不用复现推荐方案冒充重做全局优化。干净目录同宿主重建通过七项几何完全一致和关键值一致。

## 可重跑搜索与新输入

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L1/execution/src/solve.py --config runs/R19/levels/L1/execution/configs/base.json --budget 12 --out runs/R19/levels/L1/execution/results/new_generic_search
py -3.12 -X utf8 -B runs/R19/levels/L1/execution/src/module_sweep.py --out runs/R19/levels/L1/execution/results/new_module_search
py -3.12 -X utf8 -B runs/R19/levels/L1/execution/src/boundary_tests.py
```

solve.py支持符合base.json结构的自定义JSON（保持五类型G1-G5，修改其尺寸/质量/数量与车辆参数；本题算法并未验证任意业务类型ID）；缺业务字段、负数量/尺寸/载重、非法类别会报错。几何模式并非所有连续摆放枚举，未找到更好解不证明最优。一般算法对新货物维度按其0.1cm有理公因子建网格，很小公因子会增加内存/时间；模块仅支持附件1原尺寸，不支持时回通用算法。单车结果是有限候选非支配集。solver内部调用SciPy自带HiGHS，无额外安装。

finalize.py整合本次v2一般算法和modules_v3结果，成本/车数各60秒、已有可行上界剪枝，始终保留较好真实incumbent；旧失败目录不会自动入选。重新探索的耗时受系统负载影响，MILP超时可能改变incumbent，报告其真实状态。

## 参数与图文重建

configs/experiments.json冻结32个情景与原900秒启动窗口；首窗口实际923.810653秒，最后已启动情景完成形成23.810653秒超出。原记录保留，不截断。追加窗口最多600秒只接续剩余两项，见configs/experiment_resume.json与results/sensitivity/invocations.jsonl。各情景重新求解/校验；费用变化重解模式。正文仅使用完成且通过的实算行。experiments.py --resume仅跳过已完成记录，完整重新运行需保存旧结果后另安排目录，不能把重跑归零计数。

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L1/execution/src/make_paper.py
py -3.12 -X utf8 -B runs/R19/levels/L1/execution/src/render_paper.py
```

图文由冻结final/sensitivity结果生成。PDF使用系统已有SimSun、SimHei字体，PyMuPDF渲染核对。算法附件不依赖字体；图文导出需这些字体或自行声明替换，并重新核对。PDF是自定练习格式，未核验当届竞赛模板/AI规则/上传接口，未自动提交。

## 结论边界

3000件总体积287.35m³、总质量41100kg。T1全批次20辆/9000元，T2全批次10辆/7000元；混合两个推荐目标均10辆T2/7000元，99模式池内车数和费用均证明最优，但原题连续几何全局仍只有N1∈[16,20]、N2/混合N∈[7,10]、混合费用∈[4900,7000]。主口径为全底面、保守易碎原姿态、逐接触定向重心、局部竖直累计传力，不含动态道路安全。附件2缺质量、数量、类别、载重和趟费用转换依据，64个真实配对是几何接口测试，不是完整业务通用性验证。峰值内存、真实provider model/token/cost未知null。

## 环境

Python版本：3.12.8 (tags/v3.12.8:2dc476b, Dec  3 2024, 19:30:04) [MSC v.1942 64 bit (AMD64)]

已存在库：numpy=1.26.4, scipy=1.17.1, matplotlib=3.10.9, pandas=3.0.2, docx=1.2.0, openpyxl=3.1.5, reportlab=4.4.10, pypdf=6.10.2

不需要联网或安装软件。源码目录无模型权重或商业solver，实际硬件与包版本见logs/environment.json。
