# Software delivery: prove the requested behavior works

Contents: Scope · Baseline · Scenarios · Implementation · Evidence · Iteration · References.

## Scope

Read this before building a software system, implementing an agent runtime, or
making a functional change in an existing repository. Program mode can deliver
the application or runtime directly; use flow mode only when the user wants a
reusable agent-flow package. Apply these methods to UI, backend behavior, state,
data migration and integrations. A tiny copy or color edit needs proportionate
inspection, not a multi-round test project.

Writing plausible code, a successful build, a responding server and a screenshot
of an initial page are different achievements. None alone establishes that the
user's task works. The project execution loop must own discovery, implementation,
runtime execution, result inspection and bounded repair; the user must not have
to ask "did you run it?" after every change. For an explicitly requested agent
flow, encode those responsibilities in the flow's nodes and routes.

Before the first slice, state the delivery boundary: a local prototype, a
deployable application, or an operated service, based on the requested outcome.
If deployment details are absent, a local target can keep development moving;
label it provisional and retain any broader requested obligations in the TODO.
Do not silently replace a requested whole system with one isolated endpoint.
Record a short delivery contract in the project brief and turn applicable
items below into the same task/case graph, rather than a second checklist:

| Boundary | Observable closure |
| --- | --- |
| Application | Primary user task reaches a durable result, including input rejection, conflict, explanation and recovery where relevant. |
| Runtime | Another process can start it from the supplied command/configuration, inspect useful errors/status, stop and resume it where state persists. |
| Data | Define identity, ownership and lifetime; test reuse/restart and changed-content identity conflicts. Add migration/backup/restore checks when the requested data or deployment scope needs them. |
| Interface | Test the requested interface and its state feedback. Graphical targets need target visual/keyboard evidence; CLI output checks do not prove GUI quality. |
| Agent infrastructure | Exercise an actual worker invocation, its result/error receipt, interruption reconciliation and bounded retry. Label the exercised adapter/provider accurately. |

Carry startup/configuration and reproducible acceptance commands into delivery.
For an operated service, include the requested operational/load/failure evidence;
local fixture latency is not a service objective. If a boundary is blocked,
identify only the dependent tasks and needed evidence. Close from the requested
product obligations and their current results, not a count of files or agents.

## Establish the baseline and the source

Before editing, inspect the real project, its instructions, existing components,
tests and build commands. Record the source revision and current build identity.
For an existing app, exercise the relevant original tasks if a runtime exists;
otherwise label the baseline unmeasured. Preserve a list of behaviors and data
that must survive. For a new app, define the smallest useful vertical slice and
the acceptance outcomes before constructing the whole interface.

For system-scale scope, read [system-architecture.md](system-architecture.md)
before the first slice. For a UI deliverable, read
[experience-handoff.md](experience-handoff.md) and keep task journeys, component
states, and visual intent aligned. Inspect the reference and target, choose a
task-appropriate design, then check behavior and appearance separately. A
functional smoke pass does not establish aesthetic quality; visual preference
does not establish findability, task speed, or lower error rates without
appropriate observation. Localize any unavailable evidence rather than
relabelling the whole product as verified.

Classify every supplied reference: exact source, upstream ancestor, compatible
component, visual inspiration, or unverified lead. A repository URL found in an
APK is not proof that its HEAD builds that APK. Compare application IDs, stack,
assets, versions and code when available. Do not replace a native app with a
different stack merely because its reference repository is easier to obtain.
An APK-only task may permit inspection but lack reproducible source, signing,
build or device access; finish useful analysis and disclose these exact blockers.

Use the checked manifest and commands in [material-binding.md](material-binding.md).
For an existing software target, configure the material manifest and intended
operation before editing, and reevaluate its evidence before target
modification. Apply [material-binding.md](material-binding.md) to distinguish the
target, reference source, and inspected binary. Compare identities for the
selected build variant, not an unrelated default configuration. String
extraction is an observation, not decoded build provenance. A matching ID alone
cannot promote an unverified lead to exact source. A reference-project patch
remains a reference-project result until its applicability to the target is
established. For greenfield work, register the new output directory and allowed
operations; do not demand binary-source binding to a nonexistent artifact.

For an explicitly source-only task, bind the source the user selected; do not
invent a binary requirement. Keep useful inspection/design available when a
binary-to-source relationship is unresolved. A gate allowing modification does
not establish runtime readiness or grant external authorization. Carry these
constraints into the project task graph, prompts, and acceptance criteria; the
host must enforce the same gate before actual write tools.

