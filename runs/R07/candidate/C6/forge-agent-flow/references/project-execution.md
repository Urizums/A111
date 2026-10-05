# Program-mode project execution

Contents: Project state · Execution loop · Revision and recovery · Ownership ·
projectctl schema and commands.

Use program mode to deliver a working software system or agent runtime directly.
This project TODO layer coordinates implementation and evidence; it does not
compile a Flow IR package. Keep flow mode and the existing strict factory for an
explicitly requested reusable agent flow.

## Project plan and task state

Create one project plan with the current projectctl command and schema. The
forge-project-plan/1 plan uses schema_version and contains:

- project identity, goal, and deliverable kind;
- requirements with stable IDs, origin, basis, and acceptance IDs;
- acceptance assertions with required status and evidence level;
- tasks with dependencies, an owner, disjoint write paths, and acceptance IDs;
- optional defaults and unknowns.

Keep task status, attempts, and evidence in the project state. The status view
surfaces ready tasks and blockers. Include a concrete next action with the reason
when a task is blocked or failed. Together, the plan and state must make every
TODO reviewable.
Validate that each required acceptance assertion is owned by at least one task
and each dependency resolves. The controller excludes ready tasks whose
declared write paths overlap an active task's paths, including parent/child
paths, and rechecks when a task begins. Use relative paths from one project root
consistently. The guard compares normalized declarations; it does not resolve
absolute/relative aliases or symlink aliases, enforce filesystem permissions,
or isolate workers from writing elsewhere.
Keep the graph proportional: small repository changes may use only the tasks
needed for the actual change and its checks.

Use stable IDs and preserve the original brief. An explicit requirement quotes
or points to user-supplied material; derived requirements explain their
dependency; defaults state their rationale and reversible scope. Keep all
defaults and unknowns visible. Never add real business policy, permissions, or
external authority by inference. If domain rules are incomplete, implement
configurable policy with a safe all-human-review default and document any local
simulation.

## Continuous execution loop

Follow this loop until delivery or a real blocker:

1. Initialize or resume the same project state. On continuation, inspect status
   and the next ready task; do not ask whether to continue or recreate the plan.
2. Choose a task only when its dependencies are complete. Start one attempt and
   give its owner only the task-local inputs, acceptance, and assigned paths.
3. Execute the work, inspect the changed artifact, integrate disjoint work, and
   record actual evidence and acceptance results.
4. Run runtime acceptance and the applicable coverage checker. Route failed
   assertions into bounded repairs; do not close a task from a structural check
   alone when runtime behavior is required.
5. Finish the task as done, blocked, or failed with evidence or a concrete
   reason. For a blocked or failed task, include both the blocker and next action
   in the reason. Keep unrelated ready tasks moving.
6. Deliver the runnable artifact, exact invocation, acceptance results, known
   limits, and unresolved blockers.

Treat plan phases and reviews as internal checkpoints. A blocked task does not
block independent tasks. Before retrying timed-out external or delegated work,
reconcile its current host status and prior receipts. Do not infer failure from
silence, duplicate effects on retry, or count an accepted job as a completed
reply.

## Updating a project

When the user adds a constraint, retain the old graph and evidence, add stable
requirement and acceptance IDs, identify affected tasks, and add regression
coverage. Revise the plan with the concrete reason and explicitly invalidate
affected completed work; let downstream dependencies reset as required by the
projectctl protocol. For changed case acceptance, supply the revised full
evaluation plan through projectctl revise and invalidate affected completed
runtime tasks. Do not edit an exported plan file and treat an existing state
lock as updated. Never delete prior requirement IDs, silently weaken frozen
acceptance, or reuse evidence from an invalidated candidate. Resume through the
same project state after revision.

If a task lacks a safe specification, complete reversible local work using an
explicit default and leave only consequential unknowns for human policy. Use
design-only delivery only when requested or when an actual capability,
authority, or material gate blocks implementation. State exactly which tasks
remain blocked and what evidence or input will unblock them.

## Ownership and host capabilities

Use the current host's actual model, tool, and parallel-work capabilities.
Honor the user's current model preference; for routine separable tasks, prefer
an available Luna worker at maximum reasoning when the host supports that
configuration. Avoid adding roles without a distinct outcome. Give each worker
disjoint write paths, and keep integration and final acceptance with the
coordinator. Give independent evaluators task artifacts without expected
answers, diagnostic notes, or known failure labels.

Record actual model/settings, elapsed time, work claims, repairs, questions,
and host receipts in task evidence or the host's run log. The controller's
status includes elapsed time, but does not record worker claims or questions
for you. Record unavailable token and cost measurements as null.
Describe a stub or command worker as a stub or command worker; do not claim
native automatic provider execution or parallel engine support unless the host
actually supplies and exercises those capabilities.

## Current projectctl protocol

Use current CLI help and preserve one writer per state file. projectctl persists
task state and evidence metadata; it never calls models, workers, or product
tools. Its plan schema is forge-project-plan/1.

