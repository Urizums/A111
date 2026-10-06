# Smoke, acceptance and checker responsibility

Use when designing checks, assigning acceptors or judging a result. A convincing
report is not an oracle. Derive assertions from the original outcome, domain
invariants and supplied constraints, with derived assertions identified as such.

## A usable gate contract

For each gate record: purpose; original requirement/source; versioned input;
observable assertion; evidence channel; checker and independence; reject condition;
failure route/budget; supported conclusion and excluded claims. A compact table
is sufficient. Do not require a document or custom program per field.

| Gate | Needed evidence | Supported claim |
| --- | --- | --- |
| Preflight | Actual relevant capability/material checks | Prepared to attempt the path, not delivered |
| Smoke | Small real raw-input-to-output path, receiving assertion and relevant failure path | This bounded path works under these conditions |
| Acceptance | All mandatory requirements checked against raw sources and actual artifacts | The observed requested outcome, within stated limits |
| Independent acceptance | Fresh acceptor with original requirements/raw sources and actual outputs | Independence of the stated judgment, not general correctness |
| Performance / generality | Defined comparison, controlled resources, repeats and appropriate uncertainty | Only the measured comparison/population |

## Keep smoke strong while small

Choose a path that crosses the important interfaces; a helper-only command or
static file check cannot substitute for a user-facing end-to-end result. Include
one meaningful boundary or rejection where it could otherwise allow false success.
Tie every smoke assertion to an acceptance requirement and keep uncovered ones
in the full gate. Select fewer cases if needed; do not weaken a selected assertion,
remove a rejection condition or silently call acceptance a smoke pass.

Examples of observations, adapted to the task:

- Modeling: a raw data slice passes unit/missingness checks, a baseline produces
  numerical results, the consumer checks constraints/residuals or held-out error,
  and a paper/table value can be traced to the computed output. A malformed input
  or infeasible instance is surfaced rather than silently repaired or scored.
- Frontend: an actual browser performs the main journey and checks state/output;
  keyboard access, a responsive viewport and a meaningful error/empty state are
  inspected. A screenshot establishes appearance at that viewport, not working
  interaction or all-device usability.

Do not mandate a forecasting test for optimization or a screenshot for a pure
numerical task. Domain adaptation changes which observable assertion is relevant,
not whether that assertion needs evidence.

## Give the acceptor a real task

Freeze requirements and raw input before implementation/evaluation. Producers own
artifacts and self-checks; the coordinator owns integration; an acceptor owns the
stated verification. Where independence is required, use a fresh context, withhold
expected answers, author diagnoses and previous verdicts, and give actual material
access. A producer's report may be an artifact to inspect; it is not the basis of
truth. If the host cannot supply an independent actor, name the remaining gap.

The acceptor must inspect or recompute relevant facts, examine critical interfaces
and failure paths, and return one verdict per mandatory requirement with source,
artifact/observation and limitation. Explain what evidence would cause rejection.
Require the appropriate target runtime: numerical computation for numerical
claims, browser interaction for UI claims, raw source review for synthesis claims.

When checker reliability is consequential, evaluate it on authorized controlled
defects that violate frozen requirements, paired with valid artifacts. Keep the
variant identities/classifications out of the reviewer's packet; do not contaminate
a live evaluation or count a merely described defect as an actual detected one.
Record both false acceptance and false rejection. This is an optional specific
checker test, not an automatic additional gate for every trivial task.

## Judge the judgment

Map requirement → raw source → artifact → performed check → verdict → limit.
Each required failure needs the exact violated source clause or justified derived
requirement and actual contradictory/missing evidence. Separate optional style,
extra models and novel enhancements from mandatory acceptance. A clever solution
may be wrong; a simple solution may meet the request. The author cannot relax an
assertion after failure or choose only the metrics that look favorable.

Keep artifact states precise: drafted, produced, self-checked, independently
accepted, delivered. Command state=finished and exit0 describe a command only.
No check means unverified, even when a document says finished or CI is green.

For material conclusions distinguish direct observations, causal hypotheses and
future expectations. Observations need stable sources/checks; hypotheses need
assumptions and alternatives; expected gains need an actual future measurement.
Unavailable model/timing/token/cost telemetry stays unknown, not inferred from
labels or file size. Prompt detail alone is not evidence of award-level quality.

Retain every failed attempt and failure-driven correction. Reuse existing receipts;
collect only relevant non-sensitive data. If a legacy record lacks a field, retain
the original and add a source-bound transcription only where real evidence supports
it; do not replay a side effect to fill metadata or fabricate terminal state.

Use original cumulative limits across source, orchestration and execution fallbacks.
Count failed corrective constructions even without mutations. On exhaustion stop
the case, preserve actual totals even above the limit, uncertainties and recovery
condition. Another actor, renamed sample/candidate or changed criterion cannot
restore acceptance. New requirements receive versioned scope provenance; historical
failures and budgets remain visible and must not be regraded by the new test.
