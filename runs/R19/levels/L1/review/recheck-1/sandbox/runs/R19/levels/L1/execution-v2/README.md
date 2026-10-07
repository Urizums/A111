# L1 知情修订交付与复现

本目录是同一官方D题/C11/L1作者的F1修订。首次独立初审五项通过、a4因类别来源绕过失败；结果和失败保留，修订通过不追认为首次通过。原execution250文件保持只读，修订仅写execution-v2。REVISION.md解释根因、差异与累计计数。作者自检不等于独立复审，root冻结后由原审查者知情复审。

## 交付与结果

paper/paper.md及paper/paper.pdf为完整中文论文；results/final交付四份全3000件车队及三个单车候选。主结果保持T1 20辆/9000元、T2 10辆/7000元、两个混合目标推荐10辆T2/7000元。全部235个车队实例（7主任务、99模式、32情景×4车队、小链）经修订检查器复核。参数优化没有重跑，原32情景数值/求解时间保留，修订检查时间另记。算法、表图与论文由实算文件生成。

check.py将类别、重量、车型参数从来源配置恢复，并拒绝冲突输出元数据；contracts.py绑定原G1/G2标准、G3易碎、G4/G5定向身份和库存序号。normalize.py实际读取官方DOCX类别单元格并核查三原件SHA256。合法参数可改变原五类尺寸/质量/数量、原车型数值与明确规则开关；货类类别替换、未知货号、非有限物理值、伪装车辆头部不是合法情景。本轮68项知情回归与原15项边界自检均通过，有限测试仍不证明任意恶意输入或数值尺度都可靠。

## 从官方原件重建七项方案

在含runs/R19/inputs/raw的仓库根执行，或把algorithm_bundle.zip解压到一个新目录并在该解压根执行。依赖本机既有Python3.12、NumPy/SciPy、python-docx、openpyxl、matplotlib，不联网、不安装。

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/reproduce.py --out runs/R19/levels/L1/execution-v2/results/reproduction_new
```

输出目录必须不存在或为空；恢复时选择另一新输出目录，不能覆盖已完成证据。入口重新解析官方DOCX/XLSX、生成七项全部坐标、调用修订检查器、比较逐件几何与关键数值并输出JSON/CSV/图/报告。两个混合推荐此次与T2车队一致；此命令重建已选确定性配方，不冒充重跑99模式MILP或原题全局优化。原件核查固定三份官方SHA256。源码ROOT由自身位置计算，不会回写旧execution。

## 知情回归和全部受影响几何检查

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/repair_regression.py
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/boundary_tests.py
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/recheck_affected.py
```

这些命令写本副本review报告，应在解压新副本运行以保留冻结交付。inputs/disclosed_boundary_inputs.json只含已公开初审输入、预期和由公开程序恢复的complete模式，属于知情回归，无审查器代码依赖。首轮67/68失败在history保存，随后修复复播器；修订并未修改库存守恒规则。旧研究自检及旧QA副本在history明确隔离。

## 可重跑搜索与论文

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/solve.py --config runs/R19/levels/L1/execution-v2/configs/base.json --budget 12 --out runs/R19/levels/L1/execution-v2/results/new_generic_search
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/module_sweep.py --out runs/R19/levels/L1/execution-v2/results/new_module_search
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/make_paper.py
py -3.12 -X utf8 -B runs/R19/levels/L1/execution-v2/src/render_paper.py
```

新搜索输出与交付final分开；新候选必须重新检查才可替换交付。finalize.py依赖本目录results/v2及modules_v3，会写final；experiments.py写本副本sensitivity并保留原窗口/恢复记录，不能在冻结根运行。ZIP包括图文构建所需实算依赖，PDF导出另需现有Windows SimSun/SimHei字体及reportlab/PyMuPDF。ZIP可复现修订推荐方案与知情检查、重建图文；它不是全部过去失败/工具恢复/初审过程的自动重演。完整历史以交付目录history及logs为准。ZIP不含自引用的根result.json和自身SHA，bundle_manifest.json说明内容保证，外部root result.json记录实际新路径复现与ZIP哈希。

## 保留的历史与结论边界

原工具恢复1次、实质修正4次，本轮F1使累计实质修正5次，另有本轮复播器修正1次。原参数首窗口实际923.810653秒、超出23.810653秒，追加60.965460秒，累计984.776113秒保留。父节点报告的先前额度失败保留，未知真实provider model/token/cost与峰值内存仍为null。无真实子代理调用。

99模式池内车数10、费用7000已证明最优；连续原题全局仍只有N1∈[16,20]、N2/混合N∈[7,10]、费用∈[4900,7000]。单车仅有限搜索候选非支配集。全底面支撑、保守易碎姿态、逐接触定向重心和局部竖直传力是明确模型口径；更宽松定向情景9辆/6300元不替代严格主方案。没有道路动态/弹性材料/车门装卸运动/客户卸货次序验证。附件2缺质量、数量、类别、载重和趟费依据，只完成64个真实单件几何配对。单实例不证明业务统计泛化，货类身份扩展未支持。未核验当届模板/AI规则/投稿接口，未提交。独立知情复审尚待完成。