For each proposed redesign, record the user problem, present behavior, proposed
change, expected benefit, protected behavior, measurement and rollback trigger.
Compare original and candidate on the same input/device/backend where possible.
Measure task completion, mistakes, unnecessary taps, copying, context switches,
lost work and latency. A prettier page is not evidence of a better workflow.
Label preferences and inferred benefits as hypotheses until exercised.

When combining open-source work, check actual source and license/notice files,
runtime/platform support, dependency versions, data formats, API contracts,
state ownership, authentication, retry/idempotency, persistence and migrations.
Port an independently useful component through an explicit adapter first.
Preserve import/export, existing data and compatibility tests. Do not merge two
state owners or inherit old capability, authorization or billing claims.

## Design task journeys before changing code

Give each journey an actor goal, initial state and data, a continuous sequence
of user actions, observable outcomes, failure signals and protected invariants.
Cover a primary goal, a relevant interruption/failure/recovery, and repeated use
of the same state. Add a longer task and one previously unseen variation when
stateful behavior justifies them. Keep independent scenarios reproducible, but
do not reset state between actions in a journey meant to expose state leakage.

For UI work, inspect action → visible feedback → stored state → actual request or
result. Check touch/keyboard/focus/scroll/back behavior, current mode, cancellation,
loading/error states, small screens and persistence where relevant. For backend
work, check request → durable effect → response → retry/reconciliation. Include
only relevant dimensions, with concrete expected values or observable conditions.

Examples for a drawing app (adapt, do not blindly copy):

| Goal | Continuous journey | Observable result |
| --- | --- | --- |
| Edit two characters | Add A, type, add B, switch A/B, return after settings | Correct field is reachable; each character keeps its own text; no forced clipboard shuttle. |
| Reuse a generated image | Text-to-image, choose result as input, revise prompt, generate again | Current mode/source stay visible and match the request; history remains accessible. |
| Inspect images | Open image 2, zoom/pan, visit 3, return to 2, reopen, zoom again | Correct stable image identity, working hit targets and gestures; no invisible modal intercepts. |
| Make a comic | Create several panels, revise one, retry a failure, resume later | Unchanged panels, ordering and character settings survive; only intended work is repeated. |
| Change settings | Edit transfer setting/theme, navigate away, restart, run a task | Displayed, persisted and actually used values agree; contrast and drafts survive. |
| Save without friction | Finish generation, navigate/background, inspect output file | Default save is real and findable; permission/disk errors are visible; no false success. |

Do not invent screenshot details when referenced images are unavailable. Do not
guess the denominator, time window or provider for a percentage such as "Opus
compute". Trace it to a real field and define used/remaining, refresh and unknown
states. If the meaning is materially ambiguous, finish the other work and ask
one precise question rather than inventing a percentage.

## Implement a small vertical slice

Keep one owner per state and preserve stable object IDs. Reuse actual project
components and retain external contracts. Implement one useful end-to-end task,
exercise it, then expand. Give routine implementation, scenario design and
targeted review to available smaller workers according to user preference;
the coordinator owns integration and final acceptance. A fresh scenario reviewer
gets the raw task and artifact, not a suggested passing conclusion.

Do not use a blanket rewrite as the default response to poor UX. Preserve a
working baseline and compare at most one justified alternative. For references,
translate interaction intent to the target platform instead of mechanically
copying a desktop layout or a screenshot with no state/error behavior.

## Execute and distinguish evidence

Use the actual capable host: browser for web, device/emulator for native mobile,
and real processes/services for backend work. A mocked backend can test actual
UI state, but cannot establish live service compatibility or billing behavior.
No available runner means `unverified`, not "smoke passed". Supply runnable
instructions and available artifacts without fabricating screenshots or traces.

For an Android device already reachable through ADB, follow
[android-runtime.md](android-runtime.md) and run `scripts/android_preflight.py`.
Boot-completed alone does not establish a usable HOME or completed setup. Keep
the six raw probe results, and block dependent lifecycle journeys when their
environment prerequisites fail. This read-only preflight neither repairs the
guest nor proves an app result; separately observed foreground behavior retains
its own scope.

