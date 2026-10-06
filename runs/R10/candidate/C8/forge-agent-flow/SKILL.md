---
name: forge-agent-flow
description: Design, refine and run reusable workflows for agent-assisted work. Use when a user needs a method for coordinating tasks, roles, handoffs, evidence and iteration, or wants to repair an existing workflow.
---

# Forge — meta-workflow

Turn a goal into a workable method, use it on actual material when execution is
requested, and improve it from observed results. The deliverable is the workflow:
decisions, responsibilities, handoffs, checks and stopping conditions. Use the
host's available tools; this skill requires no bundled runner or controller.

## Establish the outcome

Read the original request, supplied material and applicable project rules.
Identify the intended result, constraints, authority and evidence needed to call
it complete. Separate required behavior from optional advice and assumptions.
Ask about a missing decision only when it materially changes the work and has no
reasonable reversible default; continue work that does not depend on it.

Choose from the requested result:

- **Design a workflow:** deliver a usable method and a worked example where
  helpful. Do not imply the example or a diagram proves execution.
- **Run an existing workflow:** keep its actual requirements, resolve the needed
  capabilities and execute the supplied inputs. Do not redesign it without cause.
- **Improve a workflow:** retain the original version and observed failure,
  change the decision or handoff responsible, and verify the affected behavior.
- **Ordinary one-time work:** do the task directly with a relevant check; create
  a reusable workflow only when requested or justified by repeated coordination.

## Forge the smallest useful workflow

Use [workflow-design](references/workflow-design.md) for a new or substantially
changed workflow. Establish these elements without forcing a document per item:

1. **Outcome and acceptance:** what the user receives and what observable result
   would satisfy each material requirement.
2. **Inputs and decisions:** which source material each step needs, what it may
   infer, and which unknowns change the route.
3. **Work and ownership:** steps with dependencies, one responsible owner per
   output, and the authority to integrate or approve changes.
4. **Handoff and checks:** output format, source/evidence links, rejection
   conditions and the receiving step's check before reuse.
5. **Failure and continuation:** bounded repair, blocked-branch recovery,
   checkpoint contents and when to stop.

Reuse an existing method or specialist skill when it fits the outcome and is
actually available. State what it contributes and retain the user's constraints.
Add stages or agents only when they resolve a real dependency, expertise need or
independence requirement. A simple chain in one context can be sufficient.

## Execute and integrate

When execution is requested, perform the earliest authorized action that yields
task-relevant evidence or an output the next step can use. A tool probe is setup;
reading source may be useful work, but neither alone proves the final result.
Use the first actual batch to expose missing decisions before expanding the flow.

For delegation or multiple owners, read
[collaboration](references/collaboration.md). Delegate only when authorized and
supported by the host. Assign the original task, minimum raw inputs, output
boundary and completion conditions. Keep shared decisions and final integration
with the coordinator. Distinguish a role performed in one context from a real
independent context; a role label does not establish independence or isolation.

Check each received output before relying on it. Preserve conflicting evidence
and uncertainty rather than forcing consensus. When a tool or independent actor
is unavailable, describe the affected claim accurately and continue unrelated
authorized work. Do not infer permissions or capabilities from workflow text.

## Evaluate and revise

Read [evaluation](references/evaluation.md) when designing acceptance, reviewing
an authored workflow or assessing a failure. Compare real outputs with the
original requirements and raw sources. Separate structural checks, observed
task correctness, independent verification and claims about speed or generality.
Tests of an implementation support that implementation; they do not prove that
the workflow selects good actions or that a task was delivered.

Freeze requirements and inputs before a bounded evaluation. Preserve unsuccessful
attempts and the cumulative repair budget. Use an existing declared limit; if a
bounded evaluation has none, allow at most two failure-driven correction rounds.
Count changed source, orchestration and fallback attempts honestly. Stop at the
limit; another actor, renamed sample or changed criterion cannot restart it.
A genuinely new user requirement is a versioned scope change, not a passing
verdict on the old failure.

Revise only what the observed failure supports. Deliver the current artifact,
checks and limitations. A design-only result is complete when design was asked
for; execution work requires the actual requested output and applicable checks.

## Continue only while useful

For work spanning sessions or an explicitly ongoing goal, read
[continuation](references/continuation.md). Update the same TODO and checkpoint,
retain blockers and consumed budgets, and record the next executable action.
When a stage requires a successor, do its real first step before calling the
transition complete. Stop when the goal is satisfied, the user stops work, or a
real dependency/budget prevents further relevant progress; do not invent stages
to keep running. No instruction file provides background scheduling.
