# Fresh-context continuation acceptance

Original user goal: continue developing and validating Agent Forge across useful
capabilities and varied real tasks; deliver code and evidence to the fork dev
branch without stopping the long-term project when a PR is delivered. Original
review requirements are in runs/R00/review-comments.json in the assigned checkout.

You have no prior chat context. Your isolated repository is
/workspace/A111/runs/R02/handoff/worker/checkout.
Start from its AGENTS.md and START_HERE.md, then choose the next ready task from
its actual state. Finish that task from the original requirements/material and
actually execute the first step of its successor without asking the user to
continue. This is a bounded handoff test: return after those actions, so Root can
resume the successor. Do not finish additional tasks or edit core/skill logic.

You may create benign command-worker crash/recovery validation scripts and
outputs for the selected task. You may update only this isolated checkout's
state/continuation.json, state/phase-todo.json, state/checkpoint.json and new
state/history entries using the continuation controller. Those local derived
states are the subject of this handoff test; the outer bridge's request/control
and the real shared checkout state remain read-only. Keep pre-existing history
and source unchanged. Do not use native subagents, network or business effects.

Freeze expectations from original acceptance and input before implementing your
checks. Preserve all failed commands/processes and up to two corrections for the
same candidate; no sample swap. Record actual begin/end command evidence,
source hashes, route choice and reason, effect with baseline/conditions/results/
limits, and parent/user interventions. A real command-process exit is not a
provider or native-model failure. Missing model time/tokens/cost remain null.

Deliver a concise handoff-report.md and reply.json in the outer assigned worker
directory. Include relevant new output file hashes and isolated final state
hashes. Root will independently review outputs and replay state registration;
do not provide Root a pre-filled acceptance decision. Do not inspect any sibling
worker directory or seek an expected solution outside your assigned checkout.
