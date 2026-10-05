# Acceptance plans: branches, frozen criteria, and evidence

Choose the acceptance protocol by delivery type. Program mode uses projectctl
and a requirement-to-branch acceptance matrix to deliver a working system
directly. Flow mode uses the strict factory's frozen forge-eval plan and bound
package. Keep forge-package/1 compatibility for old flow packages; use
forge-package/2 for new factory output. The serial Flow IR engine is unchanged.

Contents: Program-mode acceptance · Coverage sidecar · Flow-mode plan shape ·
Factory stages · Bound package · Case results · Boundaries.

## Program-mode project acceptance

For software_system, agent_infrastructure, and coordinated scoped_change work,
keep the project TODO plan and full acceptance plan distinct. The
forge-project-plan/1 plan used by projectctl binds requirements and task IDs to
acceptance assertions. Maintain a complete acceptance plan alongside it with
case inputs, expected outcomes, and evidence expectations; it may use
forge-eval/1 without running the strict factory. Map each requirement to
concrete branches and distinct inputs, with expected status, values, and
evidence. See assets/example-project-plan.json for the TODO-plan shape and use
it only as a structural example. Include the primary successful behavior and
relevant rejection, missing-input, and conflict branches as separate cases.
Exercise a failure, recovery, and reuse of prior state when the system is
stateful. For permissioned actions, test both an authorized success and an
unauthorized failure. For automatic decisions, test absent or disabled rules
and require a recorded explanation. Include UI feedback, keyboard behavior, and
error states only if the deliverable has a UI.

Set the required evidence level to match the assertion. Runtime behavior needs
an actual runtime check; static validation or review does not substitute for it.
Freeze acceptance before implementation evidence, preserve its IDs and history,
and add new IDs plus regression cases when the user adds a requirement. Mark
affected completed tasks invalid and rerun dependent acceptance against the new
candidate. A structural count or reference check proves only that declared
entries are present.

Before repairing a reviewed candidate, retain its exact tested source through
an immutable revision or an explicit snapshot, together with commands, raw
results and hashes. Preserve the original findings and evaluator. Add a separate
post-fix check that expects corrected behavior; a fixture that successfully
reproduces a defect is not a passing product case. If only historical hashes or
reports remain, state that the original bytes cannot be rerun.

For each new software_system or agent_infrastructure project, initialize
projectctl with the full forge-eval/1 plan using --evaluation-plan. The state
embeds the complete plan and its hash; runtime acceptance IDs in the TODO plan
must match required criteria in that bound plan. Run the frozen required cases
and reference their actual outputs in task evidence: projectctl binds the plan
and checks declared criterion level and evidence hashes on task finish. Use
[executable-acceptance.md](executable-acceptance.md) for actual local-process
cases and projectctl assess for a separately regraded product verdict.
A completed structural project status is not itself a product-case verdict.
A legacy project without this binding remains supported and reports
product_acceptance_status=not_configured; do not claim its product cases were
verified against a frozen plan. A bound project reports
product_acceptance_status=not_assessed until a case-run report is attached.
Attached reports use exact output/status comparison, require human review where
declared, and become stale or unverified when relevant tasks, plans or files
change. Other runtime formats still need their appropriate host grader.

If acceptance changes, update the authoritative lock through projectctl revise
with the new full plan and explicitly invalidate affected completed runtime
tasks. Preserve the prior plan, hash, and attempts as history. Do not edit an
external exported file in place and treat an existing state as if it used the
new cases. Historical evidence warnings report missing or changed old files;
they do not block the new revision.

## Coverage sidecar for forge-eval/1 plans

The coverage sidecar checks declared evaluation obligations for a complete
forge-eval/1 plan, whether used by flow mode or maintained independently for
program mode. It does not replace the plan or determine whether the designer
noticed every meaningful branch. Keep the plan's full inputs and expectations
as the source of truth; use distinct case IDs for distinct input variants. A
project TODO plan is not itself a substitute for these runtime cases.

The forge-coverage/1 object has top-level schema, plan_hash, and entries. Bind
plan_hash to the canonical complete plan using flowctl.digest(plan). Each entry
maps one requirement and criterion to a scope, applicability decisions, and
obligations. Read assets/example-coverage.json for a complete sidecar example.
Every entry declares exactly the negative, recovery, reuse, authorization,
ui_feedback, and explanation dimensions, each with applies and a reason. Mark
irrelevant dimensions inapplicable with a concrete reason; do not require a UI
or policy branch that the product does not have. Applicable checks use
obligations with an ID, kind, case IDs, input variant, and expected JSON Pointer
fields. Explanation obligations also identify reason fields; UI obligations
identify UI fields. Every required criterion has at least one success obligation.
Applicable authorization checks include distinct allowed and denied paths;
applicable recovery includes both negative and recovery paths.

