# C2 native-worker recording protocol

This protocol applies to newly frozen measured runs. Never reinterpret C1 or
replay historical workers. Root authors contracts, code, integration and final
grading; a fresh Luna/max performs a bounded ordinary task. A separate source
review must grade the original requirements before commit.

## Freeze before the call

Save the source/candidate hashes, concrete business inputs and requirements,
read/write scopes, correction and query budgets, stage definitions, and the
coordinator's exact ready-to-run first command. Use only verified host settings.
Record unknown provider identity, active model time, tokens and cost as null.

The worker prompt begins with an exact command using `scripts/capture.py cli`.
Its unique record path is inside the worker write directory; the target reads
the immutable request, this protocol and the raw task inputs. The worker must
execute that command before other shell commands. Reading host tool metadata is
not a subprocess. The first captured read is bootstrap overhead and precedes
worker_work; it is neither missing work time nor invented model start time.

## Command boundary

Every invoked target subprocess, including marker creation, failed commands,
reply authoring and preflight, has an argv, cwd, raw stdout/stderr bytes, exit
status, UTC and boot-bound monotonic start/end. The outer capture wrapper is the
instrumentation boundary and is excluded; do not recursively capture wrappers.
Child subprocesses created by a target are within its aggregate span, not
separate measured targets. Do not claim full system tracing.

Use the same wrapper for marker targets:

```text
python3 CAPTURE cli --record WORKER/logs/UNIQUE.json --actor worker -- \
  python3 CAPTURE mark --events WORKER/events --actor worker \
  --stage worker_work --event begin
```

Use `worker` or `coordinator` as actor; bind the native task identity separately.
Pure file-tool operations must be disclosed, with their actual paths; they are
not CLI events. Native calls require their own before-call intent and verbatim
return records. A shell log or a copied JSON payload is not authenticated proof
of a native call. Never log secrets. Discover records by schema, not extension.

Capture a target launch error as a failed target with exit 127 and the concrete
error. Reserve a capture destination before running its target: an existing
record must reject execution without repeating effects. A started record with
no end is interrupted/unknown, not a zero-duration or successful command.

## Stages and lifecycle

Record worker_work begin before business processing and end after business
outputs; record worker_reply begin before the incomplete reply draft, and end
after the final successful captured check-reply. Preserve draft and final files.
Coordinator setup spans state/work preparation to issue. Receive begins before
polling and ends only after original bridge receive. Review, decision and commit
each have separate begin/end markers. Preflight is not semantic grading.

Persist intent before one actual native create; import that returned task name
with `accepted`. Import each actual running snapshot with `observe` before
further polling. Only a completed snapshot may drive `receive`. Then inspect
raw source and artifacts, preserve independent review, create and fill a
separate decision draft, check-decision, commit and reconcile. Keep all failed
calls. Unknown creation results require reconciliation, never a second spawn.

Use bounded notification waits (at most 45 seconds each), preserving arguments
and actual returns. They consume no status-query budget and are not terminal
proof. Reserve a final status query. Once the frozen query limit is exhausted,
retain unknown/running; do not use another actor to evade it. Same-boot ordered
marker intervals are elapsed spans including tool/wait gaps. Missing, reversed,
duplicate or cross-boot boundaries are unverified/null, never speed data.

## Scope and corrections

Worker reads only its request, bound raw inputs and declared public code/protocol.
All outputs, logs, drafts, scripts and markers stay within assigned work paths.
No sibling results, coordinator decisions/control state, global status, spawn,
followup, interrupt, delegation, network or external effects. Parent messaging
is limited to its own task's status and completion. These are instruction-level
constraints unless the host independently enforces and tests an allowlist.

Count every corrective attempt within worker and coordinator scope, including
analysis, readers and indexes, not just business output changes. Freeze any
administrative exclusions beforehand. Distinguish nonzero commands, defects and
actual repairs. Keep the first failing candidate and report, change rationale,
new source hash and post-fix verification. At most two repairs per candidate
actor. No new worker, changed sample, weakened criterion or renamed candidate
may reset the same repair budget. Preserve accidental exposure and limit claims.

First qualify recorder success, failed markers, non-UTF-8 bytes, launch failure,
and exclusive destination handling. Then run a fresh ordinary worker through
the original bridge. Record conformance separately from business acceptance.
Only a separately frozen later study can address performance; SDK, global quotas,
natural network failures, external effects and real UI each need their own cases.
