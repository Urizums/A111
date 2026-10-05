# Flow IR 1.0 and 1.1

Use `assets/minimal-flow.json` as the smallest complete example and
`assets/meta-flow.json` for a bounded repair cycle. Use Python 3.10+ with no
third-party dependencies for the supplied tools.

## Exact structure

| Field | Meaning |
| --- | --- |
| `schema_version` | Literal `1.0` or `1.1`. |
| `id`, `goal` | Stable snake_case identifier and concrete outcome. |
| `assumptions` | String list; distinguish defaults from explicit requirements. |
| `inputs` | Immutable required initial fields. Flow 1.0 uses `{type, description}`; Flow 1.1 may add a restricted `schema`. |
| `artifacts` | Writable fields. Flow 1.0 uses `{type, description}`; Flow 1.1 may add a restricted `schema`. |
| `outputs` | Artifact names required on every `$done` route. |
| `capabilities` | Map of aliases to actual host bindings and availability. |
| `budgets` | `{max_steps: positive_integer}`; host enforces further budgets. |
| `entry` | Existing node identifier. |
| `nodes` | Nonempty array of the exact node structure below. |

All identifiers use `[a-z][a-z0-9_]{0,63}`. Supported top-level artifact types are
`string`, `object`, `array`, `integer`, `number`, `boolean`. Null is not a
top-level field type. Booleans do not count as integers. NaN and infinities are
rejected.

Flow IR 1.0 keeps its original exact descriptor shape and shallow runtime
validation: each descriptor contains only `type` and `description`. A `schema`
key in a 1.0 descriptor is invalid. Existing 1.0 flows therefore retain their
previous artifact acceptance behavior.

Flow IR 1.1 descriptors may add an optional `schema` object. Its root `type`
must exactly match the descriptor's top-level `type`. The checker supports only
`type`, `required`, `properties`, `items`, `enum`, `minItems`, and
`additionalProperties`; unknown keywords and external references are rejected.
Schema depth is limited to 16 schema objects along a path. Supported schema
types are `string`, `object`, `array`, `integer`, `number`, `boolean`, and
`null`. A nullable field uses exactly one non-null type plus null, for example
`{"type": ["string", "null"]}`. `required` and `properties` apply only to
objects; `items` and `minItems` apply only to arrays; `additionalProperties`
applies only to objects and must be boolean. `minItems` is a non-negative
integer (a boolean is not an integer). `enum` must be a non-empty list of
unique finite JSON values compatible with the declared type. Unspecified
`additionalProperties` follows JSON Schema's permissive default; use `false` to
reject undeclared object fields. Empty arrays are valid unless `minItems`
requires otherwise.

This 1.1 subset is not general JSON Schema: it has no `$ref`, pattern or regular
expression support, arbitrary code, or other keywords. The engine validates
input values at `start`, node outputs at `advance`, and artifacts before dispatch
at `pending`. A failed check reports the artifact field path and does not update
the checkpoint. Schema validation is structural; it does not establish semantic
correctness or source truth. `forge-package/2` may continue embedding either
supported Flow IR version; its existing validator delegates to `flow.validate`.

Every node contains exactly:

```json
{
  "id": "extract",
  "kind": "agent",
  "reads": ["notes"],
  "writes": ["actions"],
  "tools": [],
  "prompt": "Extract explicit actions and source quotes; preserve missing fields as null.",
  "acceptance": ["Do not invent an owner or date."],
  "max_visits": 1,
  "routes": {"ok": "$done", "error": "$failed", "blocked": "$blocked"},
  "emits": {"ok": ["actions"], "error": [], "blocked": []}
}
```

`kind` is `agent` or `check`; both are dispatched to the host. For a deterministic
check, the host executes the specified checker and records its actual result.
No Python function or model is automatically selected by `kind`.

All outcome names in `routes` must appear in `emits`, and vice versa. An outcome
must provide exactly its listed fields; no additional fields. `error` and
`blocked` routes are mandatory. Targets are nodes or `$done`, `$failed`,
`$blocked`. Route predicates live in prompt/acceptance rules and are evaluated
by the host; the engine checks that the reported outcome is declared.

Artifacts accumulate, and a later allowed writer replaces the current value.
Only declared `reads` are included in a dispatch. There is no automatic stale
artifact invalidation: explicitly rebuild downstream products after repair.
Use distinct artifact names when preserving versions matters. Inputs cannot
be overwritten. The static checker uses every incoming outcome path to check
that required reads and final outputs are guaranteed to exist, including cycles.

## Capability descriptor

```json
{
  "workspace": {
    "binding": "exec_command",
    "effect": "local_write",
    "available": true,
    "authorization": "granted",
    "evidence": "Tool observed in this host; user requested local artifact creation."
  }
}
```

`effect` is `read`, `local_write`, or `external_write`. `authorization` is
`granted`, `required`, or `not_applicable`; external writes cannot use the last.
Unavailable tools and required authorization block dispatch. Declarations are
a capability snapshot, not access enforcement; the host must verify current
authority at the action boundary. Do not change a declaration to bypass a real
permission failure. When actual access changes, create a revised flow/run and
explicitly migrate validated artifacts instead of replaying side effects.

## Deliberate limits

Flow IR 1.0 and 1.1 have one active node. A branch selects one successor; it does not fan out.
The dispatcher does not implement parallel joins, provider networking, streaming,
dynamic graph generation, persistent memory retrieval, full JSON Schema, token
accounting or task-specific semantic graders. Extend a real adapter only when
needed and verify its current documentation. A structural pass is not a claim
of task quality or that the max_steps budget is sufficient for a successful run.
