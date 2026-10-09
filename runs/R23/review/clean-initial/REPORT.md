# R23 independent initial reception

The frozen operational workflow is usable for the original task and states a coherent per-method execution and receiving contract. The one-day consumer slice was independently reproduced from the locked raw inputs, including its live late-publication boundary. The slice verifies point forecasting only; its actual output contains no 90% intervals or replenishment quantities, so those mandatory outcomes remain unverified.

## `j1` — workflow-to-source and interface mapping: pass

The neutral task fixes the 2026-10-31 18:00 Asia/Shanghai decision origin, the 42 dates from Nov 1 to Dec 12, 12 stores, 8 items, per-item quantity bounds, daily capacity and budget, no carryover, two loss terms, time-stamped demand revisions/features, and per-method output keys and fields. The workflow maps those to 4,032 keys per method, separate forecast and plan tables, a method registry, point-in-time snapshots, label and feature lineage, full-day calibration vectors, objective/constraint recomputation, fold comparison and paper traceability.

Its full-horizon output contract is directly usable: each requested method must keep its own results, recommendation cannot filter the method set, and the receiving check requires exact keys, IDs, value domains, interval ordering, integer quantities, daily caps, spend and objective evidence. The workflow treats the supplied `shared_ridge10` reference as a migration baseline rather than validated authority and requires an alternative route. Its decisions match the original source definitions and the C13 workflow-design/evaluation guidance.

Limit: the actual one-day point slice uses `shared_ridge10_consumer` and `weekly_median56_consumer` IDs and has no forecast intervals or plan table, so it does not demonstrate the final method registry or delivery interface end to end.

## `j2` — evidence scope and next check: pass

The v2 workflow says full production, full-horizon results, paper and independent acceptance are pending; it disallows future actual-demand claims and separates a bounded slice from full acceptance. The received numeric report labels itself a computed one-day slice, and its excluded-claims list rules out fold ranking, generalization, intervals, optimization, 42-day production, sensitivity, paper and reliability claims. The independent reproduction found no hidden interval or plan fields.

The next checks are actionable and source-bound: derive folds from available history before scoring; retain a later untouched holdout when the authorized history permits; for every frozen method produce all 42×96 rows; recompute key sets, intervals, integer plans, daily constraints, scenario losses and paper claims. The workflow explicitly reports infeasible folds or missing completed vectors as gaps instead of relaxing the gate.

Limit: no such full-run evidence exists in this packet. One historical date and its descriptive metrics cannot establish forecast reliability, interval coverage, an inventory-policy gain, or final paper completeness.

## `j3` — actual consumer slice and boundary: pass, slice scope only

The actual v2 consumer source computes both point methods from R21 raw data at origin `2026-10-14T18:00:00+08:00` for `2026-10-15`, selects labels at the `2026-10-31T18:00:00+08:00` cutoff and contains an assertion for a real later-published training revision. Its command has a source-bound finished/exit-0 receipt. The receiver independently reproduced both methods and checked all 192 output rows against the raw snapshot, target labels, revisions, publication times and reported metrics. The boundary was active: 44 training keys had later-published rows, while the fitted snapshot remained as-of origin; all 96 scored labels were post-origin.

The reported MAE/RMSE/mean signed error for the single date also recomputed: Ridge `2.3345852722 / 2.8712789665 / +1.5008410004` units per pair; weekly median `2.5104166667 / 3.0413812651 / +1.1666666667`. These are descriptive values for one date, not evidence of ranking or generalization. Ten earlier source command receipts have nonzero exit codes; all remain preserved and their permitted process fields match. The receiver did not inspect their argv or streams, so no cause is assigned here.

Limit: the workflow’s specifically described probe for intervals and optimization has not been executed in the received slice. The slice contains no `lower90_units`, `upper90_units`, `interval_level`, `q_units`, scenario table, solver evidence or final method registry. Those checks, every 42-day method output and downstream paper remain unverified.

## `j4` — independent reception and claim language: pass

This receiver checked the original task, criteria, locked source identities, v2 operation documents, actual current source/config/output, allowed probe source and the one permitted full receipt. It implemented and froze an independent computation before running it, withheld author diagnostics and expected values, and checked the emitted numbers against the raw inputs rather than accepting self-report. The operation docs preserve unknown history/fold feasibility and say a short slice does not validate full delivery; the numeric report similarly limits its claims. The current records keep actual model, token count and cost null.

Limit: this is an independent judgment of `j1`–`j4` for the specified workflow version and one-day slice. It is not final acceptance of the 42-day product, paper, calibration, optimization, or any future realized-demand claim.

## Process and identity anchors

- Receiving packet: `runs/R23/receiving-packet/manifest.json` and `receiving-packet-lock.json`; all declared packet artifact identities matched.
- Source process projection: `runs/R23/receiving-packet/process-terminals.json`, 21,899 bytes, SHA-256 `9eec93e8b0f75eff1e771905d20ff6273c5a003bc0d0ad0077018282e3d24307`; 34/34 source receipt identities and projected terminal fields matched. The exact per-record fields are retained in `source-process-fields.json`.
- Actual consumer receipt: `runs/R23/execution/receipts/r23-consumer-30-compute-v2-final.txt`, 7,668 bytes, SHA-256 `07bd5f8517a053050fc5f1f315d0dcc9b7f04b5f225fd7273b500b8ba2c48f49`, schema `forge-command-record/1`, state `finished`, begin `2026-10-09T13:50:22.915932+00:00`, end `2026-10-09T13:50:25.154102+00:00`, exit code `0`.
- Independent source recomputation: code `verify_slice.py` SHA-256 `fa8ce5bc1d33083dd2ecdc701fac7435b638726a8a21cb9044b98791faae2de0`; config SHA-256 `d094a9b56961d64007a9353cf6c27c4d453c9ae62111ae1febf2d947db080e52`; frozen source set is recorded in `freeze.json`; computed evidence is in `recomputation.json`.
- Actual model, tokens, and cost: `null`.
