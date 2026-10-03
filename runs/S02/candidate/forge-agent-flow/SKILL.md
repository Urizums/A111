---
name: forge-agent-flow
description: Plan, design, build, and verify software systems, agent infrastructure, or reusable agent flows from natural-language goals. Use for system, application and frontend architecture, interaction and visual design, application and service development, worker runtimes, repository changes, workflow contracts, failure recovery, and evidence-based evaluation.
---

# Agent Flow Forge

## C2 recording contract (versioned candidate)

For measured native-worker runs, apply
[recording-protocol.md](references/recording-protocol.md) before dispatch. This
revision freezes a precise first-command capture, instrumentation boundary,
receipt order, correction denominator and worker tool scope. Keep the original
`skills/forge-agent-flow` snapshot unchanged. An ordinary worker smoke validates
this contract only for its observed run; it is not a performance experiment.

Turn the user's intended outcome into the smallest complete deliverable and
verify it with evidence from the real runtime. Choose the delivery type from the
result and execution boundary the user wants, not from isolated words in the
request. Record the chosen type, its basis, and reversible defaults in the
project brief.

## Choose the delivery type

| Type | Choose it when the requested result is… | Build path |
| --- | --- | --- |
| `software_system` | A usable application, service, or software product behavior. | Program mode and the project TODO workflow in [project-execution.md](references/project-execution.md). |
| `agent_infrastructure` | A runnable worker runtime or agent platform, including task state, results, and recovery. | Program mode and the project TODO workflow. |
| `agent_flow` | A reusable flow package that orchestrates work through prompts, contracts, routes, and bounded steps. | Flow mode and the existing strict factory protocol below. |
| `scoped_change` | A focused change or repair in an existing repository. | Use the repository's normal workflow and scale planning and checks to the change; use the project TODO workflow when coordination or continuity warrants it. |
| `scoped_task` | A one-time result from supplied material, without a reusable flow or software deliverable. | Perform the task directly, verify its relevant requirements and deliver the result. |
| `design_only` | The user requests a design, or a real host, access, or material blocker prevents a runnable result. | Deliver the useful design and identify the exact blocker. Do not choose this to reduce the work or avoid implementation. |

For a goal that asks for a system, use program mode to deliver the system
directly. Keep flow mode for an explicitly requested reusable agent flow; do not
wrap every software project in the factory. Treat phases and review gates as
internal checkpoints, not requests for the user to approve routine progress.
For underspecified but reversible behavior, implement a local prototype with
stated defaults and simulated policies. Set uncertain authorization and business
rules to human review and configurable policy; never invent real permissions.