Avoid multiplying fixtures for cross-cutting observations. One real success
journey can cover success, an authorized action, visible feedback, and an
explanation if that journey produces each expected field. Create distinct
case IDs and input fixtures for genuinely different branches: success versus
negative, recovery, reuse, or authorization denied; negative versus recovery;
and authorization allowed versus denied. Multiple obligations of the same
branch kind also need separate fixtures. A recovery path includes a negative
case. The checker enforces these declared distinctions but cannot decide which
branches the designer overlooked.

Validate with:

```bash
python3 scripts/coveragecheck.py validate PLAN COVERAGE
```

The checker validates the declared matrix and its references; it cannot detect
all omitted requirements, implausible expected values, or shallow reasoning.
Use an independent fresh-context review for consequential acceptance design.
Keep the review blind to expected answers and prior diagnoses.

## Flow-mode plan shape

Use `assets/example-plan.json` as a complete example. A `forge-eval/1` plan has
exactly `schema`, `id`, `criteria`, `cases`, `baseline`, `limitations`.

- `id`, criterion IDs and case IDs use the safe snake_case Flow IR identifier
  format and are unique within their category.
- `criteria` is a nonempty array of `{id, kind, required, assertion}`. Kind is
  `machine` or `human`, required is boolean and assertion is nonempty text.
  Include at least one required criterion. Do not change grader kind later.
- `cases` is a nonempty array with the exact fields in the example below.
  Inputs and expectations are full objects, even when empty. Reference existing
  criteria without duplicates. Every criterion needs a case; every required
  criterion needs a required case; a required case includes a required criterion.
- `baseline` is nonempty text; `limitations` is a string list.

```json
{
  "id": "empty_notes",
  "inputs": {"notes": "No commitments were made."},
  "expected": {"actions": []},
  "expected_status": "completed",
  "criteria": ["quotes", "commitments"],
  "required": true
}
```

Expected status is `completed`, `failed` or `blocked`. Expectations preserve
the actual intended behavior and its evidence; the generic assessor does not
interpret their domain semantics. Define and run suitable graders in the host.
Keep private holdouts outside the candidate's supplied plan and disclose them
separately; do not add them retroactively to a frozen run's denominator.

## Factory stages

Use `factoryctl.py`, with a single writer to each checkpoint:

```bash
python3 <skill>/scripts/factoryctl.py start --inputs inputs.json --state factory.json
python3 <skill>/scripts/factoryctl.py next --state factory.json
python3 <skill>/scripts/factoryctl.py advance --state factory.json --response response.json
```

Initial inputs are `request` (string) and `environment` (object), as in the meta
flow. Except for the plan freeze below, submit actual stage responses using the
ordinary Flow IR envelope: invocation_id, outcome, artifacts, evidence.

At **eval_design**, write the complete plan file and run:

```bash
python3 <skill>/scripts/factoryctl.py freeze-plan plan.json --state factory.json
python3 <skill>/scripts/factoryctl.py export-plan --state factory.json --out frozen-plan.json
```

Freeze validates the complete plan, computes its canonical SHA256, and advances
the stage with `{test_plan: {plan, plan_hash}}`. This full object is the stage
artifact and is covered by the trace output hash before architecture or build.
The checkpoint copy is authoritative. An export is an exact-content copy for
inspection, not a second independently edited plan. A normal successful
eval_design `advance` is refused so an agent cannot substitute a summary.

Later dispatches that read test_plan receive the full lock object. On every
factory operation, the wrapper validates the plan and compares it with the
recorded eval_design handoff. Editing the plan and merely recalculating its
own digest does not match the original stage output hash. These are accidental-
drift checks, not protection against someone rewriting all local evidence.

At **build**, create a draft based on the ordinary package example, then run:

```bash
python3 <skill>/scripts/factoryctl.py bind-package draft-package.json --state factory.json --out package.json
python3 <skill>/scripts/packagectl.py validate package.json
python3 <skill>/scripts/packagectl.py compile package.json --out new-compiled-folder
```

Binding sets the v2 schema and copies acceptance from the authoritative frozen
plan. Draft acceptance is replaced by this source; it never changes the frozen
plan. Use a new output path. The successful build response's candidate artifact
must contain the full `package` object and its exact `package_hash`. Other
candidate metadata such as compiled paths may accompany them.

