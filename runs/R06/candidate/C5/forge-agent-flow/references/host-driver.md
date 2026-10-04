# Persistent host-agent driver

Contents: [Bind the run](#bind-the-run) · [Execute continuously](#execute-continuously) · [Recover without repeating effects](#recover-without-repeating-effects).

Use `scripts/hostdriver.py` when an autonomous host agent should continuously
consume project-ready tasks or existing package nodes through the actual native
collaboration tools. Use the smaller bridge directly for a single explicitly
managed attempt. Read [host-bridge.md](host-bridge.md) for the unchanged worker
reply and coordinator decision protocols.

For continuation, read [host-observability.md](host-observability.md): use
`inspect` for a read-only progress/budget/recovery view and `resume` with the
original run ID. Neither command authorizes a native tool call by itself.

The driver schedules and validates typed actions; **the host agent executes
them**. Python does not embed a provider SDK or call collaboration tools. Keep
one cooperating coordinator per checkpoint and bind `--parent` to the actual
caller's canonical task path. Use Luna/max/fresh as currently supported by the
bridge. A tool's accepted settings do not independently prove internal model
identity. No background daemon or human approval between ordinary steps is
needed; the current host agent runs the loop until completion or a real blocker.

## Bind the run

Initialize the original project through projectctl, or start the supplied
package through packagectl. Preserve its plan, acceptance and original state.
Prepare a JSON work map from original task/node IDs to **absolute** work-template
paths. Each template uses the bridge's prompt, inputs, input_files, write_paths
and reply_path. Give each task a disjoint output directory outside driver and
checkpoint metadata; project scopes remain relative to the checkpoint directory.

Use literal input hashes or explicit absent input declarations as usual. For a
dependency output that does not exist before its producing task finishes, use
`{"path":"/absolute/dependency/output.json","sha256":"at_dispatch"}`.
This opt-in sentinel is resolved once when that original task becomes ready;
the derived work/request then freezes the actual bytes or absence. It does not
guess paths from arbitrary strings. Keep templates and the work map immutable.

```text
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" init --driver DRIVER --kind project --state STATE --works WORK_MAP --parent YOUR_TASK_PATH
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" init --driver DRIVER --kind package --state STATE --package PACKAGE --works WORK_MAP --parent YOUR_TASK_PATH
```

Default limits are 50 action claims per run and 20 status-query claims per job;
set `--max-actions` and `--max-polls` at initialization when appropriate. These
are enforced local call permissions, counting even a claimed call whose return
is unknown. They are not token, wall-time, global capacity or provider limits.
Read [host-resource-boundaries.md](host-resource-boundaries.md) to opt into
local shared capacity with `--registry`, or a claim-start wait cutoff with
`--deadline-seconds` and `--deadline-policy`. Both are off by default.

## Execute continuously

1. Call `next --driver DRIVER`. Retain the action ID, immutable action path and
   SHA256. Repeating next while the action is proposed returns that same action.
2. Call `claim --driver DRIVER --action ACTION_ID`. Proceed only when
   `call_allowed` is true. Perform exactly the returned tool and arguments once.
   A repeated claim returns false and never grants another tool call. Do not
   call next between a successful claim and its actual call/ack.
3. For `collaboration.spawn_agent`, `collaboration.list_agents`, or an emitted
   `collaboration.interrupt_agent`, call the
   native tool directly in the host context. Save its **actual raw JSON return**
   and run `ack --driver DRIVER --action ACTION_ID --receipt RAW_RETURN`.
   Do not fabricate a host event or treat an action as proof of execution.
4. For `coordinator.source_review`, independently inspect the supplied request,
   source material, actual reply/artifacts and original requirements. Write the
   unchanged `forge-host-decision/1` protocol and run
   `ack --driver DRIVER --action ACTION_ID --decision DECISION`. Project success
   needs original acceptance_results and any bound evaluation-plan hash.
   Package success submits the actual inner Flow response after source review.
   Host completed is not acceptance, and worker self-claims are not grading.
5. Repeat next. After a passing commit it selects the following ready original
   target, without another user prompt. For running workers, wait for a host
   notification before repeated queries; keep progress updates and avoid busy
   polling. Completed returns the original controller result. Preserve product
   acceptance status separately from structural project completion.

```text
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" next --driver DRIVER
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" claim --driver DRIVER --action ACTION_ID
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" ack --driver DRIVER --action ACTION_ID --receipt RAW_RETURN
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" ack --driver DRIVER --action ACTION_ID --decision DECISION
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" status --driver DRIVER
```

## Recover without repeating effects

A claimed spawn with no imported return is uncertain. On next, the driver
issues an exact bound-worker status query, never another spawn. If the actual
snapshot contains exactly that worker with a supported lifecycle status, the
bridge records acceptance origin `host_status_reconciliation`, retains that
snapshot, and continues observing/receiving. It does not synthesize a creation
return. Missing, duplicate or unknown entries remain inconclusive; the driver
retains rejected imports and requires reconciliation. Do not convert silence
into failure or retry. A late create return cannot overwrite a newer action.

Every ack is copied and persisted as `ack_pending` before bridge mutation. A
new CLI process finishes that same intent after a bridge/driver update gap;
it does not call the host again. Identical ack bytes reuse the record; different
acks fail closed. A provably invalid local review ack that never committed
can be retained and explicitly rejected with `retry-review`, under the exact
run/action and no-pending-transaction guards in host-observability.md; a new
review action still consumes the original budget. Native/valid/committed acks
cannot use that path. If a completed snapshot arrives before a valid reply exists,
the pending import remains blocked for evidence reconciliation. Keep old files
and failed results. Do not modify a committed reply or acceptance decision.

Actual host failure, creation error or failed coordinator acceptance closes the
attempt and stops automatic scheduling. Resolve effects/input and choose an
explicit bounded new attempt with fresh output paths using the bridge recovery
protocol; this slice does not autonomously retry failed tasks. Exhausted call
limits also stop new calls and do not imply the worker has terminated.

Driver metadata has a local POSIX lock. The bridge remains checkpoint state
owner and checks request/input/package/evidence hashes and guarded transactions.
Keep direct controller writers from racing it. This is local cooperating-agent
durability, not an authenticated security sandbox, distributed lease or atomic
transaction with an external tool. An optional deadline emits a native interrupt
after an actual post-cutoff running observation; only a later actual terminal
snapshot closes the worker. A local registry coordinates cooperating driver
admission, not provider capacity. Provider runtime timeout, natural delayed
returns, token accounting, provider-wide concurrency and external business effects
need separately observed adapters and acceptance.
