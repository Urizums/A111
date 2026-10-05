import csv
import json
from pathlib import Path


source = Path("runs/R08/validation/inputs/payments.csv")
artifact = Path("runs/R08/validation/simple/results/reconciliation.json")
with source.open("r", encoding="utf-8", newline="") as stream:
    rows = list(csv.reader(stream))

assert rows[0] == ["payment_id", "account", "amount_cents", "status"]
expected_totals = {}
expected_accepted = []
expected_rejected = []
seen = set()
for line_number, values in enumerate(rows[1:], start=2):
    payment_id, account, amount_text, status = values
    if payment_id in seen:
        expected_rejected.append({"line": line_number, "reason": "duplicate"})
        continue
    seen.add(payment_id)
    if status != "settled":
        expected_rejected.append({"line": line_number, "reason": "not_settled"})
        continue
    if account == "":
        expected_rejected.append({"line": line_number, "reason": "missing_account"})
        continue
    try:
        amount = int(amount_text)
    except ValueError:
        expected_rejected.append({"line": line_number, "reason": "invalid_amount"})
        continue
    expected_totals[account] = expected_totals.get(account, 0) + amount
    expected_accepted.append(line_number)

actual = json.loads(artifact.read_text(encoding="utf-8"))
assert actual == {
    "totals_cents": expected_totals,
    "accepted_line_numbers": expected_accepted,
    "rejected_rows": expected_rejected,
}
assert expected_totals == {"alpha": 1050, "beta": 1000, "gamma": 900}
assert expected_accepted == [2, 3, 5, 8, 10]
print(
    f"PASS: source rows reconciled; accepted={len(expected_accepted)}, "
    f"rejected={len(expected_rejected)}, totals={expected_totals}"
)
