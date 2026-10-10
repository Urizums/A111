# R24 — genuine checkout execution, source identity and release-boundary repair

Recorded: 2026-10-11 (UTC+08). Scope: PR #4, `rd/c14-necessity-review-20261010`.

## Proven progress: real source files and Python CLI

The exact source preflight introduced by commits `10039656089e7015d662f2b8e64ba7c026b9ebae` (Python) and `6224394ff1d8acac7a068e43f8ed3f9a022dd8a4` (GitHub Action) **actually executed** on GitHub's complete repository checkout.

Evidence: [R24 genuine checkout run 38077885648](https://github.com/Urizums/A111/actions/runs/38077885648), `genuine-checkout` job ID `114288581114`, conclusion **success**. The Actions logs confirm completion of:

- Python 3.12 bytecode compilation for the exact V7 candidate and preflight;
- V7 deterministic author-side `selftest`;
- `ci_genuine_checkout_preflight.py` on 18 real Markdown Skill files (9 C13 + 9 C14-lean), with source catalog fixed at Git Blob `c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0`;
- **two** real CLI `prepare` runs, seeds 12345 (`extract`, arm A=C14-lean) and 314159 (`reconcile`, arm A=C13), including frozen identity of each copied candidate, two opposing assignments, SHA-256 freeze tokens, and a sealed-grade non-success on deliberately empty submissions;
- a disposable mutated-Skill source must fail source attestation; the original source directories are left unchanged.

The job asserts that the number of V7 deterministic checks is positive and every one passed; prior exact-script R24 evidence reports 45/45. Workflow artifact `r24-genuine-checkout-receipts`, artifact ID `11678708974`, uploaded successfully per job log. Do not confuse these author-code checks with real model behavior.

This changes the historical `actual_18_file_prepare` gate from `not_run` to **`passed_ci_genuine_checkout_2_cases`** as of this observed run. The former not-run record is historically correct for its earlier observation and must not be overwritten. This does **not** establish human/AI actor model delivery, Skill-reading traces, host process isolation, cold semantic reuse, relative effectiveness or a candidate winner.

## First integration failure retained and repaired

The successful R24 workflow introduced a file beneath `.github/workflows/` that is **not listed in the repository's frozen release manifest**. Both original `Cloud delivery validation` runs against commit `6224394f` failed with the precise error:

```text
release manifest coverage differs: ['.github/workflows/r24-genuine-preflight.yml']
```

Evidence: [push run 38077880941](https://github.com/Urizums/A111/actions/runs/38077880941) and [PR run 38077885598](https://github.com/Urizums/A111/actions/runs/38077885598). The failure occurred at `scripts/verify_handoff.py --json`, **not** at the R24 V7 source prepare. Do not mark those runs green retroactively.

Repair:

1. Preserved an explicitly *inactive* workflow template at `runs/R24/studies/genuine_checkout_workflow_template.yml` (commit `f0eb831029ba83020084ca3e4b675d9df2c299c9`).
2. Removed the unregistered active `.github/workflows/r24-genuine-preflight.yml` from the draft branch (commit `e8296a824781e8ca2a011e4ed86fab0aab178c83`).
3. Did not modify `artifact-manifest.json`, `state/source-lock.json`, `scripts/verify_handoff.py`, C13, C14-lean or any frozen release-root payload.
4. The retained `runs/R24/studies/ci_genuine_checkout_preflight.py` can be run on any authorized full checkout by invoking the exact V7 CLI and itself. Re-activating the archived workflow in `.github/workflows/` requires an independently approved, correctly registered release-manifest change; the inactive template is not a live scheduled check.

Before taking the generic CI repair as finished, inspect the actual **new head** `Cloud delivery validation` outcomes and retain failed logs if any.

## Next genuine research gate (not performed)

- Run C13 and C14-lean on **fresh unseen materials** in two genuinely distinct Agent contexts, identical models, tools and budget, with reviewer oracle and opposing arm hidden at the host level. Freeze the protocol before first dispatch and collect actual Skill-read/tool/execution traces, source and output digests, initial failures, resource costs (null if not surfaced), and durable receipts.
- Run an actually separate receiver using only the sanitized packet and real `workflow.md` output, then compare domain correctness, necessary vs unnecessary work, failure handling, and independent usability.
- If these independent contexts are unavailable, the gate stays **blocked/not run**. Do not promote C14-lean, declare a version winner, merge PR #4 or start R25 solely from this preflight.
