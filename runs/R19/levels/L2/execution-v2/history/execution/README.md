# R19 L2 完整研究交付

论文：paper/paper.md与paper/paper.pdf；企业技术报告：report.md与report.pdf。四个全运场景、两车型单车非支配候选、逐件坐标/姿态、真实代码、36个实验、6幅图、检查与失败历史均已产出。当前状态是作者完成不同实现重算与离线复跑，独立外部审查尚未开始；不宣称全局最优、赛事评分、获奖或官方投稿合规。

附件1为3000件、287.35m³、41100kg。被选结果仅车型1为25辆/11250元，仅车型2为13辆/9100元；混合两目标重新求解均为13辆（1辆V1、12辆V2）/8850元。容量松弛下界16、7、7辆及4900元，原三维问题未证最优。模式库213个，其整数主问题Optimal不等于三维问题全局最优。参数原32例全部保留，随后前瞻增补易碎地板同高1例、不同种子3例，总36例：35合法、1极端车高失败。

## 已成功执行的命令

以下从仓库work/A111根目录执行，写入均在execution子目录。只用现有Windows Python3.12和科学库，不联网、不安装。

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/main.py --raw runs/R19/inputs/raw --output runs/R19/levels/L2/execution/results/final
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/check_cases.py
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/audit.py
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/check_patterns.py
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/enrich_receipts.py
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/experiments.py
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/build_delivery.py
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/main.py --raw runs/R19/inputs/raw --output runs/R19/levels/L2/execution/results/reproduction
```

final与首次不存在的reproduction输出目录语义指标及全部placements.csv字节一致，代码SHA-256一致。checks/reproduction.json保存实耗（43.72/42.37秒）和对比。experiments.py有checkpoint，已有case保留且跳过，运行它可恢复未完成案例；重新计算某已保存参数可用以下接口指定新输出目录。

```powershell
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/main.py --items runs/R19/levels/L2/execution/experiments/00_vehicle_length/items.csv --vehicles runs/R19/levels/L2/execution/experiments/00_vehicle_length/vehicles.json --config runs/R19/levels/L2/execution/experiments/00_vehicle_length/config.json --scenario q2_cost --output runs/R19/levels/L2/execution/results/parameter_replay
py -3.12 -X utf8 -B runs/R19/levels/L2/execution/code/validate.py --placements runs/R19/levels/L2/execution/results/final/selected/q2_cost/placements.csv --items runs/R19/levels/L2/execution/data/items.csv --vehicles runs/R19/levels/L2/execution/results/final/selected/q2_cost/vehicles.json --output runs/R19/levels/L2/execution/checks/manual_validation.json
```

额外重放命令不代表本交付执行了所有新命名输出；实际执行记录以logs及checks为准。算法附件algorithm_attachment.zip包括主代码、验证器、规范数据、原件和默认配置；解压后可在其根运行`py -3.12 -X utf8 -B code/main.py --raw raw --output replay`。ZIP本身的独立解压烟雾重放见checks/algorithm_attachment_replay.json。

## 输入与输出接口

main.py支持--raw、--items、--vehicles、--config、--scenario、--output。--scenario允许all（含所有单车/全运）、q1_all_v1、q1_all_v2、q2_vehicles、q2_cost。当前求解器面向题目两车型V1/V2、五类同尺寸同单重货物，CSV同一cargo_type必须同质；官方未知测试协议未适配，不把它称任意物流实例通用求解器。

items.csv必填item_id、cargo_type、category（标准件/易碎件/定向件）、canonical_l_mm/w_mm/h_mm、weight_kg、source_ref。姿态集合由category与配置推导，保留原始底面。vehicles.json每项含type_id、dims三轴整数mm、payload_kg、cost_yuan_per_trip、clearance_mm、source_ref。config含seed、starts（随机权重数量）、time_limit（仅MILP）、pressure、platforms、fragile_fixed。

placements.csv为最小角点与轴置换，车辆原点右后下，x朝车头、y朝左、z朝上。每个场景含vehicles_summary.csv（逐车两利用率及成本）、supports.csv（重建接触面积/传载）、validation.json、run.json；所有完整布局恰好3000个不同源ID。单车库存上限选择以validation的partial模式核验。主全运总体空间率分母为全部已用车名义容积和，重量率为额定载重和。

validate.py为不同于构造器的实现。CLI有效返回0，非法返回2；实际超高拒绝记录在logs/cli_rejection_receipt.json。16个边界用例全部按预期，包括累计600kg/m²拒绝、500等式接受、易碎多标准支撑。source_result_audit.json从原DOCX重新核对5类、2车、所有最终方案及指标，下界重算一致。

## 文件与证据

- data/：原件独立抽取、3000件规范数据、两车型、附件2资格审计。
- results/main/：第一轮同类竖列模式结果，不覆盖；results/improved/：平台研究迭代；results/final/：最终代码原件生成的被选run；results/reproduction/：全量干净复跑。
- experiments/：36个case的真实输入、配置、模式、输出或failure及CSV/manifest。数量/构成扰动和6000件规模均为合成附件1订单；附件2没有被冒充官方全约束订单。
- figures/：单车搜索非支配集、代表车3D/俯侧视、四全运比较、参数和性能图，全部源于结果。
- checks/：源/结果重算、原始边界测试、真实smoke、CLI拒绝、复跑、PDF逐页QA及要求映射。
- logs/：环境、原始stdout、真实失败/恢复/中断与研究迭代；未知model/token/cost均null。
- claim_evidence.csv：要求—结论—源定位—结果—论文章节—检查—限制。

## 口径、资源和剩余限制

assumptions.md冻结完整支撑、易碎平面转向、定向逐下件质心、接触面积比例累计荷载。承载面积转换mm²/10^6，间隙主值30mm；地板不套用货物500kg/m²限制。更严格易碎地板同高/单一地板支撑与固定姿态分别重求解。允许部分支撑/力矩平衡扩展未求解，未用保守模型失败证明宽模型不可行。

主MILP限60秒，参数MILP限8秒；生成/验证时间不包括在该限制内，实际总时间可超限并保留。Intel i7-14650HX、16核24逻辑处理器，Windows11，库版本见环境记录。没有整个任务期限或两轮纠错停止规则。账号中断后旧会话未知，真实进程核查未见仍运行，保留已完成13例并续跑余下例。协作写域不是OS隔离。

尚未完成：原问题全局最优证明、更宽几何支撑模型、附件2真实完整订单验证、独立上下文正式首审、真实装卸/动态安全验证、官方投稿格式/AI规则/评阅I/O核实。它们不被文件存在或作者自检追认为完成。当前产物可交给外部首审；本程序不投稿或上传。

终态补充：213/213最终候选模式逐件、方向、支撑、累计压力及数量向量重算全部通过（checks/pattern_library_validation.json）。run.json的audit_identity由enrich_receipts.py事后绑定真实raw/input/config/假设/已记录代码身份；早期实验没有捕获的代码启动身份、单run UTC时间仍为null，不以当前文件hash或mtime冒充原调用遥测。PDF逐页最终视觉和文本框检查见pdf_visual_qa.json。独立首审依然未开始。
