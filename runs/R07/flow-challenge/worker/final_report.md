# Result report

## Outcome

Assisted completion after the original roughly five-minute window ended before any artifact or native call had been persisted. The parent authorized a short continuation of the same task; this is not reported as an autonomous within-window pass.

The local Python tool ran on the five byte-copied source files and retained all seven requests. It assigned 3 `ready`, 2 `conflict`, and 2 `needs_info`; complete processing order is R01, R05, R07, R02, R04. The remaining counts for 2026-10-08 are E01: 0, E02: 2, E03: 0. The independent Luna/max source reviewer recomputed these values and rated allocation content and the duty checklist as pass.

The successor step was executed: `successor/make_checklist.py` produced the staff checklist with R03 (missing room) and R06 (unknown E99 identity/ledger quantity), including fill-in and review fields. No approval, notification, network, or other business effect occurred.

## Run and review evidence

- Runnable tool and command: `tool/allocator.py`, with full invocation in `tool/README.md`; actual allocator and checklist command argv/stdout/stderr/exit codes are in `evidence/commands.json`.
- Source coverage check: `evidence/result-check.json`; independent review: `reviewer/report.json`. The reviewer confirms all source rows, sorting, stock balances, status and checklist content. Its report notes that these inputs exercise one date per item only and do not cover malformed quantities or other absent fields.
- Native evidence: `native/create-intent.capture.json`, `native/create-receipt.json`, `native/create-return.capture.json`, both scoped status observations, `native/final-reply.txt`, and `native/terminal-notification.capture.json`. One real `gpt-6-luna` / `max` native reviewer was created and reached completed status; 2/2 scoped status queries were used. Tokens and cost are null. The reviewer’s operational-proof rating is limited because its read scope excluded coordinator command and native receipts; its source-content review remains independent.
- Input identity: `evidence/final-input-integrity.json` confirms all five copies match the original source bytes and hashes.
- Failure and repair history: `evidence/result-check-attempt-001.json` preserves the failed checker run. A broad text regex falsely matched the CSV field name `requests`; this consumed one harness repair. `evidence/result-check-command-precorrection.json` preserves the earlier incorrect exit-code envelope, while the corrected failure record retains the actual exit code and traceback. The corrected check passed on attempt 2. Total harness repairs: 1 of 2; candidate code repairs: 0. No remaining budget was reset.

## Limits

The tool’s result was exercised directly on the supplied seven-row input and independently source-checked. No frozen multi-case `caserunner` suite was run in the short recovery, so unrepresented branches such as multiple dates, malformed quantities and invalid priority values remain unverified. The initial cutoff, first checker failure, and local observation limits are retained above.
