# Read domain for informed correction

This revision was made in the new domain `runs/R23/execution/design-correction-v2/`. The write boundary is a cooperation contract, not operating-system isolation.

## Material used

- `runs/R23/brief/TASK.md`, with direct source check of line 9.
- `runs/R23/design/WORKFLOW.md`, the frozen original workflow being corrected.
- `runs/R23/initial-reception-lock.json`, read as lock metadata.
- `runs/R23/review/initial/verdict.json`, for the j1 finding only: the verdict says the prior Stage 7 selected one method and had no final future-output/receiving interface for every compared method.

No R21 raw/reference payload or C13 file was reread for this narrow contract correction. No original design, one-day consumer data/output, or v1/v2 scientific artifact was copied into the correction domain. The original design remains untouched.

One command intended to print only `criteria.j1` instead printed the whole verdict JSON to the tool output. The correction uses only the j1 finding quoted above; the other criteria were not used to make any design decision and were not copied into these artifacts. No other review/result file was opened.

## Evidence and limits

The change is an informed correction prompted by a frozen independent j1 rejection, not a new blind design. The source-bound change is limited to the requirement that each comparison method must deliver its own complete 42-day forecast/interval and replenishment tables, with per-method identity, receiving checks, and an honest failure state. The previously consumed one-day slice and its limits are explicitly left unchanged. The current operational document does not include the old verdict label or reviewer diagnosis; those facts stay here and in `CORRECTION-STATUS.json`. The self-check verifies the contract text and 42×12×8 count; it does not run production or provide an independent verdict.

All shell actions use `scripts/record_command.py`; their unique receipts are stored in this directory's `receipts/`.
