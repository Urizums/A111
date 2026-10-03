# Forge protocol draft templates

`scripts/forge_template.py` writes editable JSON drafts for the host-driven
dispatcher and frozen-plan evaluator. It reads JSON as data, rejects duplicate
keys and non-finite numbers, and creates the destination atomically without
replacing an existing file.
For outer host reply/decision drafts, use [host-drafts.md](host-drafts.md) and
`scripts/hostdraft.py`; the response/results commands below are different layers.

For a current ready dispatch, create a response envelope with the exact outcome
and artifact names declared by that dispatch:

```bash
python3 scripts/forge_template.py response \
  --dispatch dispatch.json --outcome ok --out response-draft.json
```

The draft copies the dispatch's `invocation_id`, creates empty top-level values
from the selected outcome's `artifact_types`, and sets `evidence` to `[]`.
Replace every placeholder with the actual host result and add real evidence
references before submitting it to `flowctl.py advance` or `packagectl.py
advance`. An empty-evidence draft is intentionally rejected by `advance`; the
template does not create semantic answers or evaluate nested artifact schemas.
Only exact ready dispatch shapes from `flowctl.pending`, `packagectl.pending`
(package v1 or v2), and `factoryctl.pending` are accepted. A configured factory
materials gate must explicitly allow its frozen operation. Blocked, failed,
completed, malformed, or gate-blocked dispatches are rejected. A dispatch file
alone cannot show whether its invocation is still current; `advance` checks the
copied invocation ID against the current checkpoint and rejects stale IDs.

For a validated `forge-package/2`, create a results draft bound to the exact
package and full frozen plan:

```bash
python3 scripts/forge_template.py results \
  --package package.json --out results-draft.json
python3 scripts/packagectl.py assess package.json --results results-draft.json
```

The draft has the canonical `package_hash` and frozen `plan_hash`, one row for
every plan case, and one `not_run` check for every criterion mapped to that
case. Each row has `run: null`; each unrun check has `evidence: []`. The
resulting assessment is `pending`. Fill these fields only from actual runs,
criterion reviews, and evidence. Version 1 packages are supported for response
templates, but are not accepted for this results format.
