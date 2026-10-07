# L1设计与接续TODO

目标：交付可转交新上下文执行原D题至完整中文论文的工作流。当前只完成设计；所有模型、求解、实验、成稿门槛未执行。协作写域仅本`design/`；运行写域须在下一任务明确分配。本表不修改共享state，不是后台调度。

| task_id | 依赖 | owner | 写域 | 验收 | 状态 | 实际证据 | 阻塞/下一动作 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D00 | 无 | 设计作者 | design/sources | 原输入与指定skill条件参考阅读，原材料身份/位置可核对 | done | raw-transcription.json；source-map.md；PDF三页视觉核对图 | 无；进入D01 |
| D01 | D00 | 设计作者 | design/workflow.md | 各原问题到决策/接口/检查/失败路径，缺口和权限清楚 | done | workflow.md需求矩阵、算法及G0–G6；不是已运行证明 | 无；进入D02 |
| D02 | D01 | 设计作者 | design/handoff.md、TODO.md、result.json | 新上下文可从原材料启动，未执行与真实限制不伪装 | done | handoff.md的E00真实命令及路径；result.json状态字段 | 无；设计交付完成 |
| E00 | 设计交接；执行任务授权写域 | 新执行者 | 新分配RUN | 核对哈希、读通原件、记录真实能力/运行目录 | not_started | 无，handoff中命令未由执行者运行 | 等待新的执行任务；首项是只读核对 |
| E01 | E00 | 新执行者 | RUN/inputs、model | 规范字段/单位/数量、假设逐源接收 | not_started | 无 | 按workflow第3节实施 |
| E02 | E01 | 新执行者 | RUN/model、src | 模型和独立检查器覆盖全部约束/任务 | not_started | 无 | 冻结容差、支撑和传载定义 |
| E03 | E02 | 新执行者 | RUN/src、results、figures | 真实三类别小链与非法边界拒收 | not_started | 无 | 不能以数据读取替代smoke |
| E04 | E03 | 新执行者 | RUN/results | Q1S两车型、Q1F两车型、Q2N、Q2C全规模基线及可行检查 | not_started | 无 | 不缩小附件1数量冒充完整结果 |
| E05 | E04 | 新执行者 | RUN/results、configs、logs | 同条件改进、权衡、上下界和差距状态 | not_started | 无 | 改进由实际瓶颈驱动，保留失败 |
| E06 | E05 | 新执行者 | RUN/results、figures | Q3参数和性能真实实验；附件2分支诚实 | not_started | 无 | 附件2缺字段不阻塞主任务 |
| E07 | E06 | 接收者/获授权新上下文 | RUN/review | 干净复现、逐件/指标/图表可追溯 | not_started | 无 | 独立不可用则标作者自检 |
| E08 | E07 | 新执行者 | RUN/paper | 全中文论文、管理技术报告，无关键占位、数值可追溯 | not_started | 无 | 禁止把待验证变成结果 |
| E09 | E08 | 协调/接收者 | RUN/paper、review | 程序附件、可读成稿、全要求判定和限制 | not_started | 无 | 不自行竞赛提交 |
| TRANSITION | D00–D02 | 根协调者/接收者 | 新执行任务的写域 | **启动下一阶段任务**；计划路径`workflow.md`，首项`E00`，须实际启动证据 | cancelled_for_design_scope | 无E00启动证据；本任务目标是构建，不授权作者求解 | 设计目标已完成；由根协调者在另行执行任务中启动，不能追认done |

checkpoint：原件读取与转录已完成；所有原题数值答案、求解器运行、smoke、全题验收、独立验收、复现和论文为not_run。无未决调用。真实工具错误0；无研究/纠错调用（未求解）。模型/token/cost未获遥测，均null。下一可执行动作是接收者按handoff启动E00。真实限制详见result.json。
