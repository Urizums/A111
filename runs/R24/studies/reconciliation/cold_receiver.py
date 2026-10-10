#!/usr/bin/env python3
"""Recalculate a received reconciliation from its *packet alone*.

Independent code path, NOT an independent AI/human reviewer or security sandbox.
No imports from producer, grader, or research source packages.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

INPUTS = ("brief.md", "consumer.md", "invoices.json", "amendments.json", "payments.json")
OUTPUTS = ("ledger.csv", "suppliers.csv", "workflow.md")
REQUIRED = {*("input/" + x for x in INPUTS), *("output/" + x for x in OUTPUTS), "manifest.json", "RECEIVE.md"}
LEDGER_COLUMNS = ["invoice_id", "vendor", "total_cents", "paid_cents", "outstanding_cents"]
SUPPLIER_COLUMNS = ["vendor", "outstanding_cents"]
LIMIT = 2 * 1024 * 1024
# Canonical receiver instruction for this versioned study packet, not a global Skill rule.
RECEIVE_SHA256 = "e70cc726689d9155dd6b9a27f4519e523ca554c29baa65764b0966da4eb31cc4"


def unique_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key: " + key)
        value[key] = item
    return value


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)


def as_utc(timestamp: str) -> datetime:
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("expected UTC timestamp ending Z")
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if dt.tzinfo != timezone.utc:
        raise ValueError("timestamp is not UTC")
    return dt


def read_csv(path: Path, expected_columns: list[str], key: str, amount_fields: set[str]) -> dict[str, dict]:
    items = {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = csv.DictReader(file)
        if rows.fieldnames != expected_columns:
            raise ValueError(f"{path.name}: wrong column contract")
        for row in rows:
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"{path.name}: ragged CSV row")
            if row[key] in items:
                raise ValueError(f"{path.name}: duplicate {key}={row[key]}")
            for amount in amount_fields:
                value = row[amount]
                if not re.fullmatch(r"[+-]?[0-9]+", value):
                    raise ValueError(f"{path.name}: noninteger {amount}={value}")
                row[amount] = int(value)
            items[row[key]] = row
    return items


def packet_integrity(folder: Path) -> tuple[dict, dict]:
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("not an ordinary packet directory")
    actual = set()
    for p in folder.rglob("*"):
        relative = p.relative_to(folder).as_posix()
        if p.is_symlink():
            raise ValueError("packet contains symlink " + relative)
        if p.is_file():
            actual.add(relative)
    if actual != REQUIRED:
        raise ValueError(f"packet files differ: missing={sorted(REQUIRED - actual)}, unexpected={sorted(actual - REQUIRED)}")
    if hashlib.sha256((folder / "RECEIVE.md").read_bytes()).hexdigest() != RECEIVE_SHA256:
        raise ValueError("receiver instructions changed from study packet version")
    manifest = read_json(folder / "manifest.json")
    if manifest.get("schema") != "forge-r24-receiver-packet/1":
        raise ValueError("wrong packet schema")
    if manifest.get("status") != "ready_for_a_separate_receiver_not_yet_accepted":
        raise ValueError("packet falsely claims acceptance")
    expected_files = REQUIRED - {"manifest.json", "RECEIVE.md"}
    if set(manifest.get("files", {})) != expected_files:
        raise ValueError("packet manifest coverage invalid")
    for name in expected_files:
        path = folder / name
        if path.stat().st_size > LIMIT:
            raise ValueError("oversized input: " + name)
        content = path.read_bytes()
        mark = manifest["files"][name]
        if len(content) != mark.get("bytes") or hashlib.sha256(content).hexdigest() != mark.get("sha256"):
            raise ValueError("packet file hash invalid: " + name)
    return manifest, {k: v["sha256"] for k, v in manifest["files"].items()}


def recalculate(packet: Path) -> dict:
    manifest, digests = packet_integrity(packet)
    brief = (packet / "input/brief.md").read_text(encoding="utf-8")
    contract = (packet / "input/consumer.md").read_text(encoding="utf-8")
    workflow = (packet / "output/workflow.md").read_text(encoding="utf-8")
    match = re.search(r"\bas of (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)", brief)
    if not match:
        raise ValueError("missing cutoff in original brief")
    cutoff = as_utc(match.group(1))
    if not all(name in contract for name in ("ledger.csv", "suppliers.csv", "posted", "approved")):
        raise ValueError("not a recognized downstream source contract")

    invoices = read_json(packet / "input/invoices.json")
    amendments = read_json(packet / "input/amendments.json")
    payments = read_json(packet / "input/payments.json")
    if not all(isinstance(rows, list) for rows in (invoices, amendments, payments)):
        raise ValueError("expected JSON arrays")
    invoice_ids = [x["invoice_id"] for x in invoices]
    if len(invoice_ids) != len(set(invoice_ids)):
        raise ValueError("duplicate invoice IDs")
    known = set(invoice_ids)
    if any(r["invoice_id"] not in known for r in amendments + payments):
        raise ValueError("orphan amendment or payment")
    expected_ledger, supplier_totals = {}, {}
    for inv in invoices:
        identifier = inv["invoice_id"]
        revisions = []
        for correction in amendments:
            if correction["invoice_id"] != identifier or correction["state"] != "approved":
                continue
            approved = as_utc(correction["approved_at"])
            if approved <= cutoff:
                revisions.append((approved, correction["change_id"], correction["revised_total_cents"]))
        revisions.sort()
        effective = revisions[-1][2] if revisions else inv["total_cents"]
        if isinstance(effective, bool) or not isinstance(effective, int):
            raise ValueError("noninteger invoice total")
        received = 0
        for payment in payments:
            if payment["invoice_id"] == identifier and payment["state"] == "posted":
                if as_utc(payment["posted_at"]) <= cutoff:
                    cents = payment["cents"]
                    if isinstance(cents, bool) or not isinstance(cents, int):
                        raise ValueError("noninteger payment cents")
                    received += cents
        balance = effective - received
        vendor = inv["vendor"]
        expected_ledger[identifier] = {
            "invoice_id": identifier, "vendor": vendor, "total_cents": effective,
            "paid_cents": received, "outstanding_cents": balance,
        }
        supplier_totals[vendor] = supplier_totals.get(vendor, 0) + balance
    expected_suppliers = {k: {"vendor": k, "outstanding_cents": v} for k, v in supplier_totals.items()}
    submitted_ledger = read_csv(packet / "output/ledger.csv", LEDGER_COLUMNS, "invoice_id",
                                {"total_cents", "paid_cents", "outstanding_cents"})
    submitted_suppliers = read_csv(packet / "output/suppliers.csv", SUPPLIER_COLUMNS,
                                   "vendor", {"outstanding_cents"})
    discrepancies = []
    for label, expected, submitted in (("invoice", expected_ledger, submitted_ledger),
                                       ("supplier", expected_suppliers, submitted_suppliers)):
        for missing in sorted(expected.keys() - submitted.keys()):
            discrepancies.append(f"{label}: missing {missing}")
        for extra in sorted(submitted.keys() - expected.keys()):
            discrepancies.append(f"{label}: unexpected {extra}")
        for common in sorted(expected.keys() & submitted.keys()):
            if expected[common] != submitted[common]:
                discrepancies.append(f"{label}: incorrect values for {common}")

    workflow_nonempty = bool(workflow.strip())
    return {
        "schema": "forge-r24-cold-receiver/1",
        "data_replay_passed": not discrepancies,
        "required_outputs_present": workflow_nonempty,
        "receiving_checks_passed": not discrepancies and workflow_nonempty,
        "packet_hash_check_passed": True,
        "invoice_count": len(expected_ledger),
        "supplier_count": len(expected_suppliers),
        "suppliers_with_zero_balance": [x for x, v in sorted(supplier_totals.items()) if v == 0],
        "discrepancies": discrepancies,
        "workflow_present": workflow_nonempty,
        "workflow_semantic_usability": "unverified_requires_real_new_context_consumer",
        "independent_agent_or_human_review": False,
        "business_acceptance": "unverified",
        "inherited_context_isolation": "not_established",
        "source_sha256": {key: digests[key] for key in sorted(digests) if key.startswith("input/")},
        "limits": "Separate program reads packet alone; code-path independence is not an independent Agent.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.receipt.exists():
        print("refusing to overwrite existing receiving receipt", file=sys.stderr)
        return 2
    try:
        result = recalculate(args.packet)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeError) as exc:
        result = {"schema": "forge-r24-cold-receiver/1", "data_replay_passed": False,
                  "packet_hash_check_passed": False, "errors": [f"{type(exc).__name__}: {exc}"],
                  "business_acceptance": "unverified", "independent_agent_or_human_review": False}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("receiving_checks_passed") else 2


if __name__ == "__main__":
    sys.exit(main())
