import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path


source = Path("runs/R08/validation/inputs/payments.csv")
destination = Path("runs/R08/validation/simple/results/reconciliation.json")
totals = {}
accepted = []
rejected = []
seen = set()

with source.open("r", encoding="utf-8", newline="") as stream:
    for line_number, row in enumerate(csv.DictReader(stream), start=2):
        payment_id = row.get("payment_id")
        if payment_id in seen:
            rejected.append({"line": line_number, "reason": "duplicate"})
            continue
        seen.add(payment_id)

        if row.get("status") != "settled":
            rejected.append({"line": line_number, "reason": "not_settled"})
            continue

        account = row.get("account")
        if account is None or account == "":
            rejected.append({"line": line_number, "reason": "missing_account"})
            continue

        try:
            amount = int(row.get("amount_cents"))
        except (TypeError, ValueError):
            rejected.append({"line": line_number, "reason": "invalid_amount"})
            continue

        totals[account] = totals.get(account, 0) + amount
        accepted.append(line_number)

payload = {
    "totals_cents": totals,
    "accepted_line_numbers": accepted,
    "rejected_rows": rejected,
}
destination.parent.mkdir(parents=True, exist_ok=True)
data = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
destination.write_bytes(data)
written_utc = datetime.now(timezone.utc).isoformat()
written_monotonic_ns = time.monotonic_ns()
print(
    json.dumps(
        {
            "artifact": str(destination),
            "sha256": hashlib.sha256(data).hexdigest(),
            "written_utc": written_utc,
            "written_monotonic_ns": written_monotonic_ns,
        }
    )
)
