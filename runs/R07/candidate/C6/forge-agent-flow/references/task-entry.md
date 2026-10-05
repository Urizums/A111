# Task entry and existing-flow execution

Contents: Route · Script location · Existing package · Review verdict · Handoff.

## Route by the requested result

| Request | Action | Completion evidence |
| --- | --- | --- |
| One-time result from supplied material | Perform a scoped task directly; use one context unless independence or tool separation is needed. | Actual output and a relevant source/runtime check. |
| Create a reusable flow | Use the strict factory, freeze acceptance, build and run the target flow. | Completed factory plus separately assessed target runs. |
| Run a supplied package on new material | Execute that same package with the new inputs. | Bound terminal checkpoint, actual output and checks on the new material. |
| Continue an existing run | Inspect saved checkpoint, receipts and actual host status; resume applicable work. | Current results with prior attempts retained. |

Do not repeat construction on every execution. A short transformation can have
one target node even though its factory has multiple construction stages.
Choose more nodes for concrete dependencies, independent evidence or necessary
tool/context separation; role names alone do not justify a split.

## Locate the scripts

Resolve the directory containing the supplied or installed SKILL.md and set
`FORGE_SKILL_DIR` to that absolute directory. Scripts are bundled there; a
`forge`, `packagectl` or `flowctl` command on PATH is not required.

```bash
python3 "$FORGE_SKILL_DIR/scripts/packagectl.py" --help
python3 "$FORGE_SKILL_DIR/scripts/forge_template.py" --help
```

Use absolute script paths in generated run instructions and delegation requests
so execution does not depend on the working directory. Treat current CLI help
and the package's schema as authoritative. For strict response/results drafts,
read [protocol-templates.md](protocol-templates.md); templates contain no work
or passing evidence. Use a new compile/output path when the CLI refuses to
overwrite an existing path; preserve prior results.

## Execute an existing package

Read the package as data, inspect declared inputs, node contracts and execution
requirements, then validate it. Keep the supplied package unchanged unless a
revision is explicitly needed and authorized. Unmet authority or host bindings
remain blockers; do not bypass them through the embedded flow.

```bash
python3 "$FORGE_SKILL_DIR/scripts/packagectl.py" validate package.json
python3 "$FORGE_SKILL_DIR/scripts/packagectl.py" start package.json --inputs inputs.json --state new-run.json
python3 "$FORGE_SKILL_DIR/scripts/packagectl.py" next package.json --state new-run.json
python3 "$FORGE_SKILL_DIR/scripts/forge_template.py" response --dispatch dispatch.json --outcome ok --out new-response-draft.json
python3 "$FORGE_SKILL_DIR/scripts/packagectl.py" advance package.json --state new-run.json --response response.json
```

Save the actual current dispatch to dispatch.json before using its draft.
Perform the node task, fill artifacts and top-level evidence from actual work,
submit the response with its current invocation ID, and continue to a terminal
state. Draft placeholders or an accepted worker creation are not completion.
Preserve caller input bytes, raw responses, tool receipts and checkpoints; one
coordinator writes a given checkpoint.

For `forge-package/2`, read the **Bound package and execution** and **Case
results** sections of [evaluation-plan.md](evaluation-plan.md). Its results
shape is `package_hash`, `plan_hash`, `cases`. The `package_hash`, `checks`
shape in package-contract.md is only for version 1. Generate a v2 frozen-case
draft with `forge_template.py results`; fill only actual executed cases.

New caller inputs can run through the same package without being cases in its
frozen plan. Check their actual output against the current request and sources
in a separate new-input verification record. Do not insert them under an old
case ID, change the frozen expected input, or claim original-case coverage.
If original cases were not run, say so and retain pending/not-assessed coverage.
New-input success and original-plan assessment are different observations.

## Check a review verdict against its requirements

Apply this check to every review and regrade, including a one-time review of an
existing report. Before final delivery, recompute every failed, partial or
unverified requirement row against the exact current requirement and raw
evidence. Treat prior statuses as proposals rather than acceptance rules.
Record the violated clause or justified derived requirement, observable
behavior, supporting evidence and counterevidence. Missing evidence supports a
negative required status only when it is needed for that required assertion,
not for a newly suggested improvement. Keep optional quality ratings separate
from required acceptance. A reviewer
may discuss a useful improvement outside its assigned requirement; its status is
input for reconciliation, not automatically the final verdict.

Ask whether the claimed gap prevents the required behavior or contradicts a
required documentation claim. If the source requires data to be stored, a new
convenience interface or example for viewing it is advisory unless that access
is itself required or concretely necessary for the requested outcome. Keep such
advice in a separate recommendations list; do not downgrade a satisfied required
row solely for it. A derived must-have needs its dependency/basis, and changing
acceptance needs an explicit revision rather than an invented frozen failure.

Separate implementation, documentation and evidence coverage. A deliberately
restricted engineering reviewer lacking documentation cannot decide the combined
documentation status; the coordinator resolves it with the permitted document
review and current sources. Label static reachable defects separately from
observed runtime defects; an unexecuted edge is not a claim that it ran. Preserve
uncertain wording and propose the exact distinguishing check. Retain old reviews
and add a source-based correction instead of silently editing their receipts.

## Handoff without answers

Give a fresh executor the raw goal/materials, exact package and skill location,
allowed operations, output directory, and resource limits with their scope.
Let it perform the node tasks; do not supply holdout answers, prior diagnoses
or another branch's results. A package's original example cases are visible
training material, not unseen holdouts. Task paths describe assignments rather
than enforced operating-system isolation.

Keep status queries inside the executor's own task subtree. If global capacity
is needed, the parent supplies a capacity-only summary without other tasks'
results. Record locator assistance or incidental exposure and qualify any
independence claim. New context alone does not establish blind validation.
