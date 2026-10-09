# Forge 研究与下一阶段研发总入口

> 状态：研发资料包 / 规划成果；不是通过的业务实验、已启动的 R25，亦非新的正式 Skill。
> 审计截点：2026-10-10；main 基线 8fedb92c310d85adf7a516adb28de69f85514aeb；研究草稿位于 PR #4 分支。
> 研究目标：让 Agent 能从新需求自主构造可执行的 Agent Flow，完成真实交付、验证、定向修复，并使经验在后续任务中可审计地复用。

## 阅读顺序与工作入口

1. [HISTORY_AND_EVIDENCE.md](HISTORY_AND_EVIDENCE.md)：历史经过、成功/失败证据、可迁移经验与不能推广的结论。
2. [WORKFLOW_RESEARCH.md](WORKFLOW_RESEARCH.md)：元工作流分层、决定机制、信息流和复用边界。
3. [RESEARCH_AGENDA.md](RESEARCH_AGENDA.md)：待证伪研究假设、检索策略、实验所需材料。
4. [PHASE_ROADMAP.md](PHASE_ROADMAP.md)：R24–R28 任务、依赖、交付、检查和进入下一阶段的条件。
5. [EVALUATION_AND_CHALLENGES.md](EVALUATION_AND_CHALLENGES.md)：前瞻测试矩阵、对照设计和评价口径。
6. [FORWARD_AUDIT.md](FORWARD_AUDIT.md)：每阶段开始/中间/结束的前瞻审计、风险与决策门。
7. [HANDOFF.md](HANDOFF.md)：新会话/新 Agent 可直接执行的交接指令。
8. [CHANGE_AND_SOURCE_MAP.md](CHANGE_AND_SOURCE_MAP.md)：原仓库文档的优先级、避免误用过期内容、改动边界。

## 当前必须正确理解的五项状态

- 项目长期目标仍 active；原 checkpoint 主阶段为 R08 且历史 R08-03/R08-next 仍 blocked。R23 定界支线已经结束，不代表所有历史门通过。
- C13 是已保留的九 Markdown 方法候选；方法内容不等于执行控制器、内置验证程序或全面行为通过。
- C14 在 runs/R24/candidate/C14-hypothesis 是文本实验候选。R24-01 的文本已形成，但完整必要性静态审查和新上下文 C13/C14 行为对照尚未完成。
- PR #4 曾因更动根目录锁定文档及漏登记新根文件导致 CI 失败；问题已针对性回滚并重新检查。CI 状态必须按具体提交查询，不继承此前绿色。
- 本研究包的编写与提交是真实文档研究工作，不等于 R24-03 或未来 R25 的执行者已经启动。

## 用法

面对新任务，先按本目录证据卡判断已证明什么；从研究假设中选一个有信息增益的问题，核对真实宿主能力与许可，再按阶段门冻结原件、验收及研究条件。产出后回填证据与限度。只有真实执行/审查所支持的项目才可变更为 accepted。

涉及旧根 README、旧持续迭代提示词和 AGENTS 的冲突，以当前用户授权、真实 checkpoint、冻结历史及最新有效候选身份为准；不要从旧文档里的“当前”“必须两次纠错”推导全局政策。

## 与原库的关系

本目录只作为 runs/R24/ 内的研究附件和今后的决策入口；保持源锁、发行清单、历史失败/原始报告和根目录三份冻结文件不变。将来如需正式变更根文档，须按仓库现有发布清单和全部必要验证进行独立提交；不能通过修改哈希锁掩盖变动。
