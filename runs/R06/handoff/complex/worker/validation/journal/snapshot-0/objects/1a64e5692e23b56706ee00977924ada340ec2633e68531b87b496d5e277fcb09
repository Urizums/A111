# Host reply and decision drafts

Contents: [Worker](#worker-reply) · [Coordinator](#coordinator-decision) · [Preflight](#read-only-preflight) · [Limits](#boundaries).

Use `scripts/hostdraft.py` inside an existing host bridge loop when identity,
hash and acceptance-row authoring would otherwise be manual. Keep ordinary
one-time tasks on their proportional direct path. The bridge still constructs
the request and owns lifecycle state; this helper does not call tools, claim an
action, receive a reply, recover a journal or commit a checkpoint.

## Worker reply

Read the original prepared `request.json`, do the actual work and write its
business files within assigned scopes. Create a new draft:

```bash
python3 "$FORGE_SKILL_DIR/scripts/hostdraft.py" reply \
  --request "$REQUEST" --artifact "$ACTUAL_OUTPUT" --out "$NEW_DRAFT"
```

Repeat `--artifact` for real files, or omit it before files exist. The helper
copies job/attempt/request identity and hashes only existing regular in-scope
files. It rejects bound-input drift or newly appeared declared-absent input,
missing files, scope escapes, reply self-reference and existing destinations.
It does not infer file paths from arbitrary strings in `inputs`.

Outer `outcome` stays null. Project `result` stays null. Package `result` keeps
the original inner invocation, null outcome, empty artifacts/evidence; optional
`--flow-outcome DECLARED_OUTCOME` uses the existing Flow template to scaffold
that explicitly chosen branch's names/types. Business values and real evidence
remain empty. Host task outcome and inner Flow outcome are distinct.

Retain that draft and create the assigned `work.reply_path` by filling actual
`done`/`failed`, result, artifacts and real failure reason as applicable. Do not
add outer `invocation_id` or metadata fields. A package inner result has exactly
`invocation_id`, `outcome`, `artifacts`, `evidence`; outer artifacts are path/SHA
references. Run preflight before reporting completion. An unchanged draft is
rejected by the original receive protocol.

## Coordinator decision

After actual completion and original bridge receive, generate a separate file:

```bash
python3 "$FORGE_SKILL_DIR/scripts/hostdraft.py" decision \
  --job "$JOB" --evidence "$ACTUAL_REVIEW_FILE" --out "$NEW_DECISION_DRAFT"
```

Project rows use original acceptance IDs, minimum levels and the authoritative
embedded evaluation-plan lock, when present. Their statuses stay `not_run` and
outer outcome stays null. Optional repeated `--evidence` hashes actual evidence
files as candidates for each row; select evidence that supports each assertion
after independent review. Shared candidate hashes are not coverage or grades.

Package results copy the exact captured worker Flow response. Do not supply
`--evidence` for package decisions or alter that response to repair a bad reply.
Package-wide case assessment remains separate. Independently check actual
sources/requirements, preserve the draft, and write a final decision reflecting
the real review. Failed/blocked decisions need null results and a real reason
with next action. Generated drafts never set `pass` or `done`.

Decision helpers require settled `received` state, verify original refs and
checkpoint, and reject unreceived/committed jobs or pending journals without
recovery. They cannot replace bridge metadata, checkpoint, protected source or
an existing destination. Use the original inspect/resume/reconciliation path
when needed; do not regenerate bindings to conceal drift.

## Read-only preflight

```bash
python3 "$FORGE_SKILL_DIR/scripts/hostdraft.py" check-reply \
  --request "$REQUEST" --reply "$ASSIGNED_REPLY"
python3 "$FORGE_SKILL_DIR/scripts/hostdraft.py" check-decision \
  --job "$JOB" --decision "$FINAL_DECISION"
```

Both use strict finite duplicate-free JSON. Reply check reuses existing outer
identity/outcome/artifact validation; it returns `payload_valid`. It does not
check actual native completion or advance the package's inner response. Decision
check invokes the original pure `commit_plan`; it returns `controller_compatible`
without executing its images. It verifies original controller compatibility,
not whether the coordinator's semantic conclusion is true. Reports always deny
automatic host calls and do not grant a claim. Invalid data exits 2 with
`invalid`; unreadable evidence exits 2 with `unavailable`. Fix the actual missing
material, not its frozen hash. The original receive/commit checks still apply
after preflight, including evidence changes occurring later.

## Boundaries

Draft output creation is exclusive/atomic through the existing template writer.
Preflight writes no business/state bytes; it never replays a journal. Files and
requests are local cooperating-writer evidence, not authenticated receipts,
distributed leases or a filesystem sandbox. A request file alone cannot prove
its invocation is still current; decision/controller checks use original state.
Successful hashes or protocol compatibility are not independent acceptance.
Measure actual workflow overhead in comparable trials before claiming a speed
improvement; unavailable token/cost telemetry remains null.