Distinguish creating a flow from executing a supplied flow package. For a
one-time `scoped_task`, use one agent and a meaningful check unless the task
requires independent evidence or tool separation. Do not create a factory or
application merely to produce the result. For an existing package, preserve it
and execute its declared inputs through packagectl; do not restart the factory
or redesign its frozen plan. Read [task-entry.md](references/task-entry.md) for
the startup paths and existing-package handoff. Factory construction stages
are not a required number of target-flow nodes or worker contexts.
For every review or regrade, including a `scoped_task`, read and apply
[Check a review verdict against its requirements](references/task-entry.md#check-a-review-verdict-against-its-requirements).
Recompute the verdict from the current source and evidence; a previous report
is a candidate conclusion, not an acceptance rule. For each negative required
rating, identify the exact violated source clause or justified derived
requirement and the actual contradiction or missing evidence for that assertion.
If no such requirement supports the gap, retain it as advice. Rate optional
usability or documentation improvements separately; they cannot by themselves
downgrade a satisfied required row or the required verdict.

## Run the selected path

Read [design-from-brief.md](references/design-from-brief.md) before intake. Keep
the user's goal, explicit requirements, derived requirements, defaults, and
actual blockers distinct. Ask only for information that changes a consequential
choice with no safe reversible default. Continue useful unblocked work while a
local task is blocked.

For `scoped_task`, record only relevant assumptions, perform the task and check
the output against its source. Additional architecture, flow/package schemas
and project controllers are optional only when the work needs them. For an
existing package, begin with task-entry.md, its schema-matching acceptance
protocol and host-execution.md; load factory design references only if creating
or explicitly revising a flow.

For `software_system`, `agent_infrastructure`, and coordinated `scoped_change`
work, read [software-delivery.md](references/software-delivery.md),
[project-execution.md](references/project-execution.md),
[host-execution.md](references/host-execution.md), and
[evaluation-plan.md](references/evaluation-plan.md). Load their program-mode
sections first; load flow/package sections only when using that protocol.
Keep a durable TODO graph
with dependencies, owner and write paths, acceptance, status, evidence, blocker,
and next action. Bind the full case plan when initializing a new system or agent
infrastructure project. On continuation, resume the same project and preserve
prior history; do not ask whether to continue or reconstruct the plan from scratch.
For a product reachable through a local process, read
[executable-acceptance.md](references/executable-acceptance.md) and run the
frozen cases with `scripts/caserunner.py`; attach its regraded report through
`projectctl assess`. Use the target runtime for UI and human criteria. Keep
structural TODO completion and the product verdict separate; reopen implicated
done work on observed failure without changing the frozen acceptance.

For a new system or an architecture request, read
[system-architecture.md](references/system-architecture.md). For an existing
change, use only its affected layers. When a deliverable has a graphical UI, read
[experience-handoff.md](references/experience-handoff.md) and use the independent
`design-product-experience` skill for visual, interaction and motion design.
Forge owns shared architecture, tasks, integration and acceptance; the design
skill owns its detailed methods and original presets. Adapt candidates to the
existing stack and verify them in the target app.
For a text CLI, resolve command discoverability, progress, error and recovery
feedback in its journeys; load visual palettes, graphical layout and motion
methods only when the requested interface needs them.

For creating `agent_flow`, read [evaluation.md](references/evaluation.md),
[evaluation-plan.md](references/evaluation-plan.md), [patterns.md](references/patterns.md),
[architecture.md](references/architecture.md), [flow-contract.md](references/flow-contract.md),
[package-contract.md](references/package-contract.md), and
[host-execution.md](references/host-execution.md). Use the existing strict
factory wrapper and its frozen plan/package binding. Its Flow IR, stages, and
acceptance remain the flow path; do not use them as a substitute project manager
or as evidence that software works.

Apply checks in proportion to the selected scope. Existing-software changes use
the material gate in [material-binding.md](references/material-binding.md).
Greenfield work records its output directory and permitted operations; it does
not require a binding to a nonexistent binary. Require real UI interaction only
when the deliverable has a UI. For native Android work with an available ADB
device, read [android-runtime.md](references/android-runtime.md).

## Design applicable layers

Resolve runtime reliability, application responsibilities, frontend engineering,
interaction, and visual design as related concerns. Keep one state owner and
trace important requirements through decisions, interfaces or components,
tasks, and acceptance evidence. For small changes, retain a short impact note;
for systems, record the relevant boundaries and quality scenarios before the
first useful vertical slice. Keep architecture and implementation consistent
when new constraints arrive.

Tie layout, density, color, navigation, loading and motion choices to the audience
and primary task. Review their combined effects on attention, discoverability,
waiting, accessibility, and system behavior. Treat a reference, preset, or
design rationale as a candidate until checked in the target. Distinguish
functional runtime evidence, inspected visual evidence, and observed usability
or performance outcomes; none alone proves the others. State measurement
conditions and the basis of thresholds, and keep unknown operational targets
explicit rather than inventing production guarantees.

## Implement and verify

Keep the host in a continuous loop: plan or update the task graph, select a ready
task, execute and integrate it, run runtime acceptance, make bounded repairs,
and deliver. When a new constraint arrives, update the graph, retain the old
record and add relevant regression checks. Block only the affected task; keep
independent work moving. Do not treat reading or writing a schema, compiling,
or creating a package as completion of the requested product.

For agent infrastructure, implement an executable worker adapter, task status
and result handling, and observable error and recovery paths. When credentials
or a model endpoint are unavailable, exercise an explicit local stub or command
worker and state exactly what that run proves. Never describe a stub run as a
real LLM run. Treat models, parallelism, permissions, and provider access as
available only when the current host confirms them. Honor the user's current
model preference; for routine separable work, prefer an available `gpt-6-luna`
worker with `max` reasoning. Assign disjoint write paths, keep integration with
the coordinator, and give fresh evaluators task artifacts without expected
answers or prior diagnoses. Record actual model/settings and elapsed time;
record unavailable token or cost data as `null`.

For an actual host that creates workers, read [host-bridge.md](references/host-bridge.md)
and use its request/receipt/reply/commit loop for a project task or existing
package node. Persist intent before the real host call, verify the returned
worker and output, and reconcile interruptions before any retry. The local
bridge supplies no embedded provider execution or external-effect transaction.
For continuous host-agent execution, read [host-driver.md](references/host-driver.md)
and use `scripts/hostdriver.py` to select ready work, claim typed native-tool
actions, import actual receipts, independently review and commit, then continue.
After a claimed creation call loses its return, reconcile the bound worker;
never repeat a claimed spawn or turn unknown status into failure. For a saved
run, read [host-observability.md](references/host-observability.md), inspect
without replaying effects, and resume with the original run ID and budgets.
Reconcile a provably invalid uncommitted local review ack explicitly; preserve
its bytes and request a new review, never discard uncertain native effects.
For local shared admission or a wait cutoff, read
[host-resource-boundaries.md](references/host-resource-boundaries.md). Keep
unknown workers admitted, require actual terminal evidence to release a slot,
and query actual running status before a single deadline interrupt. A control
return is not terminal proof; preserve late results for original source review.
For host reply/decision scaffolding and read-only protocol preflight, read
[host-drafts.md](references/host-drafts.md). Copy original identities and hash
actual files with `scripts/hostdraft.py`; fill business results and independently
grade acceptance before the existing receive/commit loop. A generated draft or
successful preflight never establishes semantic acceptance or native completion.

For reusable skill development, keep requirements, architecture, generalization,
core instructions and repairs with the coordinator as author. Delegate website
search, source research, frontend/interaction preprocessing and independent
validation to an available Luna worker. Give research workers evidence-output
paths, not skill write paths; treat their design suggestions as candidates for
the coordinator to assess. Follow the role and handoff contract in
[host-execution.md](references/host-execution.md#skill-development-roles).
Honor any later explicit change to the user's role assignment.

Freeze acceptance before candidate verification. Test distinct input branches,
including success, rejection, missing information, and conflict where relevant;
exercise failure, recovery, and reuse of prior state. Check both authorized
success and unauthorized failure for permissioned operations. If the system
makes automatic decisions, test absent or disabled rules and require an
explanation field. Add real feedback, keyboard behavior, and error states only
for UI journeys. Keep structural counts and references labeled as structural
checks. Preserve frozen criteria; version later changes and rerun regressions.
Use [evaluation-plan.md](references/evaluation-plan.md) to choose the matching
acceptance protocol and report its limits.

Deliver the working artifact, how to run it, acceptance evidence, unresolved
blockers, and relevant limitations. Distinguish designed, structurally checked,
fixture-exercised, and live-exercised results. Never claim native automatic
provider execution, parallel execution, or production readiness unless the
current host actually supplied and exercised that capability.
