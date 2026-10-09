# 仓库资料优先级、冲突及迁移说明

## 本目录的权限性质

本次资料位于 runs/R24/research/，是尚未正式提升版本的研究层，不重置 state/checkpoint.json、state/phase-todo.json、state/continuation.json。基线资料是已有 repo 的原报告/源码，不是被本目录“替换”的历史。主线当前候选和工作前沿分别以实际冻结身份和最新 checkpoint 为准。

## 从旧文档读到不一致时按这个顺序处理

1. 当前用户最新授权和真实宿主权限/拒绝规则。
2. 当前 main 的 AGENTS.md、state/checkpoint.json、state/continuation.json、state/phase-todo.json。
3. 已冻结并有实际证据的当前候选（目前 C13）及原始失败/原报告。
4. 本 R24 研究包用于提出将来的方向及候选测试，不能改判历史。
5. 旧 README、START_HERE、CODEX_HANDOFF、docs/PROJECT_STATUS、prompts/CONTINUOUS_ITERATION 等应按原写作时间解释；不把“当前”或旧纠错上限视为今天新的用户要求。

当两份资料冲突，先确定它们是在不同历史时点说“当前”，还是实质性不一致；用原 source lock、原事件、最新 checkpoint 与用户指令裁定，不从流畅的摘要猜。

## 已知具体冲突与处理

| 文件 | 可能误导下一 Agent 的措辞/状态 | 正确范围及行动 |
| --- | --- | --- |
| README.md 根 | 多处把 C6/R07/R08-02 写成“当前” | 历史导航；最新方案见 R20 C13、R23 后续和真实 checkpoint；此文件受 release hash 锁，暂不直接编辑 |
| START_HERE.md 根 | 首段已指向 R23，而后半段又有 C9/C10、R08 阶段旧前沿 | 按时段理解，具体恢复以当期 checkpoint / 实际 host 为准 |
| CODEX_HANDOFF.md 根 | 同一文档从 R23 到 R19/R17 历史“当前”层层叠加 | 历史可核，但不能将 R19 范围当今天新授权 |
| prompts/CONTINUOUS_ITERATION.md | 提到 C5、统一最多两次修复、旧仓库/dev 发布方向 | 这是旧政策记录；后续已在 AGENTS、R17/C10 修订。不得把它直接作为当前运行提示词 |
| docs/PROJECT_STATUS.md | C5、“当前浏览器已可用”等反映早期特定宿主 | 不能由此推断本次/另一个宿主浏览器可用，也不能抵消 R14 的明确拒绝 |
| runs/R24/PLAN.md 初稿 | 原写 “CURRENT_STATUS.md” 会让执行者误以为根目录仍存在该文件 | 正确地址为 runs/R24/CURRENT_STATUS.md；本次修改候选分支内该引用 |
| state/checkpoint.json | active_phase R08、next_task_id null，R23 已定界关闭 | 这反映历史主线阻塞/旁支完成，不能因本研究包被发布就自动设 R24/R25 为 active |
| runs/R24/CURRENT_STATUS.md | 状态快照固定到先前 main commit | 只作已有主线导航，使用前重新核真实 main/PR head/CI |

## 文件/证据角色和写入目标

- 长期原件与评估回执：runs/Rxx 下已有版本；新研究不要修改已冻结路径。
- 候选方法文本：runs/R24/candidate/C14-hypothesis/forge-agent-flow/，保留 C13 原文件。
- 当前研究资料：runs/R24/research/，交接与后续研究优先从 INDEX.md 进入。
- 真正的新执行及接收证据：未来在对应新 runs/ 阶段独立目录，配以版本/hash/当期前瞻计划。
- 当前状态变更：只有协调者在核实实际工具/队列/host 后更新 state；不能由研究计划代填完成。
- 发行根文件和 artifact-manifest：受 release hash 和仓库一致性检查保护；要修改必须走专门发布升级，不为清理措辞而解除保护。

## 对文件编码和分发的最低保证

中文 Markdown 用 UTF-8；JSON/文本读取使用显式 UTF-8。需要 CSV 给 Windows Excel 等消费者时评估 UTF-8 BOM，不能把 BOM 普遍加到所有文件。ZIP/其他交接物使用 ASCII 文件名更易跨平台；若含中文成员名，实际在 Linux/Windows 解包检查。检验文内相对链接、SHA/字节、渲染出来的公式/数字/单位。未实际打包、未解压、未测试就不得声称通过。

## 下一次 research 的最短阅读路径

仓库主约束 → 当前 checkpoint/候选 → 本目录 INDEX → HISTORY_AND_EVIDENCE 对应原报告 → RESEARCH_AGENDA 一个具体假设 → PHASE_ROADMAP 的待做任务 → EVALUATION_AND_CHALLENGES/ FORWARD_AUDIT 的相关门 → HANDOFF 实际执行并存证。
