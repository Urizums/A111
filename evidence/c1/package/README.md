# C1 package block evidence

Four package samples were run in the frozen order B1, A1, A2, B2 against the unchanged package and notes. Each sample has an original bridge job, one requested gpt-6-luna/max/fork-none worker, an independent source review using the original v1 acceptance, and a recorded terminal checkpoint result.

| Sample | Treatment | Business v1 | Controller terminal | Requested worker | Status queries / waits | Capture grade |
|---|---|---|---|---|---:|---|
| B1 | B/hostdraft | pass | completed | gpt-6-luna/max/none | 5 / 4 | qualified with material gaps |
| A1 | A/manual | pass | completed | gpt-6-luna/max/none | 3 / 3 | qualified with a worker process-capture gap |
| A2 | A/manual | pass | completed | gpt-6-luna/max/none | 4 / 4 | qualified with unverified worker setup and a missing decision-begin marker |
| B2 | B/hostdraft | pass | completed | gpt-6-luna/max/none | 4 / 3 | qualified with coordinator protocol and marker deviations; worker skill read unverified |

The v1 source rule is unchanged: every quote must be an exact substring; only explicit actions are included; unstated owners/dates remain null. The independently reviewed rows are in each sample's `review/source-review.md`. The frozen no-action branch was not run, and no cross-block or speed claim is made.

Evidence indexes: `cli-index.json` preserves every captured argv/stdout/stderr/exit and timing record found at build time; `native-index.json` keeps native intent/return observers and raw native files; `marker-index.json` keeps all stage markers. Per-sample `index.json` files link the evidence and show only uniquely paired same-boot spans as durations. Missing, duplicate, or cross-boot markers remain unverified.

Material qualifications are retained in `block-summary.json` and each sample index. B1 preserves boot-change recovery, late observe imports, worker/output corrections, and an initial package-assessment error. A1 preserves a worker's disclosed uncaptured mkdir and a Flow-envelope packaging caveat. A2 preserves unrecorded worker setup reports, an incorrect coordinator capture path, and a missing decision-begin marker. B2 preserves the premature duplicate setup end, two failed bridge state transitions before recovery with the original receipts, one failed capture-index parse, and an unverified worker SKILL read. Root assistance is documented where it affected recovery.

The final index-builder subprocess is itself captured at `package/B2/logs/037-build-block-indexes.json`; it is excluded from the indexes it creates to avoid a self-referential capture. Earlier captured index/audit commands remain in the CLI index. Coordinator direct-write operations are disclosed separately in the sample indexes and raw-return files.

Source, protocol, and installed Forge code hashes are listed in `block-summary.json`. Hostbridge telemetry reports internal model identity unverified and token/cost fields null.
