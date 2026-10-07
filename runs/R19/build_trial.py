"""Prepare a prospective four-level trial; never modify prior candidates/results."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'runs/R19'
OLD = ROOT / 'runs/R17/candidate/C10/forge-agent-flow'
NEW = HERE / 'candidate/C11/forge-agent-flow'
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def record(path):
    data = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

shutil.copytree(OLD, NEW)
modeling = NEW / 'references/modeling.md'
text = modeling.read_text(encoding='utf-8')
text = text.replace('## Interpret prompt detail honestly', '''## Design the evidence needed by the final paper

A request to complete mathematical modeling includes a usable scientific argument
even when the user does not spell out research, experiments or review. Derive
those duties from the actual problem and intended conclusions, not prompt length.
Build the reusable workflow so another executor can perform them without the
designer's private reasoning. Keep definitions, data availability, constraint
interpretations and unresolved decisions visible at each receiving interface.

Before solving, map each requested answer to a proposed claim, the computation or
experiment that could support it, a counterexample that would refute it, and the
paper section consuming the evidence. This map evolves with results; it is not a
prefabricated answer. Cover all original questions before optional sophistication.
For a multiobjective task state how alternatives are compared and tradeoffs shown;
do not quietly replace the original objectives with a convenient weighted sum.

After the first feasible result identify the material weakness that could change
the answer: an omitted constraint, loose bound, unsupported assumption, poor
baseline, unstable estimate or unexplained discrepancy. Choose a targeted next
experiment and its receiving check. If no improvement is supported, report the
tradeoff or limitation. A smoke pass permits continued work; it does not establish
that a first candidate or its paper is sufficient for final delivery.

Treat paper production as a consumer of checked evidence. A complete paper needs
a stand-alone account of the problem, necessary assumptions with consequences,
defined quantities/equations, reproducible methods, actual results answering every
question, validation, interpretation and limits. Its abstract should report the
supported findings; figures/tables should resolve a question, with units and
sources, rather than decorate a model-name narrative. Do not fabricate novelty,
citations, convergence, optimality or experiments. An unproved optimum remains a
feasible candidate with an appropriate bound or explicitly unknown gap.

Include a substantive receiving review before delivery: can a fresh reader
recover the original question, recompute critical results from raw inputs, find
the evidence for each conclusion and identify conditions where it fails? Separate
fatal mathematical or evidential defects from optional editorial polish. Repair
the former with new checked results before strengthening the narrative. The
workflow should support this review without outsourcing its judgment to author
self-checks or promising a competition outcome.

## Interpret prompt detail honestly''')
modeling.write_text(text, encoding='utf-8')
design = NEW / 'references/workflow-design.md'
text = design.read_text(encoding='utf-8').replace('Define the receiving interface before delegating a step:', '''When a reusable workflow will be handed to a different context, include the
decision criteria and evidence needed for its intended final artifact, not only
stage names. Check that the executor can begin from raw inputs, branch on results,
and know when substantive delivery requirements are met without hidden designer
knowledge. Sparse user detail does not remove those derived domain duties.

Define the receiving interface before delegating a step:''')
design.write_text(text, encoding='utf-8')
write(HERE/'candidate/C11-lock.json', dict(schema='forge-revision-lock/1', revision='C11', parent='C10', files=[record(p) for p in sorted(NEW.rglob('*')) if p.is_file()], limits='Frozen candidate identity only; all four full-workflow behavior trials are pending.'))

common = '''主要针对国内两个比赛：

1. 全国大学生数学建模竞赛（国赛）
2. MathorCup 数学应用挑战赛（妈妈杯）

目前下一场主要对阵 MathorCup。
'''
levels = {
1: common+'''
你的任务是帮助我们完成数学建模竞赛，包括分析题目、建立模型、求解问题、生成图表、分析结果和完成论文。
''',
2: '''主要针对国内两个比赛：

1. 全国大学生数学建模竞赛（国赛）
2. MathorCup 数学应用挑战赛（妈妈杯）

目前下一场主要对阵 MathorCup。

你的任务是帮助我们完成数学建模竞赛，包括分析题目、建立模型、求解问题、生成图表、分析结果和完成论文。

目标不是单纯得到一个答案，而是完成一份具有竞赛竞争力的完整解决方案。

需要兼顾：

- 题目理解是否正确
- 模型是否合理
- 求解结果是否可靠
- 图表是否有效
- 结论是否能够解释
- 论文是否完整、清晰
- 模型、代码、结果和论文是否一致

当前优先针对 MathorCup 进行准备。
''',
3: common+'''
你的任务是帮助我们完成数学建模竞赛，包括分析题目、建立模型、求解问题、生成图表、分析结果和完成论文。

完成题目时，不要直接看到关键词就套模型。

先理解：

- 题目真正要求解决什么
- 每一问的输入和输出是什么
- 有哪些已知条件
- 有哪些约束条件
- 各小问之间有什么联系
- 附件数据能够提供什么信息
- 最终需要给出什么结果

然后再考虑：

问题分析
→ 数据分析
→ 数学抽象
→ 模型选择
→ 模型求解
→ 结果验证
→ 结论分析
→ 论文整理

如果存在多种合理方法，应进行比较，而不是直接确定第一个想到的模型。
''',
4: common+'''
你的任务是帮助我们完成数学建模竞赛，包括分析题目、建立模型、求解问题、生成图表、分析结果和完成论文。

拿到题目后，首先完整拆解问题和附件数据。

对于每一问，需要明确：

- 问题目标
- 输入变量
- 输出变量
- 决策变量
- 约束条件
- 评价标准
- 与其他问题的关系

不要为了显得高级而使用复杂模型。

重要问题应尽量考虑：

1. 一个简单、可靠的 baseline
2. 一个经典数学建模方法
3. 一个可能效果更好的改进方法

比较不同方案的：

- 合理性
- 准确性
- 稳定性
- 可解释性
- 计算成本
- 是否真正解决题目要求

模型得到结果以后，还要检查结果是否合理，而不是得到数字以后直接写论文。
'''}
for level, prompt in levels.items():
    write(HERE/f'inputs/L{level}.md', prompt)
inputs = [p for p in (ROOT/'runs/R16/source/official_extracted/D_corrected').iterdir() if p.is_file()]
raw = HERE/'inputs/raw'
raw.mkdir(parents=True)
for p in inputs:
    shutil.copyfile(p, raw/p.name)
write(HERE/'inputs/raw-lock.json', dict(schema='forge-raw-input-lock/1', source='Official corrected 2026 MathorCup D bytes acquired in R16; excludes source-stage recommendations, summaries, old solutions, participant papers and verdicts.', files=[record(p) for p in sorted(raw.iterdir())]))
write(HERE/'acceptance.json', dict(schema='forge-four-level-transfer-trial/1', frozen_at=datetime.now(timezone.utc).isoformat(), candidate='C11', mandatory=[
    dict(id='a1',assertion='Every original subquestion including the technical report and Attachment2 is answered with actual artifacts; problem constraints and objective definitions are respected or consequential ambiguity explicitly bounded.'),
    dict(id='a2',assertion='Mathematics, assumptions, units, data treatments and parameter provenance justify the computed answer; comparisons are fair and complexity is proportionate.'),
    dict(id='a3',assertion='Fresh reviewer can rerun code from official raw data and independently recompute critical feasibility/objectives and paper values; no hardcoded answer or fabricated execution.'),
    dict(id='a4',assertion='Task-relevant substantive checks, meaningful boundary/failure behavior, material uncertainty and method comparison have actual evidence; bounds/heuristic limits replace unsupported optimality claims.'),
    dict(id='a5',assertion='Complete stand-alone Chinese paper with coherent question-analysis-model-result-validation-interpretation argument, meaningful figures/tables, source attribution and restrained conclusions; key claims agree with raw data/code/results.'),
    dict(id='a6',assertion='Generated workflow is usable by a new executor without designer intervention; receiving checks and correction routes preserve original duties, meaningful smoke and full acceptance are separate, actual actor roles and all failures are recorded.')
], quality_diagnosis=['problem fidelity','mathematical justification','empirical sufficiency and fair alternatives','reproduction and result-to-paper traceability','clarity and completeness of scientific argument','workflow transferability and autonomous gap resolution'], quality_rule='Use evidence-backed achieved/partial/missing judgments and material deficiencies, not guessed competition scores or prizes. Mandatory correctness and delivery defects cannot be averaged away. Optional sophistication is not a universal model-count/page-count quota.', blind_rule='Builders/executors do not receive this external acceptance document, old trial outputs or other-level inputs. They receive exact level input, same skill and official raw data plus neutral task logistics. Reviewers receive original sources, that level request, generated workflow and frozen outputs with no root expected answer/diagnosis/other verdict. Re-review after feedback is explicitly informed.', interpretation='One case per level and uncontrolled sampling randomness; descriptive behavior observations only. Historical ordinary contest practice does not establish October big-data competition performance. No award prediction.', resources='Same local available Windows Python3.12 scientific libraries and CPU, no installs, network/solution search prohibited. No universal two-recovery stop. Preserve attempts; use evidence-backed progress with actual host constraints; report unavailable provider model/token/cost as null. Individual numerical experiments have declared task-relevant time/scale limits; no invented whole-task short deadline.'))
write(HERE/'PLAN.md', '''# R19：Level 1–4 的可转交工作流与完整论文试验

用户授权范围：制作四层工作流，按L1→L2→L3→L4分别执行至论文，并回查源头设计。5–8不测试。能力要求落实到决策、证据和接收检查；不以奖项或虚构评分替代质量。

每层分别使用新上下文构建者、另一新上下文执行者、另一独立审查者。执行者可以按本层工作流组织实质子任务，但不能把角色名当真实分工。构建者只见该层原始文本、同一C11与同一官方原始附件；没有共享高信息验收提示。外部统一验收预先冻结，由审查者执行。L2–L4不见先前层方案/结果/反馈。首轮与获知审查结果后的修订分开。

输入是用户完整Level1–4（仅排版规范化，并非累加拼接或摘要）、官方2026修订D题PDF/DOCX/XLSX。独立离线试解，不读取既有论文、题解或R16/R18求解成果。本轮是明确授权的新前瞻试验，不替换或追认R14/R16旧实验，旧失败/锁/计数不动。

C11保留C10纯文档结构，增强从论文结论倒推证据与新上下文可执行性；仅源身份已冻结，完整行为验收待实测。算法、实验、论文属于runs中的测试产物，不进入技能包。不安装个人skill、不提交比赛。

依次执行：冻结→L1构建/执行/审查/必要修订→L2→L3→L4→独立整合诊断→源头修订（若证据支持，另存版本并新测受影响行为）→启动有实际意义的下一阶段首步。单层若存在实质缺陷，保留未通过判定；不降低标准，不通过换样本、换执行者或遮蔽失败来通过。
''')
write(HERE/'TODO.md', '''# R19 TODO

- [x] 冻结用户新范围、C11、四份原层级输入、同一官方原始数据和统一独立验收。
- [ ] L1：工作流构建 → 新上下文执行到完整论文 → 独立实质审查 → 必要纠正与复核。
- [ ] L2：同等条件，顺序执行；不接触L1成果。
- [ ] L3：同等条件，顺序执行；不接触前层成果。
- [ ] L4：同等条件，顺序执行；不接触前层成果。
- [ ] 汇总逐层实际分工、题面覆盖、数值可靠性、验证深度、论文一致性和工作流迁移缺口。
- [ ] 按实测证据修订源头设计并验证受影响行为；没有证据时不宣布技能升级有效。
- [ ] 启动下一阶段任务：依赖完整四层诊断，保存明确计划与真实首步；未满足则保持待办。
''')
write(HERE/'before/history-lock.json', dict(files=[record(ROOT/p) for p in ['state/continuation.json','state/project-todo.json','state/phase-todo.json','state/checkpoint.json','CODEX_HANDOFF.md','START_HERE.md','runs/R17/candidate/C10-lock.json','runs/R14/math-comparison.json']]))
print(json.dumps(dict(candidate='C11', markdown_files=len(list(NEW.rglob('*.md'))), levels=list(levels), raw_files=len(inputs), state='prepared_not_executed')))
