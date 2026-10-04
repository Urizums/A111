# 在新上下文接续

请从这个 checkout 的 AGENTS.md、START_HERE.md 和 state/checkpoint.json 开始。用户目标是持续研发、扩展和实际效果验证；交付 PR 不终止长期目标。运行 verify_handoff.py 与 continuation.py --root . next，读取所选任务的原材料、验收、写域和预算，从当前前沿继续，不重开历史阶段。

使用 START_HERE.md 指定并锁定的 C5 候选。先核对 coordinator lease、原生未决任务及 state/publication-gate.json，不并发修改共享状态。简单一次性任务直接交付，完整系统走 program，明确的复用 agent flow 才走 package。Root 写核心和 skill；Luna 做研究、脚手架与独立验证。只使用真实可用工具，保留 first failure、所有修正和未知指标，不把 preflight 当语义验收。

完成下一就绪项并检查实际效果，然后真正执行其后续任务的首步、保存命令返回，更新双队列和阶段。连续推进能力队列与不同领域/形态/复杂度的挑战队列；阻塞只影响相关分支，不等用户再发 continue。详情见 CONTINUOUS_ITERATION.md。停止会话时留下可复核 checkpoint，准确说明是否存在实际后台接续。

全部必需验收、冒烟以及新问题修复复测通过后才可提交或推送 dev；禁止单批发布、跳过独立验收、重置失败额度。上游 PR 自动随 dev 更新，不合并上游。没有可用执行宿主或状态未变化时保持安静，保留恢复条件，不宣称后台代码在持续执行。
