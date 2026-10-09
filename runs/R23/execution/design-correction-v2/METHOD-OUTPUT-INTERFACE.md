# Per-method future-output contract

This is the execution and receiving interface for future prediction/interval and replenishment tables. `runs/R23/brief/TASK.md:9` requires these tables for each method and requires `method_id` recognition.

## Frozen method set

Before candidate scoring, freeze `requested_methods` in the run manifest. It must list the current reference and every alternative actually compared, with a stable `method_id`, formula/config/code identity, and role. The recommendation is recorded separately as `recommended_method_id`. Selection can identify the preferred route for discussion; it cannot remove any entry from `requested_methods`, suppress that method's future output, or satisfy its output contract with another method's table.

The current workflow's intended set is `shared_ridge10` and `weekly_median56`. If a pre-score input defect prevents one from being defined or applied, preserve it in `requested_methods` and report it as failed/unverified; do not silently remove it, replace its ID, or reduce the method count. Any additional method actually compared must also be added to the frozen registry before scoring.

## Required future tables

The method-specific expected key set is

`K = {(d,s,i) | d = 2026-11-01..2026-12-12 inclusive, s = the 12 source store IDs, i = the 8 source item IDs}`

so `|K| = 42 × 12 × 8 = 4,032` for **each** method. Store and item IDs must come from the accepted source dimension tables; never synthesize a different ID set to make row counts match.

`future_predictions.csv` contains every method's full table with columns:

`service_date,store_id,item_id,method_id,demand_point_units,lower90_units,upper90_units,interval_level`

`future_replenishment.csv` contains every method's full table with columns:

`service_date,store_id,item_id,method_id,q_units`

For each `m ∈ requested_methods`, the receiver independently checks:

1. `predictions[m]` has exactly 4,032 rows, 4,032 unique `(service_date,store_id,item_id)` keys, and key set exactly `K`.
2. `replenishment[m]` has exactly 4,032 rows, 4,032 unique keys, and key set exactly `K`; its key set equals `predictions[m]`.
3. Every row's `method_id` equals `m`; forecast/interval values are finite and nonnegative, lower ≤ upper, `interval_level=0.9`; `q_units` is finite, integer and nonnegative.
4. For each date and method, all 96 quantities satisfy the item/store maximum of 55, network cap of 1,600, and procurement cap of 6,000 yuan. Independently recompute scenario loss and solver claims from that method's own scenarios and plan.
5. The registry names both output paths/hashes, expected and observed row/key counts, checks, and status for that method. The set of table method IDs must equal `requested_methods`, not merely contain the recommended method.

When tables are stored in separate per-method files, each file must still carry `method_id`, and the registry maps the stable ID to the path. Separate files do not relax any cardinality or check.

## Registry and failure semantics

The registry separates producer state from receiver state. Suggested fields:

```json
{
  "requested_methods": ["shared_ridge10", "weekly_median56"],
  "recommended_method_id": "<one requested method after frozen selection>",
  "methods": {
    "<method_id>": {
      "requested": true,
      "producer_status": "produced_self_checked | failed | unverified",
      "independent_status": "pending | accepted | rejected",
      "expected_rows_per_table": 4032,
      "prediction_rows": 4032,
      "replenishment_rows": 4032,
      "prediction_keys_sha256": "...",
      "replenishment_keys_sha256": "...",
      "prediction_path": "...",
      "replenishment_path": "...",
      "checks": [],
      "failure_reason": null,
      "recovery_action": null
    }
  },
  "overall_production_status": "pending | complete | incomplete"
}
```

`independent_status=accepted` is reserved for the receiver; a producer cannot assign it. A method can be marked `produced_self_checked` only after its complete tables pass the producer checks. `failed` or `unverified` must name the failed stage, observed counts/key coverage, exact evidence/receipt, and next recovery action. A partial attempt may be retained in a failure-specific path, clearly labeled partial, but must not occupy the complete table path or count toward output totals.

If any frozen method fails or is unverified, set overall production to `incomplete` (or pending while a supported recovery is active). Keep the original method in the registry. Do not emit empty placeholder tables, fabricate rows, drop the method after seeing results, transfer its `method_id` to another method, or count another candidate's output as its substitute. The comparison/recommendation can still be reported with this explicit unresolved gap, but the full TASK output is not accepted until every requested method has complete, independently checked tables.
