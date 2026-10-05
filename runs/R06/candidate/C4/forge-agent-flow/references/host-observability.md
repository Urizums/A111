# Inspect and resume the original host run

Contents: [Inspect](#inspect) · [Resume](#resume) · [Evidence limits](#evidence-limits).

Use these commands when continuing a saved host-driver run. Keep the original
driver, checkpoint, work map, input bindings and acceptance. Do not recreate a
run because a host notification or creation return is absent.

## Inspect

```text
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" inspect --driver DRIVER
```

Inspect returns `forge-host-inspection/1`: saved run identity, phase/reason,
current original target and bound worker, pending action identity/status,
remaining action/poll counts, capacity summary and own slot, deadline/clock
observations, and `next_required_step`. It never authorizes a native call.

It validates the saved configuration, immutable work/action/ack references,
and a settled bridge's request, ledger and checkpoint bindings. A pending
bridge transaction is reported without replay; `bridge_validation` remains
pending recovery. No prepare, claim, acknowledgement, capacity release or
expiry observation is persisted. Run/checkpoint/output JSON bytes remain
unchanged; ordinary cooperating POSIX lock-file bookkeeping is permitted.

The capacity view exposes aggregate local counts and this run's own slot,
not other workers' tasks/results. Treat it as an observation, not admission:
only the original action claim grants a call. Deadline elapsed/remaining
seconds are local same-boot monotonic observations. Changed boot, backwards
or unavailable clock is explicit, with durations unknown; inspect does not
reset a clock, infer terminal status, or authorize interruption.

| Next required step | Coordinator action |
| --- | --- |
| `resume_original_controller`, `resume_terminal_record` | Resume the same run; do not create a replacement checkpoint. |
| `claim_pending_action` | Claim that saved action, then perform the returned tool once only if allowed. |
| `wait_capacity` | Wait for actual terminal release, then claim the same pending action. |
| `reconcile_claimed_action` | Resume to query/reconcile the bound worker; do not repeat the earlier tool. |
| `replay_saved_ack`, `resume_saved_transaction` | Resume the original private local intent; never call the native tool again for that intent. |
| `query_bound_worker`, `source_review` | Resume to expose the matching typed action; claim before execution. |
| `reconcile_clock`, `explicit_reconciliation` | Inspect the precise clock/failure/budget/evidence reason and reconcile it; resume does not clear it. |
| `reconcile_invalid_review_ack` | Preserve the invalid ack and use explicit `retry-review` with the same run/action, then independently regrade the original sources. |
| `reconcile_review_evidence` | Restore authentic unavailable review evidence; do not discard a potentially valid intent. |
| `completed` | Reuse the original completed controller result and retained evidence. |

If a required file/hash is unavailable or drifted, the CLI fails closed with
`reconcile_required`. Restore authentic original evidence or report the exact
unavailable history. Do not manufacture receipts, rehash modified inputs to
make an old run appear valid, or infer that an uncertain worker is terminated.

## Resume

```text
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" resume --driver DRIVER --expect-run SAVED_RUN_ID
```

Take `SAVED_RUN_ID` from the inspected original run. A mismatch fails before
mutation. Resume performs one bounded invocation of the existing `next`
recovery/scheduling path. It can finish a saved ack/bridge transaction and
expose at most one proposed action, but grants no native call by itself.
Continue the unchanged claim → actual native call/source review → ack loop in
[host-driver.md](host-driver.md). A claimed creation without a return becomes
an exact bound-worker query; a claimed interruption never repeats.

The same saved budgets, configuration, request/attempt identity and acceptance
apply. Resume does not refill calls, reset deadlines, retry failed business
tasks, or unblock a failed run. For explicit new attempts use the existing
bridge failure-recovery protocol only after reconciling effects and inputs,
with bounded repair count and fresh output paths. Keep prior failures.

If a submitted local source-review decision fails deterministic validation
before commit, inspect reports `review_ack_validation:invalid`. Use:

```text
python3 "$FORGE_SKILL_DIR/scripts/hostdriver.py" retry-review --driver DRIVER --expect-run SAVED_RUN_ID --action OLD_REVIEW_ACTION --reason RECONCILIATION_REASON
```

This requires the same active pending `ack_pending` review, a valid settled
bridge still at `received`, exact action/request binding, no pending bridge
journal, and a deterministic validation error. It retains the original private
ack and validation/reconciliation reasons, marks that action `rejected_ack`,
and clears only its pending pointer. Resume then proposes a new review under
the original budget. Recompute the new decision from authentic unchanged
inputs, reply and acceptance; use a distinct decision file. No worker is
respawned, no attempt restarted, and no checkpoint success is inferred.

A valid ack must replay; unavailable I/O or a pending/committed transaction
cannot be discarded through this command. Native actions cannot use it. A
later different ack still cannot overwrite the rejected original action.

## Evidence limits

Inspect is a cooperating local snapshot, not live host status, a provider
timeout, a distributed lease or a proof of external-effect idempotency. Actual
worker lifecycle still needs actual native returns through the driver. Worker
completed still needs original source review and commit. Product case
acceptance remains distinct from structural controller completion. Tokens,
cost and internal model identity remain unknown unless independently supplied.
