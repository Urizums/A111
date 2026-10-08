# L3 修订交付接收入口

本包是同一 L3 作者对首次首审具体缺陷的知情修复：从相同的已核验数值输出重写中文论文与企业报告，修复 PDF 的面积、体积、负幂和平方复杂度，并追加可实测的调用输出保留及进程接续方式。模型、数值代码、正式配置、原数据和方案坐标没有改变。本轮不新增全局最优证明，不重复无影响的历史求解。

首次独立判定保持 a1–a4 在声明范围 pass、a5 fail、a6 partial；当前材料仅经作者自检，等待同一审查者知情复审。修复完成不意味着首次判定被改写或全部门已经独立通过。

## 交付与证据路径

所有相对路径以本 README 所在的 execution-v2 为基准。完整接收必须同时保留同层相邻的冻结 `../execution/` 和本修订域；单独拷走新 PDF 不能替代完整计算证据。

| 消费目的 | 实际路径 | 身份与范围 |
| --- | --- | --- |
| 阅读论文 | paper.md、paper.pdf | 修订正文，11页；同一原模型/数值，全文科学与论证检查 |
| 企业实施报告 | technical_report.md、technical_report.pdf | 3页；条件、方案、参数取舍与操作限制 |
| 数值算法、完整数据和坐标 | ../execution/src/、data/、plans/ | 原冻结程序，六正式任务，每件坐标、配置、指标、自检 |
| 算法比较和参数原证据 | ../execution/experiments/、column_milp/、deep_columns/、local_search/、sensitivity/ | 历史已计算数据，包含未改善与失败记录 |
| 原题字段及需求—结果连接 | ../execution/data/raw_audit.json、evidence.csv | 官方原文件身份与字段定位、结果追溯 |
| 六正式任务干净重算 | ../execution/replay/fresh3/receipt.json | 当前最终数值源码/配置/输入哈希绑定，六任务主指标/库存/坐标一致 |
| 图表及其数据 | figures/ | 原PNG与CSV逐字节副本，无重画或数值变化 |
| 修订依据 | ../review/initial/report.md、result.json；../review/initial-lock.json；../REPAIR_FOLLOWUP.md | 首次判定与知情修复要求，只读 |
| 数值/源码/原件最终绑定 | logs/final_bindings.json、logs/source_bindings.json | 原3722个payload复核、新来源与当前代码身份 |
| 全文修改理由 | logs/editorial_changes.json、reader_feedback_changes.json、两份editorial.diff、editorial_coverage.json | 原句/改句/理由/证据、全文复核范围；条数不作质量证明 |
| 最终消费者PDF核查 | qa/pdf_semantic_checks.json、visual_review.json、scientific_editorial_review.json、markdown_semantic_checks.json | 全750显示单元，40个科学源记号，14页实际视觉检查，原表/数值语义复核 |
| 逐页及科学记号图像 | qa/pdf/paper/、qa/pdf/technical_report/ | 全页图、提取文本、46个可重叠科学局部及其接触表 |
| 前瞻日志机制与实测 | src/receipts.py、receipt_cli.py；qa/prospective_receipt_final.json、prospective_receipt_checks.json；attempts/ | 唯一目录、PID/创建时间、原stdout/stderr、退出状态、活动进程阻止后续启动 |
| 资源/失败/接续 | logs/resources.json、repair_failures.json、tool_invocations.json；TODO.md、checkpoint.json | 原历史限制与新追加资源分开 |
| 机器接收及字节清单 | result.json、manifest.json | 组合包入口、检查范围、未闭合事项；manifest不包含自身 |

`qa/draft-before-reader-feedback/` 和 `qa/reader-feedback-before-final-wording/` 是保留的中间稿图像/PDF，不用于最终消费。其历史语义快照中的旧绝对图像路径已随目录归档移位，当前权威核查只用 `qa/pdf/` 和 `qa/pdf_semantic_checks.json`。两份最终 PDF 始终以本域根路径为准。

## 数值复现范围与安全写域

原 `fresh3` 实际重新计算六任务，不预读正式 placements 作为答案，源码、六配置和输入哈希与当前原冻结程序一致。它覆盖当前论文使用的正式主数值和逐件坐标；不生成全部历史网格、图表或本次修订 PDF。图表沿用同一原输出的逐字节副本，本轮 PDF 另经新字体导出及最终检查。没有把本轮3次小实例收据测试称为六任务重跑，也没有算法 ZIP 的重跑声明。

原程序的可运行入口为 `../execution/src/solver.py`、`checker.py`、`column_milp.py` 和 `reproduce.py` 等。通用 JSON 格式见原 `../execution/README.md`；当前消费者入口在本域 `src/receipt_cli.py`。它调用原字节程序，强制为输出创建 `execution-v2/attempts/<类型>-<唯一ID>/output`，不允许覆盖先前输出。原代码以 `-B` 运行，不产生原域 pycache。

