# Requirements-based evaluation

Read for acceptance design, review and observed failure analysis.

Before a meaningful evaluation, retain the original request and input version,
candidate identity, material constraints, expected observable behaviors and
repair limit. Define success from the user outcome, not from the implementation
or the author's preferred wording. Select cases that exercise actual decisions,
handoffs and consequences; a script-count or entry-length target is insufficient.

Build a compact requirement-to-evidence record: requirement; actual artifact or
observation; verdict; limitation. Recompute or inspect relevant source-derived
facts rather than echoing the worker's verdict. Do not downgrade satisfied
required behavior because an optional enhancement is absent.

Keep claims separate:

| Evidence | What it can establish |
| --- | --- |
| Frontmatter, links and package inspection | Discoverability and structural consistency |
| Worked design or simulated trace | Method legibility or declared branching, not execution |
| Actual outputs checked against raw input | Correctness for that observed task |
| Fresh context independently executing or reviewing | The stated independent acceptance, within its input and environment bounds |
| Comparable measured runs with defined conditions | A scoped performance comparison, not general improvement |

For workflow evaluation, observe whether it selects a proportional route,
produces the requested deliverable, carries material constraints through handoffs,
handles missing/conflicting evidence, and terminates or continues appropriately.
Inspect rejection or recovery only where that behavior matters to the request.
Preserve the difference between a tool failure and an incorrect business result.

Record every failed attempt and failure-driven correction before continuing.
Use the original limit across source edits and execution fallbacks; successful
work does not erase the failed path. On exhaustion retain the current artifacts,
reason and recovery condition, and stop that attempt. Different work can proceed
when genuinely independent; it cannot serve as replacement acceptance for the
failed case.

After a failure, identify the earliest unsupported decision or broken handoff.
Fix the cause with the smallest change, retain the prior version and rerun the
affected frozen checks within budget. Broaden checks when the change affects
other behavior, not to inflate counts. New requirements receive a versioned scope
decision with their provenance; keep the old verdict and budget visible.

State observed correctness, independence, performance and generality separately.
If data is unavailable, leave the claim unverified. Do not manufacture timing or
token numbers from role labels, output sizes or assumed provider behavior.
