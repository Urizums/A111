# Read domain and source notes

This file records preparation scope, not a substantive verdict.

## Read

- `AGENTS.md` (UTF-8).
- `runs/R23/brief/TASK.md`, `runs/R23/brief/INPUTS.json`, and only criteria `j1`–`j4` from `runs/R23/acceptance.json`.
- All nine Markdown files in `runs/R20/final/candidate/C13/forge-agent-flow/`; the nine file sizes and SHA-256 values matched `runs/R20/final/candidate/C13-lock.json`.
- `runs/R21/inputs/raw/**`, `runs/R21/inputs/reference/**`, and `runs/R21/input-lock.json` for identity metadata. Every raw/reference file's recorded size and SHA-256 matched the lock. Lock entries identifying `REQUEST.md` and `PROBLEM.md` were metadata only; neither content was opened.

## Task facts to use as checks, not as findings

- The neutral task fixes a 42-day horizon beginning 2026-11-01 at a 2026-10-31 18:00 Asia/Shanghai origin, 12 stores, 8 items per store, per-item daily quantity 0–55 integer, network daily capacity 1,600, and procurement budget 6,000 yuan. No carryover; shortage is lost and excess is discarded. Procurement cost constrains budget; shortage and waste are the two losses.
- It requires point forecasts, nominal 90% intervals, and integer replenishment for every future date/store/item, plus a comparison of the stated policy and a supported alternative, explanatory results, limitations, and a complete Chinese paper. Demand revisions and promotion/weather announcements have publication times. Future actual demand is unavailable. The holiday flag is a fictional business event. Sources are fictional offline material; the task disallows searching prior papers or existing solutions.
- The specified forecast and replenishment table keys are `service_date/store_id/item_id`; forecast fields are `demand_point_units/lower90_units/upper90_units/interval_level`, replenishment field is `q_units`, and outputs must identify `method_id`.
- R21 raw source headers observed: demand reports (`service_date, store_id, item_id, revision, available_at, demand_units, settlement_yuan`); promotions (`service_date, store_id, item_id, announced_at, discount_fraction`); weather (`service_date, zone_id, available_at, kind, rain_mm`); calendar, stores, items, and decision inputs are also present. Reference materials identify a current-policy migration contract, experiment configuration, and executable source. Their existence does not make that policy validated.
- The reference material explicitly distinguishes a bounded first slice from full delivery, uses availability-time checks for revised labels and known features, requires scenario/constraint/objective receiving checks, and treats full-day residual vectors as usable only when complete and ready. It warns against claiming empirical future coverage, identified cross-day dependence, proven optimality, or performance beyond the measured evidence.

## Preparation execution notes

- No workflow or consumer was executed; no output was evaluated; no acceptance conclusion was formed.
- Initial recorder invocation from the handoff parent directory and one subsequent inventory invocation from that directory failed before `record_command.py` could start because it was not the A111 working directory. Two later one-line Python extraction commands had syntax errors. These failures are retained in the transcript; corrected source reads/checks completed without repeating the same command text.
- Actual model, tokens, and cost are unknown and recorded as null. The preparation contains no model-usage telemetry source.
