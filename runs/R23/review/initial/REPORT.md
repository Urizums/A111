# R23 independent reception

## Verdict

Overall: **fail**, because j1 has a source-bound missing mandatory interface. j2, j3 and j4 pass within their stated scope. This is the first complete independent verdict; no repair feedback or root judgment was received before it was written.

The frozen task requires point forecasts, nominal 90% intervals and integer replenishment for the fixed 42-day plan. It also specifies keyed forecast/interval and replenishment tables for each method (TASK.md lines 7 and 9). The workflow maps dates, stores/items, daily resource constraints, time availability, modeling/evaluation stages, and a Chinese-paper consumer. However Stage 7 refits only “the selected eligible method” and its table contract is 4,032 rows “per selected method” (WORKFLOW.md lines 44 and 53–54). The design does not say how the future forecast, interval and replenishment tables for every compared method are emitted and received. That is the j1 failure.

## What the actual slice establishes

The frozen consumer slice is a single historical origin, 2026-10-14 18:00 Asia/Shanghai, for target date 2026-10-15. It computes two point methods over 96 store/item pairs, using demand labels published by the evaluation cutoff 2026-10-31 18:00. It does not compute intervals or replenishment. The design and its consumer configuration explicitly distinguish this smoke from full delivery and reliability.

I independently recomputed from the R21 raw inputs without importing or invoking the consumer program. All input hashes match the permitted R21 input lock; the design, consumer, config, freeze, CSV and report match their corresponding design/execution lock entries. The training snapshot has 15,936 rows; its 56-day window has 5,376. There are 166 report rows arriving after the forecast origin and 44 training keys with later reports. The boundary is real: for S01/K03 on 2026-10-12, revision 1, available 2026-10-13 09:00, is visible at the 2026-10-14 18:00 origin; revision 2 arrives 2026-10-15 09:00 and is excluded. All 96 target labels are post-origin and available at the evaluation cutoff (75 revision 1, 21 revision 2); 96/96 promotions are announced by the origin.

The independently recomputed Ridge forecasts differ from the CSV by at most 4.94e-11; the weekly-median forecasts match exactly. Recomputed MAE, RMSE and mean signed error match the consumer report for both methods. These observations support the actual one-day point-forecast path and its availability boundary. They do not support future 42-day reliability, nominal interval calibration, an optimized replenishment plan, or a full modeling paper.

## Actual consumer process and preserved failures

The final v2 consumer invocation is recorded at runs/R23/execution/receipts/r23-consumer-30-compute-v2-final.txt with exit code 0. The execution lock lists 34 command receipts; I checked each receipt's bytes and begin/end fields against the lock: all identities match, all have begin/end, with 24 exit-0 and 10 exit-1 commands.

The nonzero events remain visible and are not reclassified as passes: #05 boundary-search command had a Python syntax error; #09 compute found malformed freeze JSON; #11 freeze repair still failed JSON parsing; #13 compute found a raw-source hash mismatch; #16 compute still found malformed JSON; #19 v2 source-freeze command had a quoting syntax error; #21 v2 compute received literal backslash-n source text and failed parsing; #22 source-repair command exited with an IndexError after writing, followed by a source check and a separate repair; #25 v2 compute resolved runs/runs/... and could not find the config; #27 compute found a code/freeze hash mismatch. Subsequent records preserve corrections and retries; #30 is the final v2 computation with exit 0. The final strict-cutoff source and outputs are independently checked above. These are consumer process events, separate from my own receiver-tool failures below.

My own retained process events are in runs/R23/review/initial/receipts/: #005 attempted to freeze before the checker existed at the assigned A111 path; a patch-tool path initially targeted the default workspace root and was immediately removed before execution, then #006 wrote the checker in the assigned domain. #008 ran v1 of my checker and stopped because I had assumed the config encoded a numeric 56-day window; the frozen config states it in prose. I preserved that failure and corrected only the contract check in recompute-v2.py, froze v2 at #011, and executed it at #012. #014 was a receipt-history query with the wrong path base; #015 corrected the query. These receiver failures are not production failures and do not change the consumer's record.

## Criterion results

- **j1 — fail.** The final future-output interface is singular (“selected eligible method”) while the source requires method-specific forecast/interval and replenishment tables. See verdict.json for exact source and artifact pointers.
- **j2 — pass.** The workflow and slice label the one-date evidence narrowly and leave a concrete full-horizon acceptance path.
- **j3 — pass.** Another consumer ran the frozen slice from the locked raw inputs; the source boundary was actually activated, the output was independently recomputed, and the consumer's failures remain preserved.
- **j4 — pass.** This receiver had no producer diagnostics, expected answers or prior verdict. The report was inspected as an artifact, not treated as an oracle. Claims and limits were checked against source and actual output.

No method, tokens or cost telemetry was available; all remain null. No model, page, window, universal retry or award-quality quota was introduced. The 42-day outputs, per-method future outputs, 90% intervals, replenishment/optimization, comparisons and Chinese paper remain outside what this slice establishes.