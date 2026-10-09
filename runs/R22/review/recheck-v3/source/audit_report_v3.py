"""Independently audit every report table against locked CSV text."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
REPORT_ROOT = ROOT / "runs/R22/execution/correction-v3/report"
SCI = ROOT / "runs/R22/execution/science-v1"
INITIAL = ROOT / "runs/R22/review/initial/rebuild-v5"
OUT = ROOT / "runs/R22/review/recheck-v3"
D0 = Decimal(0)


def csvrows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def dec(value: str | int) -> Decimal:
    return Decimal(str(value))


def fmt(value: str | int | Decimal, places: int = 3) -> str:
    return format(dec(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), f".{places}f")


def pct(value: str, places: int = 2) -> str:
    return fmt(dec(value) * 100, places)


def readcsv(name: str) -> list[dict[str, str]]:
    return csvrows(SCI / "results" / name)


def origin_date(origin: str) -> str:
    return origin[:10]


def method_short(method: str) -> str:
    return "R" if method == "shared_ridge10" else "W"


def route(origin: str, method: str) -> str:
    return origin[5:10] + "/" + method_short(method)


def table_blocks(md: str) -> list[dict[str, object]]:
    lines = md.splitlines()
    found: list[dict[str, object]] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|---"):
            cap_i = i - 1
            while cap_i >= 0 and not lines[cap_i].strip():
                cap_i -= 1
            caption = lines[cap_i].strip() if cap_i >= 0 else ""
            header = [x.strip() for x in lines[i].strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([x.strip().replace("<br>", "\n").replace("<br/>", "\n") for x in lines[j].strip("|").split("|")])
                j += 1
            found.append({"caption": caption, "header": header, "rows": rows})
            i = j
        else:
            i += 1
    return found


def build_expected() -> list[tuple[str, list[str], list[list[str]]]]:
    origins = csvrows(INITIAL / "results/origins.csv")
    overall = readcsv("group_overall.csv")
    stages = readcsv("group_stage.csv")
    activity = readcsv("group_activity.csv")
    activity_band = readcsv("group_activity_band.csv")
    activity_stage = readcsv("group_activity_stage.csv")
    stores = readcsv("group_store.csv")
    items = readcsv("group_item.csv")
    combined = readcsv("combined_first_two.csv")
    solver = readcsv("solver_daily.csv")

    exp: list[tuple[str, list[str], list[list[str]]]] = []
    exp.append(("table1", ["原点18时", "训练日期数/键数", "训练最大服务日", "固定目标范围", "活动日"], [
        [origin_date(r["origin"]), f"{r['train_days']}/{r['train_rows']}", r["latest_train_service_date"], f"{r['first_target']} 至 {r['last_target']}", r["activity_days"]]
        for r in origins
    ]))
    exp.append(("table2", ["窗/路线", "MAE", "RMSE", "偏差", "覆盖%", "宽度", "区间评分"], [
        [route(r["origin"], r["method_id"]), fmt(r["mae"]), fmt(r["rmse"]), fmt(r["bias"]), pct(r["coverage"]), fmt(r["width"]), fmt(r["interval_score"])] for r in overall
    ]))
    exp.append(("table3", ["窗/路线", "下漏%", "上漏%", "缺货", "报废", "总损失", "采购", "备货"], [
        [route(r["origin"], r["method_id"]), pct(r["below"]), pct(r["above"]), fmt(r["shortage_per_day"], 2), fmt(r["waste_per_day"], 2), fmt(r["loss_per_day"], 2), fmt(r["procurement_per_day"], 2), fmt(r["q_per_day"], 2)] for r in overall
    ]))
    exp.append(("table4", ["窗/路线", "阶段", "日期/键数", "MAE", "偏差", "覆盖%", "日损失"], [
        [route(r["origin"], r["method_id"]), r["stage"], f"{r['days']}/{r['rows']}", fmt(r["mae"]), fmt(r["bias"]), pct(r["coverage"]), fmt(r["loss_per_day"], 2)] for r in stages
    ]))
    exp.append(("table5", ["窗/路线", "日类", "日期", "MAE", "覆盖%", "区间评分", "日损失"], [
        [route(r["origin"], r["method_id"]), "活动" if r["holiday"] == "1" else "普通", r["days"], fmt(r["mae"]), pct(r["coverage"]), fmt(r["interval_score"]), fmt(r["loss_per_day"], 2)] for r in activity
    ]))
    bands_by_key = {(r["origin"], r["holiday"], r["band"]): r for r in activity_band if r["method_id"] == "shared_ridge10"}
    exp.append(("table6", ["原点", "1-7", "8-14", "15-21", "22-28", "29-35", "36-42"], [
        [origin_date(o)] + [f"{bands_by_key[(o, '1', str(b))]['days']}日/{bands_by_key[(o, '1', str(b))]['rows']}键" + ("\n不可估计" if bands_by_key[(o, '1', str(b))]['rows'] == "0" else "") for b in range(1, 7)]
        for o in [r["origin"] for r in origins]
    ]))
    exp.append(("table7", ["路线", "日期/键", "MAE", "RMSE", "覆盖%", "区间评分", "日损失"], [
        [method_short(r["method_id"]), f"{r['days']}/{r['rows']}", fmt(r["mae"]), fmt(r["rmse"]), pct(r["coverage"]), fmt(r["interval_score"]), fmt(r["loss_per_day"], 2)] for r in combined
    ]))
    solver_by_route: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in solver:
        solver_by_route[(r["origin"], r["method_id"])].append(r)
    rows8 = []
    for o in [r["origin"] for r in origins]:
        for m in ["shared_ridge10", "weekly_mean56"]:
            rr = solver_by_route[(o, m)]
            rows8.append([route(o, m), str(min(int(r["capacity_slack"]) for r in rr)), str(max(int(r["capacity_slack"]) for r in rr)), fmt(min(dec(r["budget_slack"]) for r in rr), 2), fmt(max(dec(r["budget_slack"]) for r in rr), 2), str(sum(int(r["capacity_slack"]) == 0 for r in rr))])
    exp.append(("table8", ["窗/路线", "最小容量松弛", "最大容量松弛", "最小预算松弛", "最大预算松弛", "容量绑定日"], rows8))
    for label, dimension, data in [("store", "store_id", stores), ("item", "item_id", items)]:
        for o in [r["origin"] for r in origins]:
            sub = [r for r in data if r["origin"] == o]
            by_group = {r[dimension]: r for r in sub}
            route_groups = defaultdict(dict)
            for r in sub:
                route_groups[r[dimension]][r["method_id"]] = r
            body = []
            for group in sorted(by_group):
                r = route_groups[group]["shared_ridge10"]
                w = route_groups[group]["weekly_mean56"]
                diff = dec(w["loss_per_day"]) - dec(r["loss_per_day"])
                body.append([origin_date(o), group, fmt(r["loss_per_day"], 2), fmt(w["loss_per_day"], 2), fmt(diff, 2)])
            exp.append((f"{label}-{origin_date(o)}", ["原点", "门店" if label == "store" else "商品", "R日损失", "W日损失", "W减R"], body))
    exp.append(("tableC", ["窗/路线", "阶段", "活动日/键", "MAE", "覆盖%", "日损失"], [
        [route(r["origin"], r["method_id"]), r["stage"], f"{r['days']}/{r['rows']}", "不可估计" if r["rows"] == "0" else fmt(r["mae"]), "不可估计" if r["rows"] == "0" else pct(r["coverage"]), "不可估计" if r["rows"] == "0" else fmt(r["loss_per_day"], 2)]
        for r in activity_stage if r["holiday"] == "1"
    ]))
    return exp


def financial_reconstruction() -> dict[str, object]:
    costs = {r["item_id"]: r for r in csvrows(ROOT / "runs/R21/inputs/raw/items.csv")}
    keys = readcsv("keys.csv")
    errors: list[str] = []
    by_origin_method: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    by_store: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    by_item: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    by_origin_method_day: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for n, r in enumerate(keys, 1):
        c = costs[r["item_id"]]
        q, y = dec(r["q_units"]), dec(r["actual"])
        expected = {
            "shortage_yuan": dec(c["shortage_yuan"]) * max(y - q, D0),
            "waste_yuan": dec(c["waste_yuan"]) * max(q - y, D0),
            "procurement_yuan": dec(c["procurement_yuan"]) * q,
        }
        for field, value in expected.items():
            if dec(r[field]) != value:
                errors.append(f"key row {n} {field}: CSV={r[field]} raw-cost-recomputed={value}")
            by_origin_method[(r["origin"], r["method_id"])][field] += value
            by_store[(r["origin"], r["method_id"], r["store_id"])][field] += value
            by_item[(r["origin"], r["method_id"], r["item_id"])][field] += value
            by_origin_method_day[(r["origin"], r["method_id"], r["service_date"])][field] += value
    summary_checks = []
    for name, rows, keyspec, totals in [
        ("group_overall.csv", readcsv("group_overall.csv"), ("origin", "method_id"), by_origin_method),
        ("group_store.csv", readcsv("group_store.csv"), ("origin", "method_id", "store_id"), by_store),
        ("group_item.csv", readcsv("group_item.csv"), ("origin", "method_id", "item_id"), by_item),
    ]:
        for row in rows:
            key = tuple(row[k] for k in keyspec)
            value = totals[key]
            for field, source_field in [("shortage_per_day", "shortage_yuan"), ("waste_per_day", "waste_yuan"), ("procurement_per_day", "procurement_yuan")]:
                expected = value[source_field] / Decimal(42)
                observed = dec(row[field])
                if abs(expected - observed) > Decimal("0.00000002"):
                    errors.append(f"{name} {key} {field}: {observed} != {expected}")
                summary_checks.append({"file": name, "group": key, "field": field, "csv_decimal": row[field], "raw_items_cost_recomputed": str(expected), "matches_1e-8": abs(expected-observed) <= Decimal("0.00000002")})
    return {
        "key_rows": len(keys),
        "raw_items_cost_recomputed_fields": ["shortage_yuan", "waste_yuan", "procurement_yuan"],
        "per_key_exact_mismatches": len([e for e in errors if e.startswith("key row")]),
        "group_daily_amount_checks": len(summary_checks),
        "group_daily_amount_mismatches": len([e for e in errors if not e.startswith("key row")]),
        "mismatch_examples": errors[:20],
        "summary_checks": summary_checks,
        "daily_independent_recompute_groups": len(by_origin_method_day),
    }


def main() -> None:
    bindings = json.loads((REPORT_ROOT / "document-data-bindings.json").read_text(encoding="utf-8"))
    binding_results = []
    for entry in bindings["critical_tables"]:
        path = ROOT / Path(entry["path"])
        binding_results.append({"path": entry["path"], "size": path.stat().st_size, "sha256_matches_binding": hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]})
    md = (REPORT_ROOT / "REPORT.md").read_text(encoding="utf-8")
    actual = table_blocks(md)
    expected = build_expected()
    table_checks = []
    for ix, (table_name, headers, body) in enumerate(expected):
        got = actual[ix] if ix < len(actual) else None
        normalized_rows = [[cell.strip() for cell in row] for row in body]
        matches = bool(got and got["header"] == headers and got["rows"] == normalized_rows)
        table_checks.append({"table": table_name, "caption": got["caption"] if got else None, "expected_rows": len(body), "actual_rows": len(got["rows"]) if got else 0, "headers_match": bool(got and got["header"] == headers), "all_cells_match_locked_csv_decimal_format": matches,
                            "mismatches": [] if matches else [{"expected_header": headers, "actual_header": got["header"] if got else None, "expected_row": e, "actual_row": a} for e, a in zip(body, got["rows"] if got else []) if e != a][:20]})
    financial = financial_reconstruction()
    result = {
        "schema": "r22-v3-report-independent-data-audit/1",
        "v3_source_and_report_paths": ["runs/R22/execution/correction-v3/source/build_report_v3.py", "runs/R22/execution/correction-v3/report/REPORT.md", "runs/R22/execution/correction-v3/report/REPORT.pdf", "runs/R22/execution/correction-v3/report/document-data-bindings.json", "runs/R22/execution/correction-v3/report/figures/"],
        "data_binding_csv_count": len(binding_results),
        "data_binding_hash_failures": [x for x in binding_results if not x["sha256_matches_binding"]],
        "markdown_table_count": len(actual),
        "expected_table_count": len(expected),
        "table_checks": table_checks,
        "table_mismatches": [x for x in table_checks if not x["all_cells_match_locked_csv_decimal_format"]],
        "financial_reconstruction": financial,
        "rounding": "Decimal text quantized ROUND_HALF_UP; table cells compared exactly; row-level money recomputed from key CSV actual/q and original raw items.csv unit costs.",
        "actual_model": None,
        "tokens": None,
        "cost": None,
    }
    out = OUT / "numeric-ledger.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"ledger": str(out), "table_count": len(actual), "expected_tables": len(expected), "table_mismatches": len(result["table_mismatches"]), "key_rows": financial["key_rows"], "amount_mismatches": financial["per_key_exact_mismatches"] + financial["group_daily_amount_mismatches"], "binding_hash_failures": len(result["data_binding_hash_failures"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
