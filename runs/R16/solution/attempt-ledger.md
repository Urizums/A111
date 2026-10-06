# R16 attempt ledger (producer, current case)

Status: paused at coordinator instruction on 2026-10-07. No solver execution has occurred. Do not infer a solved result from files present in this directory.

## Observed command/construction sequence

1. A `py -3.12 -X utf8 -c ...` one-line extraction command failed with `SyntaxError` due to invalid comprehension syntax. It ran directly, outside `scripts/record_command.py`; therefore no receipt exists. Recovery action: authored `read_sources.py` and ran that new construction.
2. The first recorded `read_sources.py` run failed with `StopIteration` because its source path was rooted at `A111/source` instead of `A111/runs/R16/source`. Its raw command record is `receipts/01-source-read.json` (exit code 1). Recovery action: changed the script's path calculation and constructed a second recorded command.
3. The second recorded `read_sources.py` run succeeded and read all three official corrected originals. Its raw command record is `receipts/02-source-read.json` (exit code 0). This is the only successful source-reading command receipt.
4. `solve.py` was authored but has not been executed. It is unverified and must not be treated as an achieved baseline or result. Any future instruction to resume must first reconcile the original case's correction budget with the coordinator; do not overwrite these receipts or count a new actor as a reset.

## Budget accounting question for coordinator

At least one failure-driven correction is clearly evidenced: item 2's wrong-path script fix. Item 1 also has a failed command and a replacement construction; whether that is a separate correction under the frozen source/orchestration/construction/fallback policy requires coordinator adjudication. There was no solver child process and no solver fallback. Do not silently omit the failed initial command merely because it had no receipt.

## Boundary disclosure

One earlier PowerShell command unintentionally resolved a path and displayed `source-manifest.json`, outside the authorized read list. Its contents were not used in modeling, computation, claims, or this ledger; the file must not be read again in this case. Authorized original-source facts were extracted directly from the corrected PDF, DOCX, and XLSX.
