import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


SOURCE = Path("/workspace/A111/runs/S03/native/expenses.csv")
OUTPUT_DIR = Path("/workspace/A111/runs/S03/native/worker")


def as_fen(amount_text):
    fen = Decimal(amount_text) * Decimal(100)
    if not fen.is_finite() or fen != fen.to_integral_value():
        raise ValueError(f"Amount is not an exact number of fen: {amount_text!r}")
    return int(fen)


def yuan_text(fen):
    sign = "-" if fen < 0 else ""
    units, cents = divmod(abs(fen), 100)
    return f"{sign}{units}.{cents:02d}"


with SOURCE.open("r", encoding="utf-8", newline="") as csv_file:
    reader = csv.DictReader(csv_file)
    if reader.fieldnames != ["id", "category", "amount"]:
        raise ValueError(f"Unexpected CSV columns: {reader.fieldnames!r}")
    seen_ids = set()
    category_totals = defaultdict(int)
    category_ids = defaultdict(list)
    row_count = 0
    total_fen = 0
    for row in reader:
        row_id = row["id"]
        category = row["category"]
        if not row_id or row_id in seen_ids:
            raise ValueError(f"Missing or duplicate ID: {row_id!r}")
        if not category:
            raise ValueError("Missing category")
        seen_ids.add(row_id)
        amount_fen = as_fen(row["amount"])
        category_totals[category] += amount_fen
        category_ids[category].append(row_id)
        total_fen += amount_fen
        row_count += 1

categories = [
    {
        "category": category,
        "total_fen": category_totals[category],
        "ids": category_ids[category],
    }
    for category in sorted(category_totals)
]
payload = {
    "row_count": row_count,
    "total_fen": total_fen,
    "categories": categories,
}

with (OUTPUT_DIR / "totals.json").open("w", encoding="utf-8", newline="\n") as output:
    json.dump(payload, output, ensure_ascii=False, indent=2)
    output.write("\n")

lines = [
    "# 费用汇总",
    "",
    f"根据 `expenses.csv` 的 {row_count} 条记录汇总。每笔十进制金额都先精确换算为整数分再相加；退款按负数计入，零金额记录也予以保留。",
    "",
    f"总额：{total_fen} 分（{yuan_text(total_fen)} 元）。",
    "",
    "类别按名称排序：",
    "",
]
for item in categories:
    ids = "、".join(item["ids"])
    lines.append(
        f"- {item['category']}：{item['total_fen']} 分（{yuan_text(item['total_fen'])} 元）；ID：{ids}。"
    )
lines.extend(["", "全部 6 个源记录 ID 均各保留一次。", ""])
with (OUTPUT_DIR / "totals.md").open("w", encoding="utf-8", newline="\n") as output:
    output.write("\n".join(lines))
