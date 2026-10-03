# Host-driven worker bridge

Contents: [Prepare](#prepare-and-issue-once) · [Observations](#import-actual-host-observations-and-reply) · [Acceptance](#coordinator-acceptance-and-commit) · [Restart](#rejection-interruption-and-restart).

Use `scripts/hostbridge.py` for a project task or an existing package node when
the host can actually create workers and report their status. This is a POSIX
local bridge driven by a cooperating host coordinator; it does not embed a
provider SDK, authenticate a model, or automatically call collaboration tools.
It preserves projectctl/packagectl schemas and uses runledger for receipts.
For an autonomous host-agent loop over ready work, read
[host-driver.md](host-driver.md); its typed actions retain this bridge as state
owner and still require actual native host calls and independent source review.

## Prepare and issue once

Create `work.json` with `prompt`, JSON `inputs`, absolute directory `write_paths`
and absolute `reply_path`. Optional `input_files` holds `{path, sha256}` references
for files the task reads. Use `sha256: null` to bind intentional absence. Embed
small raw input data directly; bind referenced file bytes explicitly. The bridge
does not infer that arbitrary strings in inputs are file paths.

Project task scopes resolve relative to the checkpoint directory. Work scopes
must stay within them and exclude the checkpoint, bridge metadata and read-only
inputs. Package scopes, when nonempty, currently need absolute host mapping;
relative package scopes are blocked rather than guessed. The current adapter
supports `host_default` or explicitly requested `gpt-6-luna`, using Luna/max with
fresh context. Other explicit model mappings require another verified adapter.

```text
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" prepare --kind project --state STATE --task TASK --work WORK --job NEW_JOB_DIRECTORY --parent YOUR_TASK_PATH
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" prepare --kind package --state STATE --package PACKAGE --work WORK --job NEW_JOB_DIRECTORY --parent YOUR_TASK_PATH
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" issue --job JOB_DIRECTORY
```

`prepare` preserves an immutable request and reserves one unresolved host job
per checkpoint. For a project it starts the bound attempt; for a package it uses
the current ready invocation without advancing it. Repeated same-job prepare is
idempotent; changed input needs a new binding. `issue` persists dispatch intent
and returns `spawn_arguments` and the task-local status query. **The coordinator
must call the actual host creation tool once**, using those exact arguments, and
save its raw return. If interrupted after calling but before recording the
receipt, inspect that exact host subtree; never reissue based on silence.

## Import actual host observations and reply

```text
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" accepted --job JOB --receipt CREATE_TOOL_RETURN
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" recover-accepted --job JOB --receipt ACTUAL_BOUND_WORKER_STATUS
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" observe --job JOB --receipt OWN_SUBTREE_STATUS
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" receive --job JOB --receipt COMPLETED_SUBTREE_STATUS --reply REPLY
```

The current collaboration adapter expects an accepted `{task_name}` return and
status `{agents: [{agent_name, agent_status}]}` for the bound worker. It does not
invent a failure from a missing, unknown or running status. A completed snapshot
can establish the running-to-completed transition without claiming a measured
start time. Accepted means the request is recorded, not that the task is done.
Raw local JSON imports are not independently authenticated host/provider events;
the host coordinator must preserve real tool calls, not fabricate receipts.
Use `recover-accepted` only after an unresolved issue when the actual status
snapshot contains exactly the bound worker. It records status reconciliation
as the acceptance origin and retains that status evidence; it does not invent
a creation-tool return. Absence and unsupported status cannot recover a job.

The worker writes the assigned path with this wrapper, outside the unchanged
Flow/project result protocols:

```json
{
  "schema_version": "forge-host-reply/1",
  "job_id": "FROM_REQUEST", "attempt_id": "FROM_REQUEST",
  "request_hash": "FROM_ENVELOPE",
  "outcome": "done", "result": {},
  "artifacts": [{"path": "ABSOLUTE_ASSIGNED_FILE", "sha256": "ACTUAL_FILE_HASH"}],
  "reason": null
}
```

For package work, `result` has exactly `invocation_id`, `outcome`, `artifacts`
and `evidence`. The invocation ID comes from the dispatch; outcome is one of its
declared outcomes; artifacts maps that outcome's emitted names to business
values; evidence is a nonempty list of actual output/blocker reference strings.
The dispatch's business schema applies to those artifact values. The outer
host `artifacts` remains file references with path/SHA256. The request includes
this response contract and issue supplies it to a fresh worker. For project
work, result is the task output.
An actual task error uses `outcome: failed` with its real reason and next action.
A completed host context can contain a failed task; these statuses stay distinct.
Use [host-drafts.md](host-drafts.md) to generate identity/hash scaffolds and
preflight final files without receiving or committing. Preserve the initial
draft separately and fill results from actual work; null outcomes cannot submit.

## Coordinator acceptance and commit

Independently check actual output against its sources/requirements. Write a
`forge-host-decision/1` object containing `request_hash`, current
`reply_sha256`, `outcome`, `results` and `reason`. Project results use the original
projectctl acceptance_results and its evaluation_plan_hash when bound. Package
acceptance results must equal the actual worker Flow response. For a rejected
package result, use `failed` or `blocked`, null results and an explicit reason
with the reconciliation next action. This closes the host attempt while keeping
the original checkpoint bytes and ready Flow invocation. It cannot turn a bad
reply into an advance. A passing self-claim or a
valid hash is not a semantic grader. Regrade or review using the required method.

```text
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" commit --job JOB --decision COORDINATOR_DECISION
python3 "$FORGE_SKILL_DIR/scripts/hostbridge.py" reconcile --job JOB
```

Commit checks request/reply/evidence identity and submits through the original
controller. Identical duplicate commits return the prior record without another
state advance. Different decisions, stale replies or changed evidence fail
closed. Reconcile verifies saved data and returns the next action; it does not
create a worker or automatically retry.

## Rejection, interruption and restart

Use `rejected --job JOB --receipt ERROR_RETURN --reason REASON_AND_NEXT_ACTION`
only for a saved creation error (no accepted worker), and
`terminate --job JOB --receipt TERMINAL_HOST_STATUS --reason REASON_AND_NEXT_ACTION`
only for an observed failed/interrupted worker. Do not claim a control-tool
acknowledgment is terminal status unless the host actually reports it. Both keep
old receipts; a project failure finishes that attempt as failed. A new eligible
project attempt uses a new job directory and reconciled effects, preserving its
two-repair bound. Use fresh output paths that cannot overwrite retained prior
reply/artifact evidence. Raw worker replies are also copied into private bridge
receipt storage. A failed package result or host interruption retains the
original checkpoint. Reconcile effects and decide explicitly whether to retry
the still-ready invocation in a new host job or start a new flow run. Rejection
counts toward the same two-repair host bound, including worker-reported success
that fails coordinator acceptance. Valid Flow error/blocked outcomes still use
the original Flow response through packagectl; host rejection is distinct.

The bridge writes a guarded local transaction journal before checkpoint,
ledger/control updates, guarding package bytes as well as result evidence.
Restart verifies evidence before writing and applies only matching old
or intended new images. Conflicting writes are not overwritten. Keep one
cooperating coordinator per checkpoint; direct controller writers must not race
the bridge. The lock is local POSIX admission, not a distributed lease, filesystem
permission sandbox or atomic transaction with external tool effects. Later
legitimate checkpoint changes make an old job non-reusable; its receipt history
remains available. File durability depends on local filesystem fsync semantics.

Resource scope is one active host job per checkpoint. No global capacity,
wall-time limit or token ceiling is enforced. Capture actual host timings where
available and retain unavailable model identity, tokens and cost as unknown/null.
