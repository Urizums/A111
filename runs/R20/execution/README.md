# R20 鲜食建模完整执行交付

正式产物在 `delivery/`。这是一份原创合成数据离线研究，并非正式赛题或真实商业收益。所有结果由附件重建，执行者自检不等同独立验收。

## 阅读与使用

- 完整中文论文：`delivery/paper/paper.md`（可编辑），`delivery/paper/paper.pdf`（正式渲染版，11页，全部页面已实际查看）。
- 未来预测：`delivery/results/future_predictions.csv`，1344个唯一日期/门店/商品键，点预测、非负90%边际区间及名义水平。
- 整数备货：`delivery/results/future_replenishment.csv`，同样1344键，q_units为非负整数。每日1600件，采购不超过6000元，逐店品不超过raw商品上限。14日合计22400件，采购78851元。
- 历史实验、损失分项、未来每日资源与情景损失、按店/商品分配、压力方案均在`delivery/results/`。
- 场景与残差来源在`delivery/uncertainty/`；训练/评价分离、特征发布时间、原行号和内容哈希在`delivery/data/`。
- 图表及由同一块结构生成的公式图在`delivery/figures/`；claim_registry.json把论文主张映射到机器结果。

## 从原附件重跑的一条主入口

在仓库根目录`C:/Users/admin/Documents/Codex/2026-10-05/urizums-a111-main-codex-handoff-md/work/A111`运行：

```powershell
py -3.12 -X utf8 -B scripts/record_command.py --out runs/R20/execution/evidence/your-unique-rerun-record.json -- py -3.12 -X utf8 -B runs/R20/execution/code/run.py --out runs/R20/execution/your-empty-output
```

选择一个尚不存在的输出目录和命令记录路径，避免覆盖历史。入口一次从raw生成审计、全部历史实验、完整未来预测/备货、不确定性、压力表、七幅分析图、Markdown与PDF。执行代码由相对路径定位原件`runs/R20/inputs/raw/`、`input-lock.json`、`design-lock.json`和冻结设计包；它校验设计文件身份，但不消费设计smoke或其他阶段结果。迁移时须保留这一仓库相对布局及冻结锁所列文件，不能仅移动单一脚本。程序无网络或外部账号依赖。

实际Python 3.12.8；依赖为numpy 2.5.3, pandas 3.0.2, scipy 1.17.1, scikit-learn 1.8.0, matplotlib 3.10.9, reportlab 4.4.10, pypdf 6.10.2。绘图/PDF使用Windows中文字体`C:/Windows/Fonts/simhei.ttf`。当前宿主实测可用，其他平台字体路径和未指定产物格式能力未知，未承诺通用跨平台。渲染工具为实际可用Poppler pdftoppm。

```powershell
py -3.12 -X utf8 -B runs/R20/execution/code/selfcheck.py --out runs/R20/execution/your-empty-output --compare runs/R20/execution/delivery
pdftoppm -r 100 -png runs/R20/execution/your-empty-output/paper/paper.pdf runs/R20/execution/your-empty-output/paper/page
```

作者真实的两次同版本完整重跑是013（delivery）和014（clean_rerun），均exit0。最终015重新从raw核对快照、全部预测与计划键、精确采购约束、14日情景损失、32组历史指标、真实晚到及修订拒绝、所有可用性lineage，并比较全部同路径CSV（求解秒数是运行测量，明确忽略）。独立新上下文接收仍由root完成。

## 数字与概率约定

CSV以10位小数保存浮点数；点需求不用整数。区间端点在计算覆盖前统一舍入10位小数，保存和重算的包含关系一致。有限值与比较的冻结数值容差为1e-7；件量为精确整数，采购成本用原件与Decimal精确重算，不用容差放宽硬预算。83个等权场景的理论权重为1/83，CSV权重和有微小舍入误差；读入后先核验非负有限和在1e-7内，再归一化用于期望，检查器保持目标重算1e-6元容差。

## 时间、选模与适用范围

实验配置在任何性能测量前冻结。7/8启动误差池；7/22、8/5、8/19选模；9/2补充校准；9/16保留验证；所有原点18:00一次预测14天。训练需求先按available_at筛选再取最高revision；历史最终后到标签只评价，完整同日误差向量ready<=原点才校准。settlement和天气实况都未进入预测。远期未知促销由当原点最近56日训练商品平均折扣代替，并保留unknown指示。

当前方案是shared_ridge10，选择准则为历史同约束日均损失，最终83个可用同日误差向量等权构造分布。未来区间覆盖未知；历史天气无同批14日长预报、历史只有两个单日节假日。天气变量未用于预测，±10%全期需求和假期±20%是明确假设的压力代理，不能解释为估计的雨量弹性或新观测。场景保留同日96维相关；同一向量沿14日重复是压力依赖约定，不声称已识别跨日联合分布，不报告14日总损失尾部保证。求解器的最优性只针对经验分布目标；未来真实损失和收益没有真值可验。比较随机政策与点贪心同时改变分布处理与优化方式，不能把全部政策改善归因于不确定性。

## 失败、修复和版本

001起命令保存真实开始/结束、完整输出、退出码；最初阅读与建目录只有宿主记录，未事后伪造。002嵌套旧PowerShell读取出现中文乱码，后续明确UTF-8阅读恢复，原文件不变。

004初始研究误将上一窗末端未到达标签放入校准，已撤回；旧代码与output_initial保留。005修复ready边界并全量重跑。007第一版论文已逐页查看，发现标题孤立和一个单位用语误写；原report源码与页面保留。008较早完整运行的report导入在分页修正前已完成，输出仍见原问题，故不作为最后论文；013/014使用固定修正版本。010因CSV概率未归一化重算失败，012修复后发现区间浮点整数边界覆盖漂移；013/014统一端点精度重跑。所有失败输出与repair-001至004保留，不按两次错误中止，也不降低原题接收标准。

`output/`、`output_initial/`、`output_corrected/`、`final/`是过程或被替代版本，`clean_rerun/`是同版本复现；只有`delivery/`是交付。code/archive保存真实迭代源版本。manifest覆盖这些历史文件，以便检查，不能把文件存在当成结果被接受。

## 接收与停止状态

执行者完成T01–T07及作者接收/清洁重跑。T08新上下文独立接收和T09最终判定尚由root负责。evidence/selfcheck.json、visual_review.json、process_terminal.json记录实际范围和终态；模型/tokens/cost未知为null。完整manifest列全部执行域文件大小与SHA256，排除manifest自体和其生成时尚活动的018记录（该记录在工具返回后已终态，root最终冻结可覆盖）。没有外部联系、发布或后台继续任务。完成封装后停止写入等待root冻结。
