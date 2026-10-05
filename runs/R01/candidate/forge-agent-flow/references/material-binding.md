# Material identity gate

Use `scripts/materialcheck.py MANIFEST` before software changes and again before
target writes. The manifest is a frozen statement of which files are targets and
which are references. Paths are relative to the manifest directory. The checker
hashes regular files (maximum 64 MiB), rejects symlink targets, and never executes
file contents.

The strict top-level shape is:

```json
{
  "schema": "forge-materials/1",
  "intent": "source_only",
  "source": {
    "path": "source-snapshot.zip",
    "sha256": "<64 lowercase hex characters>",
    "role": "target_source",
    "identity": "com.example.app",
    "stack": "flutter",
    "platform": "android",
    "fingerprint_scope": "complete_source_snapshot"
  },
  "binary": null,
  "references": [],
  "provenance": null
}
```

The selected source must be a fixed archive file (`.zip`, `.tar`, `.tar.gz`,
`.tgz`, `.tar.bz2`, `.tbz2`, `.tar.xz`, `.txz`, `.tar.zst`, `.tzst`, `.7z`, `.bundle`, or
`.gitbundle`) whose declared scope is the complete source snapshot. Hashing a
single source/configuration file such as `pubspec.yaml` does not fingerprint a
source tree. The archive path and its actual SHA-256 are checked; semantic
completeness of its contents remains a declaration by the manifest author.
`assets/example-materials.json` is a template; replace its path and placeholder
digest with the selected snapshot and its actual hash before use.

For a binary/source comparison, set `intent` to `binary_source`, keep the same
`source` object, and supply `binary` with role `target_binary` and the same
`path`, `sha256`, `identity`, `stack`, and `platform` fields (without
`fingerprint_scope`). `provenance` may be `null` when the relationship is
unknown. To permit modification, point it at a regular JSON evidence file and
record that file's actual SHA-256:

```json
{
  "schema": "forge-provenance/1",
  "kind": "build_provenance",
  "source_sha256": "<actual source snapshot SHA-256>",
  "binary_sha256": "<actual binary SHA-256>",
  "issuer": "<build system or record issuer>"
}
```

`kind` may instead be `authoritative_record`. The gate checks that the evidence
file itself matches its manifest hash and that its contents bind both actual
artifact fingerprints. Equal application IDs alone never establish that link.
An unknown or conflicting identity/stack/platform, absent evidence, or evidence
that does not bind both fingerprints leaves `inspect` and `design` available but
blocks `modify`. A file/hash mismatch or malformed manifest blocks every
operation. A `reference_source`, `reference_binary`, or `visual_inspiration`
entry is never a target.

API: `require_valid(path_or_dict)` returns the parsed manifest or raises
`MaterialError` for structural, path, or file-hash failures. `assess(path_or_dict)`
returns `valid`, `status`, `manifest_sha256`, `allowed_operations`, `blockers`,
`claim_limit`, and checked `material_sha256` values. In-memory dictionaries use
the current working directory as the base for relative material paths; file
manifests use their own directory. The CLI exits `0` only when modification is
allowed and `2` for blocked or invalid manifests.

Hashes detect local inconsistency; they do not authenticate a build producer or
the authority named in an evidence record. A passing material gate permits a
modification attempt only; it does not establish runtime readiness or external
write authorization.

## Configure the factory dispatcher

For a new software-change run, start with both options:

```sh
python3 scripts/factoryctl.py start --inputs inputs.json --state run.json \
  --materials materials.json --operation modify
```

Use `inspect` or `design` when that is the actual authorized scope. The factory
stores the absolute manifest path, its byte hash, operation and assessment in
its immutable environment input. `next` and `advance` reevaluate current files;
changed manifests/evidence or an operation outside `allowed_operations` block
dispatch. The returned `materials_assessment` must accompany the worker task.
A valid but unresolved binary/source relationship can proceed under `design`
without becoming a target modification. Missing or changed files cannot.

Old runs without these options remain compatible and return `not_configured`;
they have no material-gate guarantee. Do not silently add settings to an old
checkpoint or relabel design as modify. After an intentional material/goal
change, create a new checkpoint with a newly reviewed manifest and retain the
old evidence. Revalidate the relationship of the frozen snapshot to the actual
working copy before writing: this checker hashes supplied files, not an
unmentioned working tree. The dispatcher does not sandbox the host or prevent
tools being called outside its flow.
