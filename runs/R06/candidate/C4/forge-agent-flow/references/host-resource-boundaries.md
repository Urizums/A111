# Local capacity and wait deadlines

Contents: [Admission](#admission) · [Deadline](#deadline) · [Recovery](#recovery).

Keep the bridge's request, reply, acceptance and checkpoint protocols unchanged.
Use these options only with an actual host-agent driver; Python does not execute
native tools. Neither option measures token cost or provider-wide capacity.

## Admission

Initialize one explicit registry before binding cooperating drivers:

```text
python3 "$FORGE_SKILL_DIR/scripts/hostcapacity.py" init --registry REGISTRY --limit 1
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" init --driver DRIVER --kind project --state STATE --works WORK_MAP --parent YOUR_TASK_PATH --registry REGISTRY
python3 "$FORGE_SKILL_DIR/scripts/hostcapacity.py" status --registry REGISTRY
```

Use an absolute registry path outside every worker write scope. The driver
binds its identity and limit. Do not edit them during a run. Driver, checkpoint
and registry locks coordinate local cooperating POSIX processes; this is not a
distributed lease or a security sandbox.

The registry counts **active worker slots**, across different checkpoints.
Before granting a spawn call, claim durably reserves the bound job/attempt,
worker and action. If no slot is available, claim returns `call_allowed:false`
and `status:waiting_capacity`. Wait, then claim that same proposed action; do
not create a new driver, action, attempt or child. Waiting does not consume a
call claim or start its deadline. A proposed action alone never permits a call.

An unknown creation effect or missing/unknown host entry holds its slot. No age
or silence releases it. Import an actual completed/failed/interrupted snapshot,
or an actual creation error return, through the original driver. Release uses
only that attempt's terminal ledger receipt and verifies its worker/request.
Worker completion can release the active-worker slot while source review is
pending; the original checkpoint still requires its original decision/commit.
Keep the receipt files intact after release. Untracked workers and drivers
without this registry are outside its count.

## Deadline

Set `--deadline-seconds SECONDS` to a positive finite duration when initializing
the driver. Use `--deadline-policy observe` (default) or `interrupt`. Interrupt
requires a deadline. These options are immutable and off on existing ordinary
runs. A duration begins at the durable granted spawn claim, not provider start,
and covers missing creation returns as well as accepted/running work.

Persist Linux boot identity, monotonic start and deadline, and a UTC observation
label. New CLI processes on the same boot keep the original start. On changed
boot identity or a backwards monotonic clock, reconcile; never infer expiry
from wall time or silently restart the duration. This is a local wait cutoff,
not a provider runtime timeout or guaranteed interruption latency.

At/after the cutoff, query the exact worker first. `observe` keeps waiting and
preserves a completion observed after the cutoff for ordinary source review.
The recorded time is the local import observation, not a provider event time.
For `interrupt`, an actual running snapshot from a query **claimed at/after
the cutoff** permits one `collaboration.interrupt_agent` action for that worker.
Persist that query's claim clock. A query claimed before the cutoff, even if its
return is imported late, requires a new post-cutoff query before interruption.
An older record without a query claim clock also requires a new query. Claim it, call the
native tool directly, save its actual JSON return and acknowledge it as usual.
The returned previous status or command success does not close the job or
release its slot. Query again; an actual failed/interrupted snapshot terminates
the attempt, while a completed race still needs its valid reply and source review.

## Recovery

If the interrupt return is missing, next queries the bound worker and never
issues a second interrupt for that attempt. Unknown status remains unresolved.
Ordinary call/poll limits still apply; reaching them does not release capacity
or assert a terminal state. Reconcile outstanding effects before explicit new
attempts. Failed attempts do not automatically retry or schedule more work.

The registry reservation precedes durable claim authorization. A crash between
those writes reuses the same reservation before granting the original call.
A durable claimed call with unknown effects must query, never respawn. A crash
between bridge terminal import, registry release and driver acknowledgement
replays the saved private ack and the same release proof. These are local
idempotent recovery steps, not an atomic transaction with the external tool.
