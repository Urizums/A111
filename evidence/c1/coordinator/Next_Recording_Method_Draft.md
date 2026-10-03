# Proposed next recording method — not applied to C1

Root-authored draft only. C1 source, observer, treatment and frozen acceptance remain unchanged. C1 must finish and independent audit must resolve actual evidence before this becomes a new frozen test.

The current C06 requires every subprocess to have argv, raw bytes, exit and timestamps, while shared instructions exempt marker/native observer invocations. Their own records contain event metadata rather than subprocess outcomes. This mismatch is a measurement-contract defect; business acceptance and measured stage boundaries are separate.

Proposed correction: explicitly enumerate study command categories before a future run. The outer capture wrapper records each invoked study target including mark/native commands; the wrapper itself is the instrumentation boundary and is explicitly excluded. Marker/native target files remain immutable original event records. Native tool calls remain independently recorded from actual intent and return, not reconstructed from shell records. Capture calibration must include a successful marker, a failed marker, a native-intent file operation, and an unsuccessful target command with raw-byte fidelity. No recursive wrapping. The existing observer already supports a target that is another invocation of the observer, so a new canonical runtime helper is not justified for this defect. Example future command pattern:

```
python3 CAPTURE cli --record LOGS/unique-marker-command.json --actor worker -- python3 CAPTURE mark --events ARTIFACTS/observations --actor worker --stage worker_reply --event begin
```

The outer invocation is the declared instrumentation boundary. Its target marker invocation has an argv, raw stdout/stderr, exit and start/end stamps in the CLI record; the marker has its own original event record. Native observer targets use the same pattern, while actual collaboration call receipts are captured separately. This pattern is a proposal and is not inserted into the frozen C1 worker prompts.

Use exact `worker`/`coordinator` role values and preserve native worker identity in a separate binding. Index discovery is schema-based across `.json` and complete single-object `.jsonl` files; misleading extension does not erase evidence. Never rewrite raw actors to satisfy a protocol requirement.

Resumption: retain old boot IDs and unfinished boundaries. Cross-boot spans are null with a stated reason. An existing uncertain spawn is never repeated. A confirmed original-caller history can establish that the first call has not occurred, without inferring that from missing files alone. Resumed/assisted samples remain visible and cannot establish an unassisted speed comparison.

Scope: read permissions and write paths are explicit. All logs and stage records created by a worker stay inside its assigned artifacts directory. Future dispatch must contain one exact ready-to-run bootstrap command with a unique in-scope capture destination, so the first protocol/request read is captured before the worker learns the detailed convention; /dev/null is not a substitute log destination. This is a dispatch-contract proposal, not a change to any C1 request. Any command targeting an outside path is reviewed as an attempted scope violation even when its final effect is unknown. Protocol validity does not prove scope compliance.

Evaluation: first verify the recorder contract with small local commands, then run a fresh Luna exercise against the frozen revised protocol if warranted. Do not add work/driver initialization assistance merely because setup data is missing; require observable valid setup bottleneck evidence. Ordinary one-time tasks still use a direct flow.

## Worker host-tool boundary

C1 project B2 disclosed a worker-origin status probe that exposed sibling completion summaries. This is prior-result exposure and is retained as a nonconforming original sample; semantic correctness cannot restore independent treatment efficacy. Obtain only actual available raw receipts; a disclosure is not a fabricated tool capture.

Future worker dispatch must explicitly forbid status/creation/delegation/interrupt/followup tools and reading sibling/control/review directories, naming the permitted filesystem read/write scope and the permitted parent notification channel. Coordinator owns status operations. This is an instruction contract unless the host exposes and exercises a per-worker tool allowlist. When hard enforcement is unavailable, label containment unverified, retain actual violations, and never claim a global security or budget guarantee. A better prompt alone is not an enforcement layer.

## Coordinator transition checklist

The independent audit also checks the original required running-status observe step. A future protocol must operationalize the legal sequence against the original control phase and the actual receipt type: creation return → accepted; running snapshot → observe before further polling; completed snapshot → receive; independently graded decision → commit/reconcile. A status snapshot is not a creation return, and a successful receive does not prove that every required prior observation was recorded. Retain attempted illegal calls and correction counts. Use the existing public controller/driver capabilities first; adding a new initialization helper requires valid preparation-bottleneck evidence.

Reserve the final allowed status query deliberately. Notification waits may be repeated within their frozen per-wait bound without being counted as status queries; a wait or worker message is not a terminal snapshot. Once a query budget is exhausted, preserve the unknown state rather than querying through another actor. If a worker can still write, take a manifest-backed cutoff copy and disclose its non-atomic nature, timing and per-file stability. Later files do not retroactively complete the original measured sample.

## Correction budget accounting

Count all local correction attempts within the declared worker/coordinator scope, including evidence readers and index construction; business-output-only counting is not an implicit exemption. Declare administrative exclusions before a future freeze if they are genuinely outside the sample. Preserve first versions and failed audits. A nonzero CLI exit, an incorrect derived index and a corrective attempt are different events; report them separately. Successful final artifacts do not erase a exceeded local correction budget.