对本已冻结接收包，先将完整的相邻 `execution/` 与 `execution-v2/` 复制到一个消费者独立工作目录再执行；运行写入的是复制包的 `execution-v2/attempts/`，不是原冻结证据。只读独立复审也可在其授权的新审查域直接给原 `reproduce.py --out` 指定绝对新目录，需自有收据与进程控制。生产者本轮唯一写域仍是本 `execution-v2/`。

在复制包内，以其 `execution-v2` 为当前目录，使用现有 Python/科学库，不安装依赖：

```powershell
py -3.12 -X utf8 -B src/receipt_cli.py --mode inspect
py -3.12 -X utf8 -B src/receipt_cli.py --mode replay
py -3.12 -X utf8 -B src/receipt_cli.py --mode solver --task Q1-S1 --input <新实例JSON的绝对路径>
```

`replay` 一次重求正式六任务（包含T1模板MILP）；`solver` 是通用构造而非保证同最终库改进的任意配置调用。子调用上限120秒、注册的活动子进程上限1。实际小实例验证只检验收据链路，不评估主实例搜索质量。单独坐标检查要给原checker指定新输出目录，因为checker会在该目录写validation.json；不要给它原冻结plans目录。

`inspect` 按PID和创建时间一起核对活跃进程；活跃或身份不可查时禁止启动后续调用。监视器重启且子进程已退出时，`reconcile` 保留原流文件，无法取得的退出码保持null，再解除活动登记。真正的监视器崩溃后退出分支没有做崩溃实验；本轮实测了新监视器读取仍活跃的同一进程并阻止后续启动。launch_guard存在时需核对其拥有者/收据，不能未经诊断删除。此机制是协作与输出约束，不是操作系统隔离。

## PDF导出与语言检查

微软雅黑嵌入字体覆盖中文、²、³；Segoe UI Symbol补齐负指数的⁻。每个显示字符在生成前查字形，缺字直接报错。导出程序和字体文件哈希见logs/pdf_export.json。全正文、公式每行、表格每格与最终PDF提取文本去空白精确对照；关键科学记号还实际放大检查，防止仅凭文本提取忽略读者看到的语义。

若需在复制包重新生成文字/PDF，可依次运行src/revise_manuscripts.py、reader_edit.py、export_pdf.py；前两步完整重建最终稿。export_pdf只写该复制域，不调用数值求解器。check_pdf.py默认要求全新qa/pdf目录，以防覆写核查历史；在独立副本先明确归档原qa/pdf及语义核查文件，再运行。最终PDF字节可能因生成时间元数据不同，数值及Unicode语义才是重放比较目标。微软雅黑/Segoe字体及现有ReportLab、PyMuPDF/Pillow需要可用；具体字形身份已绑定，不自动安装或找替代字体。

论文与报告统一“空间利用率/载重利用率”和“承载面密度”；在变量/支撑约束之后解释目标与算法，对每幅图交代用途，对每组场景区分观察、作用路径和限制。费用候选只在声明有限池中最小；库内占地最优不等于原三维最优；单车非支配点不等于完整Pareto前沿；增加载重无改善是本批搜索观察。重点改写的数值、单位、上标、限定词已与原记录及最终PDF核对。科学表达质量检查是作者自检，不能代替独立复审。

## 首次不可补历史与本轮资源

原声明3600秒窗口，已耗1929.69895秒；原2215次求解调用计数含两次预设不可装失败。原单求解进程目标1实际峰值2，两次偏离（一次最小重叠约1.84秒），不追认符合。最初三个CLI的原PID/stdout被覆写，保持null；原全部峰值内存未知null。原完整失败及未改善记录继续位于原logs/和研究目录，未清零。本轮工具修复、实质表达修正、正常导出迭代和预设负测试分别记录。

本轮另声明2400秒窗口、单子调用120秒、单注册子进程、1200MB内存目标（非OS强制），追加资源与原窗口分开。9个实际子进程含3次同一原程序小实例、3次坐标检查和3次流程探针；另有1次启动前阻止、1次预设缺失程序启动失败。2个负流程探针分别保留exit7与超时输出。原CLI未知没有通过新调用补造；新调用的PID/stdout完整，不表示原历史获得恢复。全程离线，没有安装、上传或投稿；实际模型/token/cost不可观测，保持null。

未闭合：原三维全局最优与完整Pareto、多支持/动态工程与装卸可达性、官方易碎朝向解释、附件2完整批次业务输入、比赛提交合规、不可补历史及本修订独立知情复审。完整终态以result.json及checkpoint为准。
