# Executable program-mode acceptance

Contents: Adapter and frozen cases · Run and assess · Repairs and recovery · Limits.

Read this when a program-mode product can be exercised through a local process.
Use the actual browser/device runner for interface behavior; this adapter does
not replace it. Keep the existing flow factory unchanged.

## Adapter and frozen cases

Build a narrow product adapter, separate from the grader. It reads one JSON
object on stdin: `{ "case_id": "safe_case_id", "inputs": { ... } }`.
It invokes the actual application/service, then emits exactly
`{ "status": "completed|failed|blocked", "output": { ... } }` on stdout.
Put diagnostics on stderr. For a deliberate rejected request, the adapter can
exit zero and report product status `failed`; a crashing adapter always fails
acceptance, even when product rejection was expected. Keep it in the foreground.

Freeze a complete `forge-eval/1` plan before using implementation evidence.
`case.expected` is the exact full expected `output` object, including fields
needed to establish durable effects, explanations and recovery. Use deterministic
identities or normalize unstable timestamps in the adapter; explain normalization
and retain raw product results where useful. Do not remove a difficult assertion
or normalize away a defect to obtain a pass. An adapter that simply returns case
inputs does not establish application behavior. Do not supply expected values or
grader code as runtime inputs to the product.

Make each case self-contained, or explicitly declare shared-state dependencies
and their starting state in the brief. The runner executes plan order using a
fresh process per case, but the adapter owns database setup and cleanup. Bind
the adapter and application source with repeated `--candidate-file`; include
configuration/schema files that affect the result. Retain an immutable revision
or source snapshot before repair. The manifest checks declared files only.

## Run and assess

```text
caserunner.py run EVAL_PLAN --cwd PROJECT_ROOT --candidate-file ADAPTER --candidate-file PRODUCT_SOURCE --output-dir NEW_RUN_DIR --timeout 30 --command python3 ADAPTER
caserunner.py assess EVAL_PLAN NEW_RUN_DIR/report.json
projectctl.py assess --state STATE --report NEW_RUN_DIR/report.json
projectctl.py status --state STATE
projectctl.py next --state STATE
```

Put `--command` last. Use absolute adapter/source paths and a new output directory
for every run. The runner executes an authorized command without a shell, sends
only case ID and inputs, and preserves input, stdout, stderr, exit code, elapsed
time, source manifest, report and assessment. It also copies declared candidate
files into `source-snapshot/` before execution; the snapshot manifest links their
original and saved paths/hashes. Capture failure stops before cases. Use these
bytes to reproduce an old candidate; they do not allow an old verdict to verify
a changed current source. It runs every case, including
optional cases; required cases determine the verdict. A timeout kills the process
group on POSIX; other platforms kill the direct process. JSON parse errors,
duplicate keys, nonfinite numbers, unexpected fields, nonzero exits, timeouts and
wrong full output/status fail. Output JSON above 8 MiB cannot be graded; this is
a parsing cap, not an OS disk/CPU quota.

Machine criteria use exact JSON comparison. A matching case with any human
criterion reports `needs_review`; do not turn aesthetic or semantic judgment
into an automatic pass by changing its kind. Maintain separate attributable
review evidence; this runner has no human-review override. Empty expected objects
test only the product status, so inspect whether that is enough for the criterion.

`projectctl assess` recomputes from raw checked evidence, records the report
reference and task fingerprint, and preserves prior assessments. Task completion
alone still reports `not_assessed`. A verified matching report yields `pass` only
after required tasks are done; otherwise it reports `pending_tasks`. Missing,
changed or unreadable evidence/source reports `unverified`. Changed plans or
task attempts report `stale`; do a new run after integration. `next` returns
`needs_acceptance`, `needs_review` or `acceptance_failed` instead of `completed`
for a bound project without a passing product verdict. The structural state
field `status=completed` remains backward compatible; report the separate
product verdict alongside it.

## Repairs and recovery

Inspect failed required cases and `next.acceptance_repairs`. Preserve the
tested candidate and original outputs first. For an already-done task implicated
by current failed cases:

```text
projectctl.py reopen --state STATE --task TASK --reason OBSERVED_FAILURE_AND_REPAIR
```

This keeps the frozen plan and old attempts, invalidates completed downstream
work, and consumes one of the task's two repair attempts. Reconcile any active
dependent attempt first. Begin the reopened task, repair, finish with current
evidence, rerun all cases into a new directory, and attach the report. When the
budget is exhausted, retain unresolved failure and its next action. Do not use
a new automatic repair attempt; the next view reports exhausted budgets and
blocks when all failed cases have exhausted their mapped tasks. Do not use
a no-content plan revision to reset attempts. Use `revise` for actual requirement
or acceptance changes, with its existing explicit invalidation rules.

If a run is interrupted, inspect its directory and current processes before
retrying; absence of a final report is incomplete execution. Partial files are
not a passing run. Reconcile non-idempotent effects in the application before a
new run. Keep unrelated ready work moving.

## Limits

This is a local product-command runner plus host-driven project feedback. It
does not dispatch model providers, enforce worker permissions, authenticate
logs/receipts, prove undeclared dependencies or production readiness, or judge
visuals/usability. Hashes detect drift of declared local bytes; a producer can
still fabricate a complete report. Use independent raw-task review and actual
product outcomes to assess the adapter and case design. Record tokens/cost as
null when host telemetry is unavailable.
