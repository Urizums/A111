# R19-L3 原题执行交付入口

本目录是从冻结的 L3 工作流、原 L3 用户输入及三份官方原文件独立执行得到的离线研究产物。包含真实程序、六任务逐件空间装载、计算、图表、中文论文及题目3技术报告。不存在上传、投稿、联网、安装或其他层数据消费。全部检查标签均为生产者自检；独立审查由root另外组织。

## 先看结果与原题对应

- `paper.md` / `paper.pdf`：完整中文论证，PDF 11页，按实质内容排版。
- `technical_report.md` / `technical_report.pdf`：题目3企业技术报告，PDF 3页。
- `plans/<任务>/selected/placements.csv`：每件坐标、尺寸、原轴置换、车辆归属和支持件；不是仅给类型模式。
- 同目录 `metrics.json`、`vehicle_summary.csv`、`config.json`、`validation.json`：目标、逐车比率、实际配置和坐标核验。
- `result.json`、`evidence.csv`、`TODO.md`：终态、要求对应证据和未解事项。

|任务|结果|费用/元|空间利用率|载重利用率|最优性界|
|---|---|---|---|---|---|
|Q1-S1|车型1，89G1+268G2|450|93.4498%|53.5333%|采样非支配，未证全局|
|Q1-S2|车型2，408G5|700|94.0408%|73.4400%|采样非支配，未证全局|
|Q1-F1|20辆T1，全部3000件|9000|74.0440%|34.2500%|16≤最优车数≤20|
|Q1-F2|10辆T2，全部3000件|7000|68.9916%|41.1000%|7≤最优车数≤10|
|Q2-N|10辆T2，全部3000件|7000|68.9916%|41.1000%|7≤最优车数≤10|
|Q2-C|10辆T2，全部3000件|7000|68.9916%|41.1000%|4900≤最优费用≤7000|

主要解释：标准/易碎允许正交轴置换，定向固定原姿态；非地板整底面由一个下层完整支撑；易碎下层必须标准且上方不承载；按实际接触面积传播累计重量，500kg/m²；顶部至少3cm。均匀质量/静态重心是缺失数据假设。易碎保持原高度、只放地板、承压计自重等另有真实敏感性输出，不混入正式场景。

## 一条命令重新计算六个正式任务

在本目录打开PowerShell，用现有Python3.12及已有numpy/scipy即可重新求解并核验六任务。输出目录必须新建，避免覆盖旧证据。

```powershell
py -3.12 -X utf8 -B .\src\reproduce.py --out .\replay\user_run1
```

该命令从`data/instance.json`与冻结配置计算新坐标；车型1整批重新求列模板MILP并装车，其他任务重新构造。不会将原`placements.csv`当答案返回。完成后`receipt.json`列出N、费用、利用率、体积、重量、库存差值和坐标字节比较。已实际执行`replay/fresh1`，六任务坐标字节一致。一次本机端到端观测约1.67秒，不是大规模速度承诺。

## 通用算法附件接口

```powershell
py -3.12 -X utf8 -B .\src\solver.py --task Q2-C --input .\data\instance.json --out .\replay\generic_case --method maxrect --seed 11 --alpha 0.5
py -3.12 -X utf8 -B .\src\checker.py .\replay\generic_case
```

任务ID为Q1-S1/Q1-S2/Q1-F1/Q1-F2/Q2-N/Q2-C。单次构造命令输出合法启发式候选，不承诺等于多启动/模板库最终方案。`--method baseline`运行同约束基准；`--config`可传gap、pressure、run_seconds、fragile_upright、fragile_floor、own_mass、reserve_support、fragile_priority等研究参数，官方主场景为gap=3、pressure=500。α在0—1间，仅引导搜索，单车最终仍需非支配排序。

输入是JSON对象，含cargo和vehicles数组。cargo每条有cargo_type、category（standard/fragile/directional）、l_cm/w_cm/h_cm、weight_kg、quantity；vehicles有vehicle_type（T1/T2对应任务接口）、l_cm/w_cm/h_cm、capacity_kg、cost_yuan。尺寸/质量/容量/费用须正有限数，数量须非负整数、总货物至少一件、类型ID不重复。`data/instance.json`提供完整示例，程序不依赖固定已存坐标。原件未知字段应保持null，不允许把附件2缺失质量/数量直接输入完整求解冒充官方实例。

退出0表示构造/检查完成；退出2表示参数、无可装列、运行边界或验证失败，标准输出有机器可读失败类型。`No legal column`仅说明此保守构造未找到，不能被当成原三维实例不可运输的证明。`boundary_tests/summary.json`记录三个实际CLI子进程：有效新数量输入通过，负尺寸和单件过大以2退出；还验证重复ID、重叠、定向朝向、悬空、非有限坐标和易碎承载等拒绝路径。

所有坐标单位cm，原点右后下，x朝车头、y朝左、z向上；orientation字符串给车x/y/z轴各取原哪一轴，例如yxz。support_ids是直接支持者件号，由检查器自行计算后对照。浮点接触容差1e-7cm。

## 研究证据与运行次序

`src/preflight.py`读取原文件、核哈希并审计字段；原文件保持只读。随后`smoke.py`运行真实小批和非法拒绝；`experiment.py`运行每任务28候选，共168次；`sensitivity.py`运行29场景348次，`unify_sensitivity.py`把两个目标合法池共享择优；`column_milp.py`对两初始库求占地MILP再做48次装车；`deep_columns.py`扩展多类型嵌套列并做64次装车；`local_search.py`运行1674次两车重装。顺序执行各脚本，等当前进程退出后再启动下一求解脚本。

全部候选在experiments/、column_milp/、deep_columns/、local_search/中保留；logs/存配置声明、真实调用及失败。参数场景配置、坐标、逐车检查存sensitivity/；原始共享选择前表也保存。附2解析及40个尺寸适配测试在extension/，准确范围仅为解析和单件几何，不宣称完整运输通用性。小实例精确体积界在oracle/。

制图及PDF命令为`publication.py`和`pdf_qa.py`，要求已存在matplotlib/reportlab/PyMuPDF/Pillow等现有库；不安装TeX。图表CSV与PNG在figures/，所有PDF页渲染图与总览在pdf_qa/。环境版本见logs/environment.json。

## 结果限度与真实资源记录

未证全球最优。嵌套单支持列和有限候选是原三维可行域的保守子空间，模板库MILP最优不等于连续三维最优。主单车有限候选未证完整Pareto前沿。动态道路安全、摩擦/绑扎以及竞赛提交合规未给数据/规则。易碎原高度情景得到15车10250元，主场景方案对解释敏感。

原计算窗口3600秒，每阶段/调用另有前置资源声明，内存目标1800MB非OS强制。实际出现两次求解并发偏离，其中MILP/参数最小重叠1.84秒；保留原声明与事实，不将其重命名为符合串行条件。未知模型、token和cost始终null，全部动作只在本执行目录写入。工具恢复、实质修复和正常研究分开记录，未采用“两局部错误停止全部任务”。完整记录见logs/failures.json、invocations.json和resource_final.json。

终态入口`result.json`与`manifest.json`只表示实际产物冻结和生产者自检状态，不代表独立审查通过、获奖或比赛评分。独立审查接收者应直接读原题/附件、配置/源码、全部终态产物及原始约束，自己下判定。
