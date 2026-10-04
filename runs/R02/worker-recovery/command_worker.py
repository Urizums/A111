#!/usr/bin/env python3
"""Stage a batch and a baseline mutation, then exit without committing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3


def canonical_hash(data):
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    source_hash = canonical_hash(data)
    connection = sqlite3.connect(args.database, isolation_level=None, timeout=5)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("BEGIN IMMEDIATE")
    existing = connection.execute(
        "SELECT label FROM assets WHERE asset_id=?", ("BASE-001",)
    ).fetchone()
    if existing is None:
        raise RuntimeError("Committed baseline is missing")
    connection.execute(
        "UPDATE assets SET label=? WHERE asset_id=?",
        ("Uncommitted mutation that must roll back", "BASE-001"),
    )
    writes = 1
    for location in data["locations"]:
        connection.execute("INSERT INTO locations VALUES (?,?)", (location["code"], location["name"]))
        writes += 1
    for asset in data["assets"]:
        connection.execute(
            "INSERT INTO assets VALUES (?,?,?,?,?)",
            tuple(asset[key] for key in ["asset_id", "label", "serial", "location", "condition"]),
        )
        writes += 1
        for event in asset["service"]:
            connection.execute(
                "INSERT INTO service_events VALUES (?,?,?,?)",
                (event["event_id"], asset["asset_id"], event["date"], event["note"]),
            )
            writes += 1
    result = dict(batch_id=data["batch_id"], source_sha256=source_hash,
                  assets=len(data["assets"]),
                  service_events=sum(len(asset["service"]) for asset in data["assets"]))
    connection.execute(
        "INSERT INTO import_batches VALUES (?,?,?)",
        (data["batch_id"], source_hash, json.dumps(result, ensure_ascii=False)),
    )
    writes += 1
    print(json.dumps(dict(state="worker_exiting", pid=os.getpid(),
                          transaction_active=connection.in_transaction,
                          uncommitted_mutations=writes, batch_id=data["batch_id"]),
                     ensure_ascii=False, sort_keys=True), flush=True)
    # os._exit skips sqlite connection cleanup and Python finalizers. The OS closes
    # the process's file handles; SQLite must roll the open transaction back.
    os._exit(73)


if __name__ == "__main__":
    main()
