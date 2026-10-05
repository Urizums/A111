import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


SOURCE = Path("/workspace/A111/runs/S03/repair-1/expenses.csv")
WORKER = Path("/workspace/A111/runs/S03/repair-1/worker")


def fen_from_amount(value):
    amount = Decimal(value)
    if not amount.is_finite():
        raise ValueError(f"non-finite amount: {value!r}")
    fen = amount * 100
    if fen != fen.to_integral_value():
        raise ValueError(f"amount has fractions smaller than one fen: {value!r}")
    return int(fen)


def yuan_from_fen(value):
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    return f"{sign}{absolute // 100}.{absolute % 100:02d}"


with SOURCE.open("r", encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle)
    if reader.fieldnames != ["id", "category", "amount"]:
        raise ValueError(f"unexpected CSV columns: {reader.fieldnames!r}")
    rows = list(reader)

ids = [row["id"] for row in rows]
if len(set(ids)) != len(ids):
    raise ValueError("duplicate ID in source")

totals = defaultdict(int)
category_ids = defaultdict(list)
total_fen = 0
for row in rows:
    amount_fen = fen_from_amount(row["amount"])
    category = row["category"]
    totals[category] += amount_fen
    category_ids[category].append(row["id"])
    total_fen += amount_fen

categories = [
    {
        "category": category,
        "total_fen": totals[category],
        "ids": category_ids[category],
    }
    for category in sorted(totals)
]
result = {
    "row_count": len(rows),
    "total_fen": total_fen,
    "categories": categories,
}
(WORKER / "totals.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

lines = [
    "# 费用汇总",
    "",
    f"源文件共有 {len(rows)} 条记录。以下类别按名称排序，金额均按原始小数精确换算为人民币分：",
    "",
]
for item in categories:
    lines.append(
        f"- {item['category']}：{yuan_from_fen(item['total_fen'])} 元（{item['total_fen']} 分）；"
        f"包含 {len(item['ids'])} 条记录，ID：{', '.join(item['ids'])}。"
    )
lines.extend(
    [
        "",
        f"合计 {yuan_from_fen(total_fen)} 元（{total_fen} 分），共 {len(rows)} 条记录。",
        "交通类的退款 -2.10 元（-210 分）已抵减该类金额；办公类的 0.00 元记录仍计入记录数并保留其 ID。",
        "",
    ]
)
(WORKER / "totals.md").write_text("\n".join(lines), encoding="utf-8")
