# Clean initial reception: read domain

This is the source and process boundary for the independent `j1`–`j4` reception.

## Materials read or checked by identity

- Repository instructions `AGENTS.md`; neutral `runs/R23/brief/TASK.md` and `INPUTS.json`; only `j1`–`j4` in `runs/R23/acceptance.json`.
- The nine C13 Forge Markdown files and `C13-lock.json`; the frozen design v2 `WORKFLOW.md` and `METHOD-OUTPUT-INTERFACE.md` plus `design-correction-v2-lock.json`.
- R21 `input-lock.json` metadata, all `raw/**` inputs and all `reference/**` inputs. The request/problem paths in the lock were identity metadata only; their contents were not opened.
- Receiving packet `manifest.json`, `receiving-packet-lock.json`, and `process-terminals.json`.
- Current numerical slice only: `execution-lock.json`; v2 `consumer_slice.py`, config, freeze, CSV and numeric report; `design/probe.py` source only. The current actual consumer receipt `execution/receipts/r23-consumer-30-compute-v2-final.txt` was the only full historical receipt read.

The packet manifest entries, both packet-lock members, v2 execution-lock entries, the two design-v2 Markdown lock entries, the C13 Markdown lock entries and the R21 raw/reference lock identities matched their recorded sizes and SHA-256 values. The independent recomputation freeze contains 38 source identities; all source checks matched.

## Process evidence read

`process-terminals.json` has 34 source receipt projections. Each source receipt was read only as bytes for size/SHA-256 and parsed in memory to compare `schema`, `state`, `begin`, `end`, and `exit_code`. Those five fields and source identities matched for all 34. No historical argv or stdout/stderr streams were printed or inspected. The projection contains 10 nonzero exit codes; their original records remain represented without interpreting their causes.

The one permitted full execution receipt is `runs/R23/execution/receipts/r23-consumer-30-compute-v2-final.txt`: 7,668 bytes, SHA-256 `07bd5f8517a053050fc5f1f315d0dcc9b7f04b5f225fd7273b500b8ba2c48f49`, schema `forge-command-record/1`, state `finished`, begin `2026-10-09T13:50:22.915932+00:00`, end `2026-10-09T13:50:25.154102+00:00`, exit code `0`. This records command completion only.

## Independent reproduction

The receiver froze `verifier-config.json` and `verify_slice.py` before running the calculation. The first run failed before calculation because the receiver config omitted `timezone`; its receipt and first freeze were retained as `records/11-independent-source-recomputation.json` and `freeze-v1-before-config-correction.json`. The config was corrected, re-frozen, and the same source-bound reproduction completed. No producer output was overwritten.

The completed reproduction independently fitted the two one-day point methods from R21 raw data, selected training and evaluation labels by the frozen availability times, checked the late-publication boundary, and compared every emitted prediction, revision, timestamp, and reported metric. It found 15,936 training rows, 5,376 rows in the 56-day window, 96 target keys per method, 166 later-published training rows, and 44 visible training keys with later-published reports. All 96 evaluation labels were post-origin and selected by the stated cutoff; all 96 target promotion announcements were known by origin.

Prediction maximum absolute differences were `4.9407589131078566e-11` for `shared_ridge10_consumer` and `0` for `weekly_median56_consumer`, within the frozen `1e-8` tolerance. Independently recomputed MAE/RMSE/mean signed error matched the report for both methods. The received table has 192 rows and 96 keys per method.

The actual received columns are `service_date, store_id, item_id, method_id, demand_point_units, actual_demand_units, actual_revision, actual_available_at`. It contains no interval fields or `q_units`; the suffixed method IDs also are not the final workflow registry IDs. No interval, scenario calibration, integer plan, constraints, 42-day output, sensitivity, paper, or reliability claim was checked by this slice.

## Deviations and uninspected material

- One initial identity-read command used a nonexistent `execution/v2/execution-lock.json` path; the actual lock at `runs/R23/execution-lock.json` was then checked. Its failed command record is retained.
- One tool-call serialization error occurred before a shell command was formed and started no process; it has no `record_command` child receipt.
- No author `CORRECTION-STATUS`, `READ-DOMAIN`, or `SELF-CHECK` was read. No other R23 author reports, self-checks, diagnostics, manifests, reviews, or historical argv/streams were consumed. No R22, audit, root findings, or actor summaries were read.
- Actual model, token count, and cost remain unknown and null.
