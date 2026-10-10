---
name: forge-agent-flow
description: Design, run, review or improve reusable workflows for agent-assisted work, including task routing, handoffs, practical checks and evidence-based iteration.
---

# Forge — designing workflows that can be used

Forge helps turn a goal into a method another person or agent can actually follow. A useful workflow explains the decisions, handoffs, checks and recovery paths needed for the outcome. It need not become a multi-agent system, a fixed diagram or a set of documents. Use the tools the host really provides; this skill does not include a runner.

**Start with the requested result.** Read the original materials and identify who will use the result. Distinguish what was explicitly requested, what is needed to make the result correct, and what would merely be helpful. Decide whether the user needs a one-time answer, an application, a workflow design, a demonstration, execution of an existing workflow, or an improvement to one. For a small task, complete it directly and check it. Do not manufacture a reusable process.

## Design for the next action

Work backwards from the outcome: what must exist, what decisions produce it, what inputs are available, and how will a consumer know it is usable? Write down only the interfaces and branches that matter to this task. A short explanation may be sufficient; use a table, diagram or machine-readable schema when it makes actual handoffs clearer. See [workflow design](references/workflow-design.md) for complex or reusable work.

Pay particular attention to **required result instances**. If the task asks for separate results for two methods, periods or groups, a recommendation of one does not silently cancel the others. Where dimensions matter, check that all required outputs have producers and consumers; do not create large coverage matrices for a single uncomplicated result.

Choose roles from dependencies and genuine benefits. One agent can do several compatible jobs. Delegate when independent review, expertise or parallelizable work warrants it, not because a template lists roles. Shared decisions need an owner, and parallel work needs interfaces that can be reconciled. For real delegation, see [collaboration](references/collaboration.md).

When consequential information is missing, ask about the decision that depends on it and continue independent useful work. Reversible defaults are fine when they do not pretend to be facts, approvals or unavailable capabilities.

## Check behavior, not ceremony

Agree on what would count as correct **before** optimizing or declaring a result complete. Checks should flow from the user's requirements and the important failure modes of the domain. A useful first slice crosses a real input, the main operation and a receiving check; test a meaningful boundary when the claimed behavior depends on it. A smoke test covers that slice, not the entire task. For deeper checks and independent review, see [evaluation](references/evaluation.md).

Use the evidence appropriate to the claim: numerical recomputation for numerical results, original sources for factual claims, and real target interactions for UI behavior. A command finishing, a file existing or a screenshot looking good proves less than a correct deliverable. When the required runtime or source is unavailable, preserve that limit instead of calling a static approximation a pass.

Where the same important numbers or conclusions appear in several outputs, check they retain their meaning after calculation, rounding and export. A full facts registry is sometimes useful, but not a default requirement.

## Execute, learn and hand off

When execution is requested and authorized, perform the earliest useful action. State what has actually run, what was only designed and what remains unverified. Producers can self-check; an independent judgment requires a genuinely separate perspective with access to original requirements and real artifacts. If author diagnoses, expected answers or prior verdicts are visible through files, logs, arguments or summaries, do not claim a blind review.

After a failure, identify whether the problem lies in the requirement mapping, interface, implementation, environment or check itself. Make a change with a reason and rerun the affected assertion. Keep earlier failed attempts and actual resource use. Do not endlessly repeat the same path without new information, or retrofit an old experiment's limits to make it pass. See [iteration and recovery](references/iteration-and-recovery.md).

For ongoing projects, preserve the working goal, accepted evidence, actual unresolved calls, blockers and the next executable step. Continue only while a useful authorized next action exists; a TODO heading does not launch an agent or background process. See [continuation](references/continuation.md).

Specialized guidance is available for [modeling](references/modeling.md), [frontend](references/frontend.md) and [source evaluation](references/source-evaluation.md). Read these only when they change the current decision. Keep experimental examples and task-specific scripts outside the portable skill. A new lesson belongs in this skill only when it has a clear trigger and improves a real decision without imposing unnecessary work on unrelated tasks.
