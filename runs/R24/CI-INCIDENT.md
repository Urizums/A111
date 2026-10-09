# R24 PR #4 CI incident and repair (2026-10-10)

## Original observed failure (retain, do not rewrite)

On draft commit `71eddd5415abf7aed48bdce110576e6937759c76`,
GitHub Actions push run [37959989621](https://github.com/Urizums/A111/actions/runs/37959989621) and PR run
[37960057311](https://github.com/Urizums/A111/actions/runs/37960057311)
both failed during `python scripts/verify_handoff.py --json`.
The PR Python 3.10 job reported exactly:

- `hash or size mismatch: CODEX_HANDOFF.md`
- `hash or size mismatch: README.md`
- `hash or size mismatch: START_HERE.md`
- `release manifest coverage differs: ['CURRENT_STATUS.md']`

Windows preflight passed; other Linux validation steps were not run.
The C14 text was not shown to be functionally incorrect by these failures,
but the initial GitHub document edits violated frozen release invariants.
This was a genuine submission/integration error.

## Repair policy and scope

- Restore the three protected root files by reusing their exact `main`
  Git blob identities; no wording edits remain in those paths.
- Remove the unregistered root `CURRENT_STATUS.md`, and retain the
  equivalent current-status snapshot under `runs/R24/CURRENT_STATUS.md`
  (outside the protected static-release file set). This is a dated
  review pointer, **not** a replacement for frozen handoff files.
- Keep nine C14 candidate Markdown files and all R24 proposals in the
  mutable `runs/R24/` research domain. Never change original
  `state/source-lock.json`, `artifact-manifest.json`, revision locks
  or `scripts/verify_handoff.py` to make this draft pass.
- Do not mark CI green, independently accepted, or C14 promoted
  until new run results are observed.

## Residual editorial issue

The old root README contains historical "current" descriptions.
Changing those requires a separately authorized, correctly registered
release update. Until then, read `state/checkpoint.json` and the
R24 snapshot with explicit as-of dates; do not reinterpret old narrative
as a fresh state or silently edit a frozen release file.

## Evidence limitations

A green integrity CI checks repository packaging/invariants and existing
regressions, not new C14 behavioral superiority or independent actor
review. No R24 C13-vs-C14 fresh matched experiment occurred during this
repair. The earlier failing runs remain in GitHub history.