For each run record candidate/build identity, frozen plan hash, environment,
scenario, starting state, actions, observations, result and evidence references.
Capture screenshots/recordings for visual transitions and logs/requests/files
where they establish the outcome. Inspect evidence content; a file path alone
does not prove it contains the claimed result. Never log credentials or package
private user histories as example assets.

Keep these levels separate: static checks; reasoning/prototype simulation;
runtime UI with controlled responses; runtime with actual backend. Check that
assertions detect a known bad outcome with a small negative control where
feasible. Clicking without observing the effect is not a smoke test.

For an `agent_flow` package that delivers software, use
`scripts/smokecheck.py assess PLAN RESULTS` as its software-delivery structure
gate; read its schema and `assets/example-smoke-plan.json`. Start an unrun result
from `assets/example-smoke-unverified.json` (recompute plan_hash after editing
the plan). Never fill run observations from imagination. Each real run records
journey_id, round, candidate_id, level, backend, status, observations and
evidence; regressions bind behavior_id, candidate_id, status and evidence. The
results header binds baseline_id as well as plan and candidate. By default this
gate checks journey coverage, candidate/plan identity, evidence level, two
recorded rounds and protected baseline behavior; its report marks evidence
content unchecked. For local file inspection, use
`scripts/smokecheck.py assess PLAN RESULTS --evidence-manifest FILE` and follow
[smoke-evidence.md](smoke-evidence.md). That mode checks manifest coverage,
hashes, formats, run bindings and declared content assertions. Neither mode
launches software, authenticates a model or producer, proves truthful observations,
or judges UX.

For software-delivery flows, include this assessment in flow evidence, give the
flow a verification stage that runs it, and route completion only from a passing
assessment. Include the gate in frozen criteria and inspect prompts and routes
for bypasses. For program-mode system work, use the project acceptance matrix
and actual product/runtime checks in [project-execution.md](project-execution.md)
and [evaluation-plan.md](evaluation-plan.md); do not require a Flow IR smoke-plan
artifact. In both paths, missing runtime evidence means unverified. Factory
package validation is a separate check and is not a substitute.

## Improve across turns without losing earlier requirements

Round 1 exercises the baseline/main path and known defect. Round 2 repeats the
task with accumulated state, an interruption or an unseen variation, and checks
all required scenarios and protected behaviors on the candidate. A further round
is justified by a concrete finding. Default to two repair attempts, then return
the best candidate with unresolved defects and next evidence needed; never loop
until a model assigns itself a high score.

On a new user message, retain the original goal, accepted requirements, baseline,
completed changes, task graph and defect ledger. Classify the message as
clarification, new requirement, regression report or explicit scope replacement.
Update affected tasks and add regression coverage; preserve the prior graph and
runs as history. Resume the current project without asking whether to continue
or rebuilding its plan. A blocker applies only to dependent tasks; proceed with
independent work. Version changed plans and candidates, and never reuse an old
build's passing record as proof for new code. Do not weaken a criterion
to hide failure. Routine self-repair must not become a user troubleshooting loop.

Record lessons as candidates: observed defect, reproduction, source/build,
repair, regression, counterevidence and applicability. Reuse a supported lesson
to select a check on the next relevant task; do not automatically rewrite this
skill, promote one run as universal knowledge, or invent persistent learning.
Save project checkpoints and lessons through the host's supported persistence.

Use [run-ledger.md](run-ledger.md) for delegated attempts and interruption recovery.
Keep the original user brief or an explicitly labelled summary alongside input
hashes; never relabel a coordinator's summary as a verbatim user instruction.
Record who discovered each defect and which round produced its evidence. Resume
only after reconciling the host receipt, input identity and saved response. A
completed review can be reused for unchanged inputs while implementation remains
blocked; its completion does not complete the whole project. Keep previous
attempts immutable, and describe retrospective recovery records as retrospective.

## Primary references consulted 2026-09-26

- Playwright [best practices](https://playwright.dev/docs/best-practices): user-visible outcomes, reproducible scenarios and assertions that wait for state. This is a web technique, not an Android runtime.
- Maestro [flows](https://docs.maestro.dev/maestro-flows): action sequences with assertions on mobile/web; actual supported runner/device still required.
- LangGraph [persistence](https://docs.langchain.com/oss/python/langgraph/persistence): distinguish thread checkpoints from longer-lived stores. Forge does not thereby gain a LangGraph adapter or restart-safe memory automatically.

These inform the method; they are not evidence that this implementation has
executed an app, or a reason to adopt another orchestration framework by default.
