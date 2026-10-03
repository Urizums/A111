import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "materials" / "expenses.csv"
SUMMARY = RUN / "artifacts" / "summary.json"
EXPLANATION = RUN / "artifacts" / "summary_zh.md"
OUT = RUN / "review" / "source-check-output.v2.json"

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result

groups = defaultdict(lambda: {"row_count": 0, "total_amount_fen": 0, "source_ids": []})
rows_seen = 0
with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
    for row in csv.DictReader(stream):
        rows_seen += 1
        category = row["category"]
        amount_scaled = Decimal(row["amount_yuan"]) * Decimal(100)
        if amount_scaled != amount_scaled.to_integral_value():
            raise ValueError("amount cannot be represented as integer fen: " + repr(row))
        group = groups[category]
        group["row_count"] += 1
        group["total_amount_fen"] += int(amount_scaled)
        group["source_ids"].append(row["id"])

expected = {category: groups[category] for category in sorted(groups)}
with SUMMARY.open(encoding="utf-8") as stream:
    actual = json.load(stream, object_pairs_hook=unique_object)
markdown = EXPLANATION.read_text(encoding="utf-8")
checks = {
    "json_shape": isinstance(actual, dict) and set(actual) == {"categories"} and isinstance(actual.get("categories"), dict)
}
actual_groups = actual.get("categories", {}) if isinstance(actual, dict) else {}
checks["category_set_exactly_once"] = isinstance(actual_groups, dict) and set(actual_groups) == set(expected)
checks["row_counts"] = checks["category_set_exactly_once"] and all(
    isinstance(actual_groups.get(category), dict)
    and type(actual_groups[category].get("row_count")) is int
    and actual_groups[category]["row_count"] == expected[category]["row_count"]
    for category in expected
)
fen_keys_by_category = {}
def fen_total(entry):
    keys = [key for key in ("total_amount_fen", "total_fen") if key in entry]
    return (keys[0] if len(keys) == 1 else None), keys
fen_checks = []
for category in expected:
    entry = actual_groups.get(category, {})
    field, fields = fen_total(entry if isinstance(entry, dict) else {})
    fen_keys_by_category[category] = fields
    fen_checks.append(
        field is not None
        and type(entry[field]) is int
        and entry[field] == expected[category]["total_amount_fen"]
    )
checks["exact_integer_fen_sums"] = checks["category_set_exactly_once"] and all(fen_checks)
checks["complete_ordered_ids"] = checks["category_set_exactly_once"] and all(
    isinstance(actual_groups.get(category), dict)
    and isinstance(actual_groups[category].get("source_ids"), list)
    and actual_groups[category]["source_ids"] == expected[category]["source_ids"]
    for category in expected
)
markdown_rows = []
for line in markdown.splitlines():
    if not line.startswith("|"):
        continue
    cells = [cell.strip() for cell in line.split("|")[1:-1]]
    if len(cells) != 4 or cells[0] not in expected:
        continue
    ids = [value.strip() for value in cells[3].replace(",", "、").replace("，", "、").split("、") if value.strip()]
    try:
        markdown_rows.append({"category": cells[0], "row_count": int(cells[1]), "total_amount_fen": int(cells[2]), "source_ids": ids})
    except ValueError:
        markdown_rows.append({"category": cells[0], "parse_error": True})
markdown_by_category = {}
for item in markdown_rows:
    if item["category"] in markdown_by_category:
        markdown_by_category[item["category"]] = None
    else:
        markdown_by_category[item["category"]] = item
checks["chinese_heading"] = "费用分类汇总" in markdown
checks["markdown_rows_agree"] = set(markdown_by_category) == set(expected) and all(
    isinstance(markdown_by_category.get(category), dict)
    and markdown_by_category[category].get("row_count") == expected[category]["row_count"]
    and markdown_by_category[category].get("total_amount_fen") == expected[category]["total_amount_fen"]
    and markdown_by_category[category].get("source_ids") == expected[category]["source_ids"]
    for category in expected
)
result = {
    "schema": "forge-expense-source-review/1",
    "sample": RUN.name,
    "source": {"path": str(SOURCE), "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "rows": rows_seen},
    "outputs": {
        "summary_json_sha256": hashlib.sha256(SUMMARY.read_bytes()).hexdigest(),
        "summary_zh_sha256": hashlib.sha256(EXPLANATION.read_bytes()).hexdigest()
    },
    "computed_from_raw_csv_with_decimal_fen": expected,
    "worker_fen_fields": fen_keys_by_category,
    "worker_summary": actual,
    "markdown_rows": markdown_rows,
    "checks": checks,
    "pass": all(checks.values())
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
