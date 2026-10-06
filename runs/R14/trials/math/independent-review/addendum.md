# Independent review addendum — round 2

This is the second review after coordinator requirement and locator feedback. The initial blind review remains unchanged in `review.json` and `review.md`. This addendum used only the original L3 request, the C9 lock/skill accounting rule, the L3 original result/receipts, and actual L1–L8 trial files for locator validation. No root diagnostic or later author reconciliation was used.

## Revised finding

**L3 m5 changes from pass to fail.** L3’s request sets a two-correction limit. Its result records two source/construction corrections and separately records an earlier orchestration failure: initial reads used the wrong relative prefix, three lookups failed, then the paths were corrected. Under C9’s rule to accumulate source, orchestration, construction and fallback corrections, that recovery is one additional correction. The L3 case count is therefore **3/2**, not 2/2. The three failed lookups share one cause and count as one correction event.

The C9 candidate lock separately records 0 source repairs + 2 orchestration corrections = **2/2** in its own frozen history. The combined lineage event total is 5 (C9 history 2 plus L3 case 3), but the lock and L3 request define separate budget domains; the L3 case alone already exceeds its own limit. The producer’s `correction_budget_count: 0` for the failed-path event is inconsistent with cumulative correction accounting. L3’s source-check, main-smoke and malformed-input receipts are real and retained; they do not erase the budget overrun.

The lookup failure appears in L3 `result.json` and `verification.md`, but no raw command receipt for those failed reads was found. Thus the event is recorded and countable under the cumulative rule, while its exact command-level details remain unverified.

## Locator correction

The initial review used a generic `solve.py` source path for every level in m2/m3. The actual L1 and L2 producer source is `solver.py`; L3–L8 use `solve.py`. The initial m4/m5 entries also named artifact classes without exact filenames. The filesystem locator audit is in `round2-locator-audit.json`; all corrected source, results, workflow, paper, figure, verification and receipt paths listed there exist. These locator fixes do not change the other substantive m1–m4 findings.

## Status and budget

The overall review now has **38 pass, 2 fail, 0 unverified** across the 40 checks. L7 m3 remains the original failure; L3 m5 is the new failure. The reviewer used its second and final correction round: round 1 corrected the independent calculation script’s indexing error; round 2 corrected evidence locators and cumulative budget accounting. Reviewer budget is **2/2**. No third review round will be performed, and no locked producer artifact was changed.

Findings remain bounded to these eight math artifacts and the shared detailed contract. Per-level validation folds differ. No level-causality/ranking or competition outcome follows; model identity, token use and cost remain unknown/null.
