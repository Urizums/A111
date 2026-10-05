# Host execution

For the implemented POSIX host-driven task/node bridge, read
[host-bridge.md](host-bridge.md). It adds durable dispatch intent, imported actual
host receipts and reply-to-controller commit without changing the existing
project/package schemas. It still requires the coordinator's actual host calls.

Contents: Program mode · Flow mode · Delegation scope · Project task completion · Skill development roles.

## Program mode

For software_system, agent_infrastructure, and coordinated scoped_change
projects, use the project TODO loop in [project-execution.md](project-execution.md).
Use projectctl.py to initialize or resume the project, validate its plan, list
status and ready tasks, begin an attempt, finish with actual results or a
concrete blocker, and revise the plan when requirements change.

```text
init PLAN --state STATE [--evaluation-plan EVALUATION_PLAN]
validate PLAN
status --state STATE
next --state STATE
assess --state STATE --report CASE_RUN_REPORT
reopen --state STATE --task TASK --reason OBSERVED_FAILURE_AND_REPAIR
begin --state STATE --task TASK
finish --state STATE --task TASK --attempt-id ID --outcome done|blocked|failed [--results RESULTS] [--reason REASON]
revise PLAN --state STATE [--evaluation-plan EVALUATION_PLAN] [--invalidate TASK_ID ...] --reason REASON
```

Use the final CLI help and schema from the current implementation as
authoritative. A ready task is work to perform, not evidence of completion.
Persist the real attempt ID, outputs, acceptance results, and evidence. Record
blocked or failed work with a reason and next action; keep independent tasks
moving. Resume the saved project state instead of restarting planning.

Initialize new software_system and agent_infrastructure projects with the
complete forge-eval/1 plan. projectctl embeds its contents and hash as the
authoritative state lock. Every runtime acceptance ID must match a required
criterion in that plan. Bound finish results include the matching
evaluation_plan_hash. Legacy unbound states remain readable, but
product_acceptance_status=not_configured does not mean frozen product cases
passed. Record the executed case IDs and outputs in evidence files; the
finish command binds criteria and hashes but does not execute or semantically
grade cases. A bound project initially reports product_acceptance_status=not_assessed.
For a local product process, follow [executable-acceptance.md](executable-acceptance.md):
run the frozen cases, attach the actual report with assess, and inspect the
separate recomputed product verdict. On failed required cases, preserve the
candidate and reopen implicated done work without changing acceptance.

The ready list and begin guard exclude tasks whose declared write paths overlap
active work, including parent/child paths. This only schedules declared paths;
declare all write paths relative to the same project root. The normalized
lexical check may miss absolute/relative aliases and symlink aliases. It does
not enforce filesystem permissions or contain workers that write outside their
assignments. Inspect status for source drift or historical
evidence warnings. A warning about missing or changed evidence from an
invalidated attempt is retained history and does not block a revised run.

For changes to an existing software target, configure and inspect the material
gate described in [material-binding.md](material-binding.md) before a worker
edits the target. For greenfield work, register the output directory and allowed
operations; do not require a binding to a nonexistent binary. A material gate
does not grant external authority or prove runtime readiness.

## Flow mode

For a unified `forge-package/1` or `forge-package/2`, use `packagectl.py` with the package instead of
`flowctl.py` with its embedded flow in the procedure below. Read and obey the
dispatch's `execution_settings` and `host_requirements`; verify actual host
support and current authority before executing. The response envelope is the
same. Never bypass unmet package requirements by launching its inner flow.
For supplied packages, follow [task-entry.md](task-entry.md) without repeating
factory construction. Invoke bundled Python scripts by their skill-root paths.

The host is the agent environment reading this skill. `flowctl` owns routing
and contract checks; the host owns reasoning, real tools and permissions.

For an agent_flow that modifies existing software, configure the material gate described in
[material-binding.md](material-binding.md). Read the returned material assessment
before invoking a worker or modifying target files. Unconfigured legacy flow
runs remain compatible but are not protected by this gate. The factory cannot stop
a host from calling tools outside its dispatcher.

1. Inspect the user's requirements and current tools. Instantiate the flow with
   verified bindings, capability status and limits before starting.
2. Create an inputs JSON object with exactly all declared input fields. Run
   `flowctl.py start FLOW --inputs INPUTS --state NEW_CHECKPOINT`.
3. Use the returned dispatch or `flowctl.py next FLOW --state CHECKPOINT`.
   A `ready` dispatch contains node prompt, input slice, allowed capability
   declarations, acceptance rules, output types and invocation ID.
   Optionally generate a response draft with `forge_template.py response` as
   described in [protocol-templates.md](protocol-templates.md). It preserves
   the current invocation ID and selected outcome but supplies no work evidence.
   IR 1.1 dispatch descriptors may include nested schemas; read and satisfy the
   entire contract before submitting a response.
4. Perform that task with the host. For a check node, run its actual checker.
   If a permitted separate worker is useful, send only task-local inputs and
   node contract. Do not leak holdout answers, author diagnoses or unrelated
   conversation. Otherwise perform the stage in the host and label evaluation
   dependence accurately.
5. Persist actual output and evidence, then submit this JSON envelope using
   `flowctl.py advance FLOW --state CHECKPOINT --response RESPONSE`:

```json
{
  "invocation_id": "copy from current dispatch",
  "outcome": "ok",
  "artifacts": {"actions": []},
  "evidence": ["No explicit action was present in the supplied notes."]
}
```

6. Continue with the next returned dispatch. Stop at a terminal or a blocking
   budget/capability check. Exit code 2 means invalid, failed or blocked; inspect
   JSON rather than treating all nonzero codes as the same defect.
7. Deliver accessible outputs and evidence. Distinguish lifecycle completion
   from task acceptance: a completed delivery may contain a candid limited result.

The trace stores input/output hashes, outcomes, node identity and evidence
references. It is an audit aid, not a tamper-proof proof or full replay log.
Save actual response files/receipts separately when auditability is required.
Use [run-ledger.md](run-ledger.md) to track real delegated attempts and derive
their recovery status from saved evidence. A job without a completed reply is
not complete merely because the host accepted its creation. Before restarting,
query the current host state for requested/running attempts; do not invent
failure from silence or relaunch an external effect blindly. Hash checks detect
changed or missing bytes, not fabricated receipts. Keep retrospective records
separate from claims about when original execution occurred.
Checkpoints retain current artifact values. Use one writer only. `next` is
read-only: a computed budget/capability block is returned without changing the
checkpoint's stored `running` status; treat the dispatch result as authoritative.

A repeated `next` returns the same invocation ID. A response from a prior step
is rejected after advancement. This prevents duplicate checkpoint advancement,
not duplicate tool effects. Before a write with external consequences, verify
existing task authority, use the invocation ID as an idempotency key when the
service supports it, and persist a receipt. After a timeout, reconcile the
external result before retrying. Never infer failure solely from lost feedback.

Persisted checkpoints are local files, not a service or scheduled background
worker. Provider timeouts, credentials, real tool access, usage accounting,
semantic payload validation and external exactly-once behavior are not provided.
Do not request secrets in conversation. Use the host's supported configuration.

## Delegation scope and actual host state

Record each resource limit with its value, scope (`global_host`, `per_flow`,
`per_worker` or the concrete project/task), owner and actual enforcement. A
per-flow child limit is not automatically the entire team's capacity. A step
bound is not an external-worker timeout; a requested budget is not metered
usage. Do not add unsupported fields to strict package schemas: put these
operational details in the handoff/ledger and use existing requirements fields
for genuine hard constraints and verified bindings.

When capacity is uncertain, inspect actual status or make one bounded authorized
creation attempt. Waiting based only on a guessed slot limit is not a capability
blocker. After creation is accepted, track the task's actual reply or concrete
failure; an acceptance receipt alone is not successful execution. A real refusal
must retain its reason and the affected next action.

Fresh workers query only their own task subtree, for example list_agents with
their canonical task path as path_prefix when the host supports that filter.
The parent handles global capacity and returns only counts/availability. Full
team status may contain other branches' answers even without opening their
files. Preserve accidental exposure, restrict later queries, and lower blind or
independent-evaluation claims accordingly. This is a context-handling method,
not a filesystem or provider security guarantee.

## Project task completion

For program mode, finish an attempt through projectctl.py using its current
accepted result object. Each result binds an acceptance ID, status, evidence
level, and evidence path/hash records. For a bound state, results also include
the evaluation_plan_hash present when the attempt began. Match every required
assertion's level to the actual check; a review cannot replace runtime evidence.
Keep raw logs, outputs, screenshots, receipts, and per-case results available
for inspection. Hashes establish byte identity only, not authorship or truth.

Run meaningful software and agent-infrastructure acceptance in the real
available runtime. If credentials or a model provider are unavailable, run an
explicit local stub or command worker and label what it proves. Project-plan
validation, coverage-matrix validation, package compilation, or completed
project status alone cannot establish that the delivered system works. Inspect
the frozen product cases and runtime evidence before claiming product acceptance.

## Skill development roles

Use coordinator-owned authorship for creating or maintaining reusable skills.
The coordinator derives requirements, selects architecture and boundaries,
authors the reusable method and contracts, decides which observations generalize,
repairs the skill, integrates results and saves the final version. Keep ordinary
application implementation separate from skill authorship; authorized workers
can still build scoped prototypes, scaffolds or test fixtures.

Use an available Luna worker for website search, source research and material
collection. Frontend/interaction preprocessing may extract observed regions,
navigation, component states, semantic token candidates and transitions; compute
selected source-value contrasts; or propose reference comparisons and open
questions. Keep observations, interpretations and proposals labeled separately.
Record URLs, access date, actual readable scope, exact revision and reuse terms
when relevant. Do not turn a source's existence or a worker recommendation into
an accepted architecture, platform rule or target-app result.

Assign research workers their own output paths and no skill editing scope.
The coordinator checks source support, applicability, contradictions and unknowns
before adopting material, then writes the final design. When those source facts
are unstable or material, verify them with the appropriate current source.
For interface research, use the research packet contract in the independent
design skill's design-references guide.

After authoring, give a fresh validator the frozen candidate, raw task and
required evidence scope. Keep author conclusions and holdouts out of forward
tasks; validation outputs and fixtures may have separate write paths, while
skill repairs remain with the coordinator. Record later known-finding rechecks
as targeted rather than blind validation. Block only unavailable checks and
do not add user approval gates for routine research, synthesis or repair.