At **verify**, run the frozen cases with packagectl start/next/advance, preserve
raw host responses, inspect outputs and construct the case results below.
Submit `{evaluation: {results: RESULTS_OBJECT}}` as the stage artifact. The
wrapper calculates and inserts `assessment`; a supplied assessment must match
exactly. Outcome `ok` requires computed `pass`. Use `fixable` for a bounded
repair or `limited` for candid delivery with unfinished evidence or unresolved
failures when further repair is not justified. Repair keeps
the plan fixed and binds a new package; old package results cannot be reused as
if they belonged to the new revision.

At **deliver**, the wrapper adds the exact plan hash, package hash and computed
assessment to the delivery artifact. It refuses contradictory supplied values.
Lifecycle `completed` means delivery finished; it does not mean acceptance
passed. A delivery may retain `pending`, `limited`, or `fail`; report the
assessment verdict explicitly and never relabel it as success.

## Bound package and execution

Version 2 keeps the same package top-level fields as version 1. Its schema is
`forge-package/2`; acceptance is exactly:

```json
{
  "plan": {"schema": "forge-eval/1", "id": "example", "criteria": [], "cases": [], "baseline": "...", "limitations": []},
  "plan_hash": "canonical SHA256 of the complete plan"
}
```

This shortened shape illustration is not a valid plan; use the complete asset.
Do not add another criteria summary beside the plan. The plan's case inputs
must exactly match the flow's input names and top-level types. Compiler output
preserves the complete package. Version 2 runtime checkpoints and dispatches
retain `plan_hash`. Checkpoints also carry `input_hash`, the canonical digest
of the complete startup inputs; runtime and assessment verify those immutable
fields remain present and unchanged. A missing, stale or mismatched binding
is rejected. Target
dispatches include the task and actual inputs, not expected answers.

## Case results

This section is the version 2 results protocol. Start from the current
`forge_template.py results` draft rather than the version 1 checks envelope.

Version 2 `results.json` has exactly `package_hash`, `plan_hash`, and `cases`:

```json
{
  "package_hash": "canonical package hash",
  "plan_hash": "canonical plan hash",
  "cases": [
    {
      "case_id": "empty_notes",
      "run": {"package_hash": "...", "plan_hash": "...", "input_hash": "...", "flow_state": {}},
      "checks": [
        {"id": "quotes", "kind": "machine", "status": "pass", "evidence": ["actual checker output path"]},
        {"id": "commitments", "kind": "human", "status": "pass", "evidence": ["actual review record path"]}
      ]
    }
  ]
}
```

Copy the complete real packagectl checkpoint into `run`; the abbreviated shape
above is not an executable fixture. Use null only for an unrun case, and never
give it a passing check. Case and criterion IDs must belong to the frozen plan
and cannot repeat; grader kinds cannot be changed. Executed checks need actual
evidence references. The assessor checks package/plan identity, startup input
binding, frozen case inputs and expected terminal status, and aggregates the frozen case/criterion
coverage. Missing required work is pending, required failures fail, optional
gaps are limited. Required failures take precedence over pending or optional
items; no average score erases them.

Keep executions with caller inputs outside the frozen plan in a separate
verification record: package/input/checkpoint identity, actual output, grading
method, evidence and limitations. Such runs can succeed while original-plan
coverage remains pending or not assessed. Never relabel the new input as a
frozen case or extend a frozen denominator after seeing results.

Choose `machine` only for an actual executable check and preserve its code,
command and result. A model's semantic review is not deterministic merely
because a record calls it machine. Keep the frozen kind unchanged; if its
promised checker has not run, mark that check not_run and document the gap.
Label model/human judgment and self-review dependence in the evidence sidecar.

Before merging a report, inspect current source and raw receipts for every
must-have claim and distinguish requirement failures from advisory findings.
Do not promote a new preference to a required failure without its basis and an
explicit acceptance revision. Preserve outdated/conflicting summaries and add
a correction tied to current evidence rather than rewriting old receipts.

## Boundaries

Local hashes and traces prove internal consistency only. They do not attest
creation time outside the recorded execution, provider identity, genuine model
calls, grader correctness or absence of unseen effects. Keep actual outputs and
tool receipts, inspect semantic grades, record context/model dependence, and
avoid production-readiness claims from a few samples. All raw checkpoint files
remain within a trusted single-writer boundary. Current host authority and
real permission enforcement still apply at each external action.
