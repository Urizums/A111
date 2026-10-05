# 在新上下文接续

请从 main 的 CODEX_HANDOFF.md、AGENTS.md、START_HERE.md 和 state/checkpoint.json 开始。用户目标是持续研发、扩展和实际效果验证；交付 PR 不终止长期目标。运行 verify_handoff.py 与 continuation.py --root . next，读取所选任务的原材料、验收、写域和预算，从 R08-02 当前前沿继续，不重开历史阶段，也不等待延期 ZCode 支线。

使用 START_HERE.md 指定并锁定的 C6 基线，保存新的 C7 候选。先核对 coordinator lease、原生未决任务及 state/publication-gate.json，不并发修改共享状态。简单一次性任务直接交付，完整系统走 program，明确的复用 agent flow 才走 package。Codex Root 写核心和 skill；可用 Luna 做研究、脚手架与独立验证，否则使用真实可用的新上下文验证者并记录模型。只使用真实可用工具，保留 first failure、所有修正和未知指标，不把 preflight 当语义验收。

完成下一就绪项并检查实际效果，然后真正执行其后续任务的首步、保存命令返回，更新双队列和阶段。连续推进能力队列与不同领域/形态/复杂度的挑战队列；阻塞只影响相关分支，不等用户再发 continue。详情见 CONTINUOUS_ITERATION.md。停止会话时留下可复核 checkpoint，准确说明是否存在实际后台接续。

当前用户已授权上传和合并应合并的开发成果，main 是接续基线。提交可审查的代码、原始证据与 checkpoint，按实际改动运行相关检查；开发合并不改判原完整产品门槛，不跳过所声称的独立验收，不重置失败额度。完整产品发布仍须满足其原验收。没有可用执行宿主或状态未变化时保留恢复条件，不宣称后台代码在持续执行。
