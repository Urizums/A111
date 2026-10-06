# Independent math review — R14 comparison branch

Scope: eight current locked math trial artifacts only. This is the R14-02 mathematical comparison branch; it is not an R14-04 two-domain overall pass. Review used the original case and each level request, independently recomputed results before considering producer self-checks, read actual command receipts, and visually inspected all eight figures.

## Independent recomputation

OLS on the supplied weeks 1–8 gives week-9 demand predictions A=28.000, B=20.357, C=30.679 units/week. Own rolling-origin validation targets weeks 3–8; trend MAE is A=0.000, B=1.414, C=1.631, versus persistence MAE 1.000, 1.333, 1.667 units/week. Since fold windows differ by level, each artifact was compared against its own declared windows.

Direct enumeration of all 24,076 feasible integer allocations under the original objective gives A=28, B=2, C=30, using 60 units, with objective 264.928571 CNY. L7 ceil-rounds predictions before defining its objective; it returns A=28, B=1, C=31 and 270 CNY. On the original unrounded objective that allocation costs 266.142857 CNY, so it fails m3.

## Per-level findings

| Level | m1 | m2 | m3 | m4 | m5 | Case corrections |
|---|---|---|---|---|---|---|
| L1 | pass | pass | pass | pass | pass | 1/2; initial lock-hash check failed and remains explicitly unresolved; candidate author budget 2/2 is separate |
| L2 | pass | pass | pass | pass | pass | 0/2; malformed rejection is expected boundary behavior |
| L3 | pass | pass | pass | pass | pass | 2/2; two producer corrections retained |
| L4 | pass | pass | pass | pass | pass | 0/2; malformed rejection is expected boundary behavior |
| L5 | pass | pass | pass | pass | pass | 1/2; initial plot-unit ambiguity corrected and prior figure retained |
| L6 | pass | pass | pass | pass | pass | 2/2; initial NameError corrected; later legend command failed due cwd and budget exhausted |
| L7 | pass | pass | fail | pass | pass | 2/2; forecast legend fixed; malformed-error-message patch did not apply |
| L8 | pass | pass | pass | pass | pass | 0/2; main and malformed original-session outputs were unavailable, later recorded reruns retained distinctly |

For every m1–m5 judgment, the JSON entry provides the exact source/artifact set, check performed, reason and limitation. L7 is the only substantive mathematical failure: its solver changes the given optimization objective through upward rounding. Its reported plan remains feasible, and its optimality argument is valid only for that changed rounded-demand model.

## Evidence and limits

Before reviewing the outputs, I compared all 99 math L1–L8 files listed in the output lock by size and SHA-256; all matched. The lock audit and its command record are retained. The review used the real trial command records for valid and malformed paths, including exit status and captured output; producer passes were not used as a numerical oracle. All figures were opened with image inspection. L6’s forecast marker legend is generic, but the series colors and matching paper/results make the plotted values traceable, so no extra polish criterion was imposed. L8’s preserved command records are later reruns; the review treats them as such. Producer failures and correction budgets remain as recorded.

The reviewer’s first calculation command failed on its own rolling-origin index range; that failure is retained and was corrected once. The corrected independent script ran successfully. No locked file, solver, or producer artifact was edited.

This supports only per-requirement findings on these eight small synthetic-task outputs and the shared detailed contract. Per-level fold windows differ. It supports no causal Level ranking, award prediction, contest standing, or general performance conclusion. Requested model labels do not establish authenticated identity, tokens or cost; those remain unknown/null.

## Artifact paths

- `review.json` — machine-readable verdicts, evidence, limits, recomputation and budgets.
- `recompute.py` and `independent-calculations.json` — independent standard-library calculation.
- `verify_lock.py`, `lock-audit.json`, and `lock-audit-command.json` — byte-size and SHA-256 check for the 99 locked math trial files.
- `recompute-command.json` and `recompute-command-correction-1.json` — original and corrected command records made with `scripts/record_command.py`.
