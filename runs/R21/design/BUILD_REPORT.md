# R21 workflow builder report

## Result and handoff

Built [`WORKFLOW.md`](WORKFLOW.md), a reusable pure-Markdown workflow for a different executor to solve the complete original fresh-food planning task and produce a scientific Chinese paper. It derives the executor duties from `REQUEST.md`, `PROBLEM.md`, the raw attachments, the supplied baseline migration contract, and the C13 workflow's outcome, handoff, as-of lineage, fair comparison, evidence-gate, iteration, and truthful-continuation requirements.

The next executor should read `WORKFLOW.md` and then restart from the source-bound R21 inputs for the actual modeling task. This builder did not fit a model, choose a winning route, produce forecasts/plans, run the proposed scientific experiment, draft the paper, or establish execution acceptance. The workflow asks the executor to treat `experiment.json` as a versioned proposed protocol, verify it against the task and information timeline before looking at results, retain its history, and record any prospective change before performance inspection. It does not prescribe a general model/page/retry quota or promise improvement, award, coverage, or optimality.

## Scope and evidence

Read the repository `AGENTS.md` because it defines the continuation context, and otherwise limited source reads to the named C13 skill and its eight references, `C13-lock.json`, R21's request/problem, input lock, raw attachments, reference baseline/config/code, and `scripts/record_command.py`. No other R19/R20/R21 material, root protocol/evaluation, diagnostics, output, later truth source, or external contest answer was read. The C13 listed source hashes and all R21 locked input hashes matched their respective locks in recorded commands.

`first-step-command.json` is the first recorded input-consumption command. It read and emitted the full locked R21 input streams and their SHA-256 hashes. This receipt includes the public demand report export. Its service dates end on 2026-10-31; the later publication timestamps (through Nov 3) belong to revisions of those historical service dates. The export does not contain the withheld 2026-11-01–2026-12-12 evaluation truth. The later audit summary independently reported the service-date range; no future planning-period demand values were extracted, scored, summarized, or used. The workflow explicitly forbids using post-origin versions to train, calibrate, select, or construct the 42-day plan, and requires full-group availability for residual calibration.

Recorded source checks:

- `first-step-command.json`: actual first input read, complete stdout/stderr streams and exit status retained by `record_command.py`.
- `source-audit-command.json`: verified each R21 input-lock entry by exact byte count and SHA-256; summarized source schemas, rows, key/revision structure and selected metadata. It did not compute future-period outcome metrics.
- `reference-code-audit-command.json`: retained the inspected excerpt of the supplied reference `run.py` for versioned snapshots and as-of features.
- `c13-lock-audit-command.json`: verified all nine C13 source-file hashes against `C13-lock.json` and recorded the lock's own hash.

Each receipt retains actual command arguments, working directory, start/end, exit code and complete text/base64 streams. The source locks attest byte identity only; these builder checks do not validate the quality or acceptance of a later scientific execution.

## Exact source hashes

SHA-256 values below are for the exact files read. C13 entries were checked against the adjacent lock. R21 input entries were checked against `runs/R21/input-lock.json`.

### C13 workflow source

| File | SHA-256 |
| --- | --- |
| `runs/R20/final/candidate/C13-lock.json` | `860caeec761028fa47723410c99ef2f48db2f61fa16405c8929a0005e158af7a` |
| `runs/R20/final/candidate/C13/forge-agent-flow/SKILL.md` | `8128c05049d3918042c89389d8b2db73f8626b94b642fcf9491952c05944adea` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/workflow-design.md` | `61412192fa7bddb0001214083d270efa3566dbb60431ec0f156d89ad9fe655aa` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/source-evaluation.md` | `fb79b4634c5fb2cae08550243f379152f939568c66497c1ddf0f5a630edc5696` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/modeling.md` | `e102ff9db978fd4bc685836b60a8a4c9cb72bd2a14f14f73aafb191766af5c64` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/iteration-and-recovery.md` | `5b82a336a88ea1adfef33dbc530c854290fc21965c01cf0d5d760458fea80675` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/evaluation.md` | `089568516bfc2f8cd4ed46bf1429fc0c4e7e0552400cdb42d1bbb363e9908a5f` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/collaboration.md` | `e47019551555763e42275ec7077370c0bd6cb658df5e53b12a02eebd56cbcb9f` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/continuation.md` | `28c33eae756b7e0522f5a913b849f5d02c97ce5e8e81fc6c7bfcc0e269c95390` |
| `runs/R20/final/candidate/C13/forge-agent-flow/references/frontend.md` | `cecbe0047fa7d61c8cbe9bc014341586d0be85128bb18724b799414cadd6f7db` |

### R21 source-bound inputs

| File | SHA-256 |
| --- | --- |
| `runs/R21/input-lock.json` | `dcd4f9ffd67097e6dc53cc919ed0333f9340f7dc938d7c6ea3694af7f33d53d7` |
| `runs/R21/inputs/REQUEST.md` | `ba9abf0100741a7d3fa25d2f569279436509f406f3686d04b35c22c085e9af3a` |
| `runs/R21/inputs/PROBLEM.md` | `835bb83f86e4581c191bbf7e1f379e3d7cea7f6f675cc7a0f58e7ab7242caf17` |
| `runs/R21/inputs/raw/calendar.csv` | `1676e38b047d96b7b66d294d85673f86f876826e96c03b29200c340cad24fbfd` |
| `runs/R21/inputs/raw/decision.json` | `7540cf7083f0163f60e431e8a75f552baa86ed174869f3c55aac69f904056753` |
| `runs/R21/inputs/raw/demand_reports.csv` | `80a3a994b8285caa0b48bf433724d476693509656b32cff99b8a6798eebd666b` |
| `runs/R21/inputs/raw/items.csv` | `bc81cb9ad6c28e108bbd4e1fcd682c4c8aa71e40c22e7ff8411b545a4fe65167` |
| `runs/R21/inputs/raw/promotions.csv` | `580c15bc827a8d86113c8ceb47edce2bfa94b317f4d88ff3a45b3e7c0c55bb45` |
| `runs/R21/inputs/raw/stores.csv` | `65ce636c8d7f6c72df3d06a1e84e59d122f33dab1c223d4e9963982c9bf54220` |
| `runs/R21/inputs/raw/weather.csv` | `8dd38ca926ba59b0de292e0b57a3e07cb4353d892cc3dd242aea8cc6f56c8403` |
| `runs/R21/inputs/reference/BASELINE.md` | `edd81388fbd5e4a3115efab7d2d1f617116be59bc162e52d1fcb387975d13855` |
| `runs/R21/inputs/reference/experiment.json` | `dd5f141e37c5e1929f0f65d8d834b6a1aa7da6b0bf21d58a8d3595675a92e307` |
| `runs/R21/inputs/reference/run.py` | `4a6198d7c2cfea627c0f74aad5aa0ca4e88841f3e23b9d961185d423a0c3cf24` |

## Assumptions and limits

- The supplied request/problem and frozen baseline migration text define the modeling task; this workflow does not infer hidden contest scoring criteria.
- The supplied `experiment.json` is an input protocol proposal whose actual time boundaries and feature availability must be checked before performance is viewed. No experiment results or preferred candidate are included here.
- `interval_level=0.9` denotes the requested nominal marginal interval level; future empirical coverage remains unknown until the hidden evaluation period is released to a separate receiver.
- Whether an optimizer proves exact optimality depends on the executor's solver evidence. The workflow distinguishes feasible plans from proven optima.
- No actual solution execution, independent acceptance, competition submission, or performance guarantee is claimed. No code or test suite is packaged in the workflow.
- Actual model, token use, elapsed work telemetry, and cost were not available as verified measurements; keep them `null`/unknown.
