#!/usr/bin/env python3
"""Aggregate the bound expense CSV into the requested worker artifacts."""

import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path


ARTIFACTS = Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/project/A2/artifacts")
SOURCE = Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/materials/expenses.csv")
EXPECTED_SHA256 = "f1a6914eae07b97537e809c9e9fa5000acd02b391ca64484927596a19c2b3bfb"

source_bytes = SOURCE.read_bytes()
actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
if actual_sha256 != EXPECTED_SHA256:
    raise ValueError(f"bound input hash mismatch: {actual_sha256}")

with SOURCE.open("r", encoding="utf-8", newline="") as stream:
    reader = csv.DictReader(stream)
    required = {"id", "category", "amount_yuan"}
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise ValueError(f"missing required CSV columns: {reader.fieldnames}")
    rows = list(reader)

groups = {}
for row_number, row in enumerate(rows, start=2):
    source_id = row["id"]
    category = row["category"]
    if not source_id or not category or not row["amount_yuan"]:
        raise ValueError(f"incomplete CSV row {row_number}")
    amount_fen = Decimal(row["amount_yuan"]) * Decimal(100)
    if amount_fen != amount_fen.to_integral_value():
        raise ValueError(f"amount cannot be represented as whole fen on row {row_number}")
    group = groups.setdefault(category, {"row_count": 0, "total_amount_fen": 0, "source_ids": []})
    group["row_count"] += 1
    group["total_amount_fen"] += int(amount_fen)
    group["source_ids"].append(source_id)

summary = {"categories": {category: groups[category] for category in sorted(groups)}}
(ARTIFACTS / "summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

lines = [
    "# 费用分类汇总",
    "",
    "金额以 `Decimal` 读取 CSV 中的元金额，再乘以 100 转为整数分；类别按字典序排列，各类来源 ID 保持 CSV 原始行序。",
    "",
    "| 类别 | 行数 | 合计（分） | 来源 ID |",
    "| --- | ---: | ---: | --- |",
]
for category, values in summary["categories"].items():
    ids = "、".join(values["source_ids"])
    lines.append(
        f"| {category} | {values['row_count']} | {values['total_amount_fen']} | {ids} |"
    )
(ARTIFACTS / "summary_zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({"source_sha256": actual_sha256, "rows": len(rows), "categories": list(summary["categories"])}, ensure_ascii=False))