Bind the full forge-eval/1 acceptance plan when initializing a new
software_system or agent_infrastructure project. The project state stores the
complete plan and hash as its authoritative lock
(`evaluation_plan_lock: {plan, plan_hash, source_path}`); the source path is
absolute or null and only a reference, while the hash covers the complete plan.
Status reports `evaluation_plan_binding.status=bound` with source status
`matches`, `drifted`, `unavailable`, or `not_recorded`; unbound legacy state
reports `not_configured`. The embedded plan remains authoritative if the
exported source is missing or changes.
Every runtime-level acceptance ID in the project TODO plan must
match a required criterion in the bound evaluation plan, which must also have
required cases. Keep legacy unbound states readable, but treat
product_acceptance_status=not_configured as no frozen product-case binding.
Never describe their runtime result as verified against a frozen case plan.
Bound states initially report product_acceptance_status=not_assessed.
Use [executable-acceptance.md](executable-acceptance.md) to execute a local
product adapter and attach raw case evidence through `projectctl assess`.
The controller then recomputes that runner's exact-JSON product verdict and
checks current candidate/evidence files. Other runtime or human evidence still
requires an appropriate host review; this integration is not a universal grader.

```json
{
  "schema_version": "forge-project-plan/1",
  "id": "project_id",
  "goal": "requested outcome",
  "deliverable_kind": "software_system",
  "requirements": [
    {"id": "req_main", "text": "Required behavior", "origin": "explicit",
     "basis": "User-supplied basis", "acceptance_ids": ["acc_main"]}
  ],
  "acceptance": [
    {"id": "acc_main", "assertion": "Observable expected behavior",
     "required": true, "level": "runtime"}
  ],
  "tasks": [
    {"id": "implement", "title": "Implement behavior", "depends_on": [],
     "owner": null, "write_paths": ["src/"], "acceptance_ids": ["acc_main"]}
  ],
  "defaults": [],
  "unknowns": []
}
```

Keep IDs safe and unique across the plan. Every acceptance ID maps from at
least one requirement and is assigned to at least one task. The owner can be
null when the coordinator will execute the task; workers own disjoint write
paths. Static acceptance can be satisfied by static or runtime evidence.
Runtime acceptance requires runtime evidence; review acceptance requires
review evidence.

Use these commands:

```text
projectctl.py validate PLAN
projectctl.py init PLAN --state STATE [--evaluation-plan EVALUATION_PLAN]
projectctl.py status --state STATE
projectctl.py next --state STATE
projectctl.py assess --state STATE --report CASE_RUN_REPORT
projectctl.py reopen --state STATE --task TASK --reason OBSERVED_FAILURE_AND_REPAIR
projectctl.py begin --state STATE --task TASK
projectctl.py finish --state STATE --task TASK --attempt-id ID --outcome done|blocked|failed [--results RESULTS] [--reason REASON]
projectctl.py revise PLAN --state STATE [--evaluation-plan EVALUATION_PLAN] [--invalidate TASK_ID ...] --reason REASON
```

A done result file contains exactly an acceptance_results object, with one
result for each acceptance ID assigned to the task. Each result has status
pass, an evidence level, and a nonempty evidence list of local file paths and
SHA-256 digests. When the state is bound, the results file must also contain
evaluation_plan_hash equal to the state's lock. A bound result has exactly
acceptance_results and evaluation_plan_hash at its root; an unbound legacy
result has only acceptance_results. Calculate digests from the actual evidence;
never copy example hashes. begin records the bound plan hash with the attempt;
finish rejects a result with a stale or mismatched hash. Static acceptance may
be satisfied by static or runtime evidence.
Runtime acceptance requires runtime evidence; review acceptance requires
review evidence. Record the exercised required case IDs in the evidence itself.
The finish command checks criterion mapping, level, evidence-file hashes, and
plan hash; it does not run cases or grade semantics. Separately attach a real
case-run report with assess. A bound project's next view cannot report completed
without a passing product verdict. After a failed required case, reopen the
implicated done task to repair without changing the frozen requirement; keep
old attempts, invalidate downstream done work and retain the two-repair budget.

Blocked or failed outcomes use --reason and do not accept results. Put both the
blocker and a concrete next action in that reason. A failed task has at most
two repair attempts before it becomes blocked. Resume by reconciling active
attempts before considering a retry. A revision keeps prior plan/evidence
history, cannot remove requirement, acceptance, or task IDs, and cannot weaken
required acceptance or downgrade runtime acceptance. When the bound evaluation
plan hash changes, runtime acceptance tasks and their dependent work are
affected; list each affected completed task with --invalidate. Omitting
--evaluation-plan retains the current lock; supply the complete revised plan
when its content changes. Dependent work
is reset as required. Record the revision reason and preserve previous candidate
results as history. Check status for evaluation-source drift and historical
evidence warnings. The embedded evaluation plan remains authoritative if an
exported source file changes. Historical missing, changed, unreadable, or
non-regular evidence is reported as unverifiable history; that warning does not
block a new revision or new work.

The status view reports blockers, ready tasks, binding status, historical
evidence warnings, actual elapsed time, and recorded attempt time. Treat a
drifted source or historical warning as evidence metadata, not as a silent pass
or a new-work blocker. Token and cost values remain null. Read these as host
accounting only; projectctl does not authenticate semantic claims or evidence
producers.
