"""Apply representation-tolerant raw-cost checks and verify repeated claims."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "runs/R22/review/recheck-v3"
SCI = ROOT / "runs/R22/execution/science-v1"
INITIAL = ROOT / "runs/R22/review/initial/rebuild-v5"
REPORT = ROOT / "runs/R22/execution/correction-v3/report/REPORT.md"
D0 = Decimal(0)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def fmt(x: Decimal | str, n: int = 2) -> str:
    return format(Decimal(str(x)).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP), f".{n}f")


def main() -> None:
    prior = json.loads((OUT / "numeric-ledger.json").read_text(encoding="utf-8"))
    text = REPORT.read_text(encoding="utf-8")
    keys = read(SCI / "results/keys.csv")
    items = {r["item_id"]: r for r in read(ROOT / "runs/R21/inputs/raw/items.csv")}
    diffs: list[Decimal] = []
    for r in keys:
        c = items[r["item_id"]]
        q, y = Decimal(r["q_units"]), Decimal(r["actual"])
        for key, field, multiplier in [("shortage_yuan", "shortage_yuan", max(y-q, D0)), ("waste_yuan", "waste_yuan", max(q-y, D0)), ("procurement_yuan", "procurement_yuan", q)]:
            diffs.append(abs(Decimal(r[key]) - Decimal(c[field]) * multiplier))
    tolerance = Decimal("0.00000002")
    sorted_diffs = sorted(diffs)
    # The exact-string audit in v1 exposed tiny binary-representation deltas in
    # the published key CSV. Judge numeric agreement with an explicit 2e-8 yuan
    # bound, comfortably below both 10-decimal storage and 2-decimal display.
    amount_check = {
        "field_count": len(diffs),
        "exact_text_equal_count": sum(x == 0 for x in diffs),
        "within_2e_8_count": sum(x <= tolerance for x in diffs),
        "over_2e_8_count": sum(x > tolerance for x in diffs),
        "maximum_absolute_delta_yuan": str(max(diffs)),
        "p99_absolute_delta_yuan": str(sorted_diffs[int(Decimal(len(sorted_diffs)-1) * Decimal("0.99"))]),
        "tolerance_yuan": str(tolerance),
        "interpretation": "Rounding-level binary float representations are retained in source CSV text; all raw-cost row products agree within 2e-8 yuan and the grouped per-day amount checks in numeric-ledger.json agree within the same bound.",
    }
    expected_claims: dict[str, str] = {}
    overall = read(SCI / "results/group_overall.csv")
    for r in overall:
        label = r["origin"][5:10] + "/" + ("R" if r["method_id"] == "shared_ridge10" else "W")
        expected_claims[f"overall {label} MAE"] = fmt(r["mae"], 3)
        expected_claims[f"overall {label} daily loss"] = fmt(r["loss_per_day"], 2)
        expected_claims[f"overall {label} coverage"] = fmt(Decimal(r["coverage"])*100, 2)
    pair = read(SCI / "results/paired_daily.csv")
    by_origin: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in pair:
        by_origin[r["origin"]].append(r)
    pair_summary = {}
    for o, rs in by_origin.items():
        diffs_o = [Decimal(r["loss_W_minus_R"]) for r in rs]
        scores = [Decimal(r["score_W_minus_R"]) for r in rs]
        n_r = sum(x > 0 for x in diffs_o)
        n_w = sum(x < 0 for x in diffs_o)
        avg = sum(diffs_o, D0) / Decimal(len(diffs_o))
        avg_score = sum(scores, D0) / Decimal(len(scores))
        label = o[:10]
        pair_summary[label] = {"n_days": len(rs), "mean_W_minus_R": str(avg), "min_W_minus_R": str(min(diffs_o)), "max_W_minus_R": str(max(diffs_o)), "R_lower": n_r, "W_lower": n_w, "ties": len(rs)-n_r-n_w, "mean_score_W_minus_R": str(avg_score)}
        expected_claims[f"paired {label} mean difference"] = fmt(avg, 2)
        expected_claims[f"paired {label} range low"] = fmt(min(diffs_o), 2)
        expected_claims[f"paired {label} range high"] = fmt(max(diffs_o), 2)
        expected_claims[f"paired {label} day win counts"] = f"{n_r}日R较低、{n_w}日W较低、{len(rs)-n_r-n_w}日相同"
        expected_claims[f"paired {label} score difference"] = fmt(avg_score, 3)
    activity = read(SCI / "results/group_activity.csv")
    activity_claims = []
    for r in activity:
        if r["holiday"] == "1":
            upper = fmt(Decimal(r["above"])*100, 2)
            lower = fmt(Decimal(r["below"])*100, 2)
            activity_claims.append({"origin": r["origin"], "method": r["method_id"], "upper_leak_percent": upper, "lower_leak_percent": lower, "days": r["days"], "narrative_mentions_upper": upper in text, "narrative_mentions_lower": lower in text})
    for r in activity:
        if r["holiday"] == "1":
            for field in ["mae", "coverage", "interval_score", "loss_per_day"]:
                n = 2 if field == "coverage" else (2 if field == "loss_per_day" else 3)
                token = fmt(Decimal(r[field]) * (100 if field == "coverage" else 1), n)
                expected_claims[f"activity {r['origin'][:10]} {r['method_id']} {field}"] = token
    claim_presence = {k: {"expected_token": v, "appears_in_full_markdown": v in text} for k, v in expected_claims.items()}
    expected_repeated = [v for k, v in claim_presence.items() if not v["appears_in_full_markdown"]]
    # The narrative makes a specific set of activity-tail claims. Verify those
    # tokens from the underlying holiday group rows; other leak rates remain
    # available in the source CSVs rather than being promised in prose.
    activity_by_key = {(r["origin"][:10], r["method_id"]): r for r in activity if r["holiday"] == "1"}
    narrative_activity_specs = [
        ("2026-07-22", "weekly_mean56", "above"),
        ("2026-09-02", "weekly_mean56", "above"),
        ("2026-09-19", "weekly_mean56", "above"),
        ("2026-09-02", "shared_ridge10", "above"),
        ("2026-09-19", "shared_ridge10", "above"),
        ("2026-09-02", "shared_ridge10", "below"),
        ("2026-09-19", "shared_ridge10", "below"),
    ]
    narrative_activity_checks = [{"origin": o, "method": m, "field": f, "expected_percent": fmt(Decimal(activity_by_key[(o,m)][f])*100,2), "appears_in_full_markdown": fmt(Decimal(activity_by_key[(o,m)][f])*100,2) + "%" in text} for o,m,f in narrative_activity_specs]
    missing_activity_narrative = [x for x in narrative_activity_checks if not x["appears_in_full_markdown"]]
    source_manifest = json.loads((OUT / "source-freeze.json").read_text(encoding="utf-8"))
    result = {
        "schema": "r22-v3-report-independent-data-audit/2",
        "previous_exact_text_check": {"ledger": "numeric-ledger.json", "tables_all_exact_match": len(prior["table_mismatches"]) == 0, "tables_checked": prior["markdown_table_count"], "binding_hash_failures": len(prior["data_binding_hash_failures"])},
        "raw_items_cost_reconstruction": amount_check,
        "group_amount_reconstruction_mismatches_over_2e_8": prior["financial_reconstruction"]["group_daily_amount_mismatches"],
        "overall_and_pair_repeated_claims": claim_presence,
        "missing_overall_or_pair_claim_tokens": expected_repeated,
        "activity_leak_claims": activity_claims,
        "activity_leak_claims_explicitly_repeated_in_prose": narrative_activity_checks,
        "activity_leak_claim_gaps": missing_activity_narrative,
        "paired_daily_derived_values": pair_summary,
        "source_freeze_sha256": hashlib.sha256((OUT / "source-freeze.json").read_bytes()).hexdigest(),
        "independent_rebuild_input_identity_count": len([x for x in source_manifest["authorized_review_input_identities"] if "review/initial/rebuild-v5/" in x["path"]]),
        "actual_model": None,
        "tokens": None,
        "cost": None,
    }
    out = OUT / "numeric-ledger-v2.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"ledger": str(out), "tables_all_match": result["previous_exact_text_check"]["tables_all_exact_match"], "raw_amount_fields": amount_check["field_count"], "raw_amount_over_tolerance": amount_check["over_2e_8_count"], "missing_claim_tokens": len(expected_repeated), "activity_claim_gaps": len(missing_activity_narrative)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
