# Explicit smoke evidence content checks

`smokecheck.py assess PLAN RESULTS` keeps the smokecheck-results/1 structure and
binding behavior. It does not open evidence references; its report marks content
inspection as `not_checked`. To require local content inspection, pass
`--evidence-manifest FILE`. That mode can report an overall `pass` only when the
existing structure assessment passes and every referenced evidence file passes
its declared checks.

The `smoke-evidence-manifest/1` manifest binds `plan_hash`, `candidate_id`, and
`baseline_id`, then maps each evidence string in results to exactly one entry.
Run entries bind `candidate_id`, `journey_id`, and `round`; regression entries
bind `candidate_id` and `behavior_id`. Every result reference must appear once,
with no missing or unused manifest entries. Reusing a result reference, evidence
path, or content hash across entries is rejected, including across rounds.

Manifest paths are POSIX paths relative to the manifest's directory. Absolute
paths, `.` or `..` components, backslashes, symlinks, non-regular files, empty
files, files larger than 4 MiB, hash mismatches, and unreadable evidence are
rejected. Reads use no-follow file opens and never execute content or access the
network.

The small initial media-type set is `text/plain` and `application/json`.
Unsupported types, including PNG, fail closed. Text must be nonempty UTF-8 and
include one exact standalone binding line:

```text
smoke-run:<candidate_id>:<journey_id>:round-<round>
smoke-regression:<candidate_id>:<behavior_id>
```

Each text entry also needs at least one `contains` literal assertion. JSON must
be a nonempty object without duplicate keys or non-finite numbers. Its root must
include the exact candidate/run fields or candidate/behavior fields for its
binding. Each JSON entry also needs at least one `json_equals` assertion. The
`field` selector follows dotted object keys, such as `screen.state`; arrays and
executable expressions are not supported. JSON comparisons preserve value
types, so `true` does not equal `1`.

Example checks:

```json
{"kind":"contains_binding"}
{"kind":"contains","value":"Expected item is visible"}
{"kind":"json_equals","field":"observation.state","value":"saved"}
```

The command is:

```sh
python3 scripts/smokecheck.py assess PLAN RESULTS --evidence-manifest MANIFEST
```

The Python API is `smoke_evidence.assess(plan, results, manifest, root=None)`.
When `manifest` is a file path, its parent directory is the evidence root. For
an in-memory manifest object, `root` selects the evidence root and defaults to
the current directory. The report includes the original structure assessment,
per-entry results, `content_status`, and `content_checked`. The latter is true
only when every evidence file was safely read, hash-checked, parsed, bound, and
tested against its assertions. A failed literal assertion yields `fail`; absent,
corrupt, unsupported, or integrity-invalid evidence yields `invalid`.

These checks establish local file consistency and the declared content matches.
They do not authenticate a producer, prove that a run happened, verify that an
observation is truthful, or judge user experience. The manifest author controls
the assertions. A passing result is not execution authentication or a UX grade.

`assets/example-smoke-evidence.json` illustrates the complete reference mapping
for `assets/example-smoke-plan.json`. Replace each evidence reference, path, and
placeholder hash with the values from the actual results and files before use.
