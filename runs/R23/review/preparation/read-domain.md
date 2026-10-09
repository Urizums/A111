# R23 receiver read-domain record

**Role/state:** independent receiver, preparation only. No formal acceptance or producer-output review has begun.

## Authorized materials read

- `AGENTS.md` as repository context; the current assignment's narrower boundaries take precedence.
- `runs/R23/acceptance.json`, `runs/R23/brief/TASK.md`, and `runs/R23/brief/INPUTS.json`.
- `runs/R20/final/candidate/C13-lock.json` identity and C13 package `SKILL.md` plus permitted references: collaboration, continuation, evaluation, frontend, iteration-and-recovery, modeling, source-evaluation, workflow-design.
- Permitted R21 business materials: `runs/R21/inputs/raw/`, `runs/R21/inputs/reference/`; R21 input-lock identity only.
- The R21 lock inventory filtered out REQUEST/PROBLEM path entries. Neither REQUEST nor PROBLEM content was opened.

## Source-bound preparation observations

- R23 acceptance sets j1–j4: traceable source-to-claim/interfaces; evidence scoped to actual support; a real different-consumer slice; and fresh independent reception. It rejects fixed model/page/window/universal-retry quotas and distinguishes a bounded slice from full delivery.
- The task and `runs/R21/inputs/raw/decision.json` set origin `2026-10-31T18:00:00` Asia/Shanghai, horizon `2026-11-01`–`2026-12-12` (42 days), 12 stores × 8 items, 1,600 units/day capacity, 6,000 yuan/day procurement ceiling, fresh daily/no carry inventory and lost unmet demand. `calendar.csv` labels a fictional activity, not an official holiday.
- `items.csv` sets per-item procurement, shortage and waste amounts and a 55-unit/day item ceiling. The task makes shortage and waste objectives, procurement a constraint.
- Demand reports contain 21,609 rows for 17,664 service/store/item keys, revisions 1–2, with availability timestamps through 2026-11-03. At the decision cutoff 21,441 rows / 17,568 keys are available, latest available service date is 2026-10-30, and 168 rows / 145 keys are later arrivals. These are inventory facts, not model or quality results.
- Promotions contain 4,032 rows in the future horizon; 960 across 10 service dates are announced by cutoff. Weather has 126 future forecast rows, 42 available by cutoff, and no future observed rows. Availability/publication time is therefore a concrete reception concern, not a model prescription or coverage promise.
- R21 reference files are supplied business references for comparison/migration, not independent validation or an oracle. The C13 lock explicitly claims exact terminal bytes, not substantive acceptance.
- Lock identities and file hashes are in `receipt_07.json`; compact source/time counts are in `receipt_08.json`.

## Boundaries honored

No R23 design, execution, review, results, evaluation, generator, audit or production output was opened. No R22 protocol/audit/results/papers/reviews or root expected design/diagnoses were opened. No R21 REQUEST/PROBLEM contents were opened. No shared TODO/state/product file was read or written. Work is confined to `runs/R23/review/preparation/`.

## Receipt notes

Every shell action used `scripts/record_command.py` with a unique receipt. `receipt_02.json` records a failed lookup for nonexistent `runs/R23/brief/source-lock.json`; the packet identifies `runs/R21/input-lock.json` and `runs/R20/final/candidate/C13-lock.json`. The failed lookup read no content and remains preserved. `receipt_05.json` records a second failed lock-path lookup (`runs/R21/inputs/input-lock.json`) after reading only authorized raw/reference sources; the actual allowed lock is `runs/R21/input-lock.json`, read in `receipt_07.json`. `receipt_01.json` records a PowerShell display-encoding issue; a UTF-8 reread provides legible AGENTS content. `receipt_09.json` preserves a failed preparation-file write (Python command quoting syntax error); no output file was accepted from that attempt. A later encoded PowerShell write produced PLAN.md under `receipt_10.json`; read-domain.md was first written under `receipt_11.json` and its final revision under `receipt_14.json`. One oversized encoded-command attempt failed before process creation, so it had no shell child or command receipt; the subsequent individual writes completed. The final preparation status is written under `receipt_15.json`.