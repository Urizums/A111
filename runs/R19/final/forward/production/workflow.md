# 四件固定方向装箱：可交接执行方法

本方法依据原 request.md、problem.md、raw.json 及 input-lock.json；输入以原件为准，不能由结果标签更改类别、质量或尺寸。目标为字典序 (车辆数, 总费用)，交付实际坐标、可运行程序、结果核验、完整中文论文 PDF 与可编辑 Markdown。当前仅一位生产者兼任设计、计算与自检角色；这些角色不是独立验收。新消费者应从原始输入开始判断，不能把本文状态视为正确性证据。

## 简报与授权
全部四件刚性箱固定方向；车内 2.4×1.2×3.2 m，顶部间隙 0.1 m、载重 500 kg；standard 累计外载/顶面面积≤150 kg/m²，fragile 不承载且只能落地或放在 standard 上。支撑必须单件完整覆盖底面并等高接触；层间外载递归传递。资源为已有 Python 3.12、标准库及本机 PDF 库与字体；离线、不安装、不提交、不改冻结输入。不设任务虚构期限；遇实际权限/材料/资源阻断时保留产物和缺口。一般错误不形成通用两次停止规则。

## 蓝图与接收接口
|触发/步骤|原输入|决策与操作|责任角色|输出和下游|接收检查|失败与恢复|
|---|---|---|---|---|---|---|
|开始|原 request、problem、raw、lock|核对文件摘要、字段、单位、身份与有限数值|设计/生产者|本方法、raw 快照、input_audit.json → 建模|摘要一致；所有 item_ids 唯一；类别和正数合法|指出冲突、不覆盖原件；仅修程序或报告缺失|
|模型就绪|审核数据、原约束|定义分配、坐标、支撑与传载；选择可证明完整的方法|建模者|paper.md 模型与 solve.py → 求解|每个强约束有公式和执行接收检查|任何遗漏回到模型；不能以复杂模型数替代正确性|
|首个贯通路径|raw.json|枚举合法支撑链、车辆分组、生成坐标；计算界|求解者|solution.json → 核验与论文|ID全集、坐标/几何、载重、顶部间隙、原身份、递归外载、目标重算|保留原输出；定位 violated constraint，修相关逻辑|
|烟雾与边界|真实解、三层传载反例|运行 verify.py；将真实输入身份与输出绑定；注入三层 160 kg 外载反例|同一生产者自检|checks.json、test_results.json → 完整自检|合法解接收；不合法叠放被实际拒绝|反例不触发就修核验，保留失败；其余完整检查仍须执行|
|实质研究|首解与已知短板|与全落地基线比较；载荷/载重临界值敏感性；给出下界或完整枚举证据|建模者|experiments.json、paper.md → 编辑|同一原件、参数修改明示；最优性不超出证明|不声称无证明的全局性；对不支持输入拒绝而非伪装解|
|论文消费|核验结果、方法、输入|完整中文论证，表格与结果逐项追溯；生成 PDF|作者|paper.md、paper.pdf → 文件读者|中文正文涵盖问题/模型/方法/结果/证明/验证/解释/局限/复现|实质歧义回到原式/原数据；纠错记录留在结果|
|最终自检|所有成果、原件|干净复跑；逐页实际渲染检查；冻结 SHA256 清单|生产者|reproduction/、pdf_review.json、result.json、manifest.json → 新消费者|复跑语义相同；所有页可读；清单相对 A111 根可复算|修复后重跑受影响检查；自检完成不升级为独立验收|
|外部接收|原件、上述冻结产物|按原问题重新判断所有必需结论与格式|新上下文消费者（另行提供）|消费者自己的验收结论|执行下面接口；每个否决绑定原约束和实际证据|必要失败交回作者；可选风格建议不可虚构为强制要求|

## 在实现前冻结的关卡
- 预检：读取输入锁并逐个实际计算摘要；检查 Python/必要 PDF 库、渲染器与中文字体存在。预检只表示能尝试。
- 烟雾：原始数据→求解→核验→论文结果表真实贯通；核验一例累计外载超限。贯通不替代全体约束或独立验收。
- 完整作者自检：数值必须有限；身份/类别/尺寸/质量来自 raw；全集恰好一次；每车边界与间隙、六向不重叠、载重、支撑接触/覆盖、fragile 规则、递归累计外载和目标都重算。保留构造错误与修改；已完成命令不能直接证明模型。
- 研究：原实例至少提供原问题可行解及界/最优性解释；针对累计传载关键弱点做反例；基线、临界参数实验只支持其明示范围。无需制造预测留出、更多模型、奖项分数。
- 交付：PDF逐页渲染并实际看图；可编辑中文源文；程序能从 raw 重算；重跑结果和论文关键数值一致；独立验收状态明确待另行执行。

## 新消费者可直接执行
所有命令在 production 目录运行：

```powershell
python solve.py --input ../inputs/raw.json --output consumer-solution.json
python verify.py --input ../inputs/raw.json --solution consumer-solution.json --output consumer-checks.json
python tests.py --input ../inputs/raw.json --solution consumer-solution.json --output consumer-tests.json
python experiments.py --input ../inputs/raw.json --output consumer-experiments.json
```

消费者可将输出放在其独立写目录（参数均可为绝对路径）；不要写冻结 inputs/candidate。只依赖 Python 标准库的前三个计算程序；paper PDF 的生成另外需要本机已有 reportlab、pypdf 和中文字体。PDF 的人工查看不依赖生成环境。

`solution.json` 必需字段：schema、source_sha256、vehicle_type_id、placements（item_id、vehicle_id、x_m、y_m、z_m、support_id）、objective（vehicle_count、total_cost_CNY）、optimality、search。车辆ID是方案内实际实例，vehicle_type_id 必须与原车类型一致；item_id 定义身份。support_id=null 表示地面，否则必须与核验发现的单件完整支撑者一致。输出不附带可替换原件身份的类别参数。求解器主动拒绝非同尺寸物件、多车辆类型等超出其完整搜索适用范围的输入；核验器可按原尺寸检查一般单车类型三维解。

`checks.json`：valid、errors、per_vehicle、per_item、recomputed_objective；核验失败退出码1，不把 NaN 视为合法。`test_results.json`：每个真实修改的 case 的 accepted、errors、expected_acceptance、assertion_passed；反例只存在测试输出，原输入不改。`experiments.json`：每个参数取值、实际解/目标/核验与基线；参数实验不是原材料被修正。

论文以原件参数和 solution 数字为证据。接收者应自行检查模型与程序一致、下界逻辑成立、递归承载用的是所有后代质量、同高相邻未当支撑、原身份不可被输出劫持。至少打开全部 PDF 页面并核对关键表格、数值、公式和声明范围，检查完整中文 Markdown 可编辑。自行重算 manifest；作者 result.json 仅提供做过什么，不提供接收真值。

## 推进与停止
出现工具错误先保留真实回执，再按已有证据换正确路径；出现约束缺陷保存旧产物后仅修受影响接口；研究实验应回答会改变结论的具体疑问。干净复跑和最终格式检查完成后冻结清单，待新消费者验收。没有下一步权限或材料则报告实际阻断，不调低检查。实际 provider/model/token/cost 遥测未知则 null。当前流程不授权联网、安装、开新线程、启动子代理或提交论文。
