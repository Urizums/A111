---
name: forge-agent-flow
description: Design, build, run and improve reusable workflows for agent-assisted work. Use when a user needs task routing, roles, handoffs, smoke checks, acceptance and iteration, including research/modeling or frontend delivery workflows.
---

# Forge — meta-workflow

Turn an intended outcome into an executable method, try it on real material when
requested, and revise from observable results. The product is the workflow:
decisions, responsibilities, interfaces, checks and stopping conditions. Use the
host's available tools; this skill requires no bundled runner or controller.

## Apply necessity and proportionality

Classify a proposed requirement as **mandatory** only when it is explicitly
required or logically necessary to deliver/verify the authorized outcome;
**conditional** when a relevant risk, dependency or task property triggers it;
**optional** when its expected value justifies the work; or **unverified**
when the needed capability/evidence is absent. Name the trigger and smallest
useful check. Examples, candidate methods, matrices, roles, artifacts and
research stages are not universal quotas. Do not promote stylistic advice,
a research hypothesis or a reviewer preference into a pass/fail requirement.
For a small task, a direct artifact and relevant check may be the entire flow.

## Resolve the requested delivery

Read the original request and raw material. Separate explicit requirements,
derived needs, reversible defaults, open decisions and permissions. Choose:

- **Design a workflow:** deliver a usable method; mark illustrations as designs.
- **Build and demonstrate a workflow:** deliver the method and a real vertical
  slice that exercises its main handoffs and checks, with remaining scope visible.
- **Run an existing workflow:** preserve its requirements and execute its inputs.
- **Improve a workflow:** preserve the original and failure; change the implicated
  decision or interface and check the affected behavior within the original budget.
- **Deliver an application or one-time result:** use the relevant direct path;
  produce a reusable workflow only when requested or justified by coordination.

Clarify missing information that changes a consequential decision with no safe
default. Continue useful independent work. Sparse prompts do not authorize weak
checks; detailed prompts do not supply missing data, hardware or permissions.

## Build a contract the next step can use

Read [workflow-design](references/workflow-design.md). Build from final outcomes
back to the decisions and evidence they require. Express the workflow as a compact
blueprint, adapting the user's format rather than forcing an execution framework:

| Step / trigger | Raw inputs | Decision or operation | Owner / authority | Output and next consumer | Receiving check | Failure / stop |
| --- | --- | --- | --- | --- | --- | --- |
| A meaningful unit of work | Version and source | What it does, including branches | Responsible role | Concrete artifact / interface | Observable assertion and evidence | Recovery condition and original budget |

Where the user requires separate outcomes by method, population, horizon,
version or other dimension, check that each required outcome has a planned
producer, usable output and receiving check. Represent combinations compactly
when they are large; do not enumerate dimensions the task never requires.
For a one-off small output, do not manufacture a coverage register.

Trace material requirements through these steps. Check dependency order, ownership,
interface compatibility, integration points and the path for missing or conflicting
evidence before adding parallel actors. One context may perform several roles;
that does not create independent verification. Reuse fitting available methods.

For research or modeling read [modeling](references/modeling.md); for substantial
UI work read [frontend](references/frontend.md). For searches, borrowed skills, papers and
community templates read [source-evaluation](references/source-evaluation.md).
These are conditional adaptations, not mandatory stages for every task.

## Freeze checks before optimizing the run

Read [evaluation](references/evaluation.md) when designing or judging a workflow.
Declare each gate's purpose, original requirement, input, assertion, evidence,
responsible checker, failure route and what its result does **not** establish.

- **Preflight:** capabilities, necessary materials and supported evidence channel.
- **Smoke:** a small real end-to-end path from raw input to a user-relevant output,
  including its receiving check and one relevant failure/boundary path.
- **Acceptance:** all mandatory outcomes checked against the original requirements
  and sources; use a fresh context when independence is required and available.
- **Delivery:** valid artifacts, reproduction instructions and unresolved limits.

Reduce smoke scope when justified; preserve the selected assertions and the full
acceptance backlog. Do not replace numerical, interactive or source checks with
file existence, an exit code, screenshots alone or the author's pass report.
An unavailable tool makes that observation unverified; it does not weaken the gate.

## Execute, delegate and integrate

Run the earliest authorized task-relevant action and complete the first useful
slice. Capability probes and input reads are preparation, not final delivery.
For delegation read [collaboration](references/collaboration.md).
When independent review matters, inspect the *actual forwarded packet and
visible history*, not only filenames: author diagnostics or expected answers
may leak via command arguments, logs or summaries. If separation cannot be
established, label the review informed/unverified rather than blind. Send relevant
original requirements, minimum raw inputs, output boundary, check responsibilities
and the existing budget. Retain actual call identities and status.

The coordinator owns shared decisions and integration. Producers supply artifacts
and self-checks; independent acceptors receive original requirements and actual
artifacts, not an intended answer or a producer's diagnosis. Inspect receiving
checks before consuming outputs. Assign reviewers a falsifiable task: which
requirement, which evidence, what would fail, what is outside their claim.

Prefer existing tool receipts and a compact requirement-to-evidence record over
bespoke recording machinery. Distinguish command completion, artifact production,
source-checked correctness and independent acceptance. Mark drafts and unchecked
outputs accurately; a producer's completion label is not the verdict.

## Improve without laundering failure

Classify material failures before changing instructions: omitted deliverable,
interface mismatch, runtime defect, contaminated evidence, weak assertion,
or an unsupported requirement. Fix the implicated step/check and test a
counterexample; do not add a universal rule merely because one case failed.
Also test that the change does not overcomplicate an unrelated simple task.

Separate observed facts, causal hypotheses and future expectations. Correct only
what real evidence supports. Retain frozen inputs, unsuccessful attempts and
counters across source, orchestration and fallback corrections, including failed
constructions without a child process. Read
[iteration and recovery](references/iteration-and-recovery.md). Separate tool
recovery, substantive defect correction and planned research/model iteration.
Continue when the next action has a supported change or unresolved material
question and fits actual authority/resources; two local errors do not impose a
whole-task stop. Do not repeat an unchanged failed path without new information.

Respect actual resource/permission boundaries and any explicitly fixed experiment
conditions. Preserve actual totals even above an old limit; do not cap or reset
them, switch actor/sample or rename a candidate to obtain replacement acceptance.
A user-authorized policy change is a prospective, recorded amendment: retain the
old conditions/verdict, state what changes and keep mandatory outcomes intact.
It does not retrospectively pass the old trial. Inspect the acceptor's verdict:
mandatory failures need a violated requirement and evidence; optional suggestions
must not invent new required conditions or justify a pass on missing evidence.

A separate capability-research loop is appropriate only when an ongoing
research/improvement goal is authorized. Select a genuinely informative new
failure mode or task class, freeze a fair comparison and bounded checks,
and distinguish a demonstrated gain from a hypothesis. Delivering the
user's task does not itself justify endless challenges or new side effects.

## Continue from a truthful checkpoint

For ongoing work read [continuation](references/continuation.md). Maintain the same
TODO, input/candidate identities, results, unresolved calls, original failures,
budgets and next executable action. A required stage transition needs its accepted
predecessors and a real successor first step. Stop at completion, a user stop or
a real dependency/budget boundary; do not manufacture stages to sustain activity.
No instruction file supplies background scheduling or competition submission authority.
