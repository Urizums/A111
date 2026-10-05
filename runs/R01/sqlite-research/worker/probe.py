"""Harmless file-backed SQLite transaction/FK/idempotence probe."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path


def canonical_digest(records: list[dict[str, str]]) -> str:
    encoded = json.dumps(
        {"schema_version": 1, "records": records},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def snapshot(con: sqlite3.Connection) -> dict[str, tuple[tuple[object, ...], ...]]:
    tables = {
        "locations": "SELECT location_id FROM locations ORDER BY location_id",
        "assets": "SELECT asset_id, location_id, label FROM assets ORDER BY asset_id",
        "imports": "SELECT batch_id, payload_sha256 FROM imports ORDER BY batch_id",
        "history": "SELECT event_id, batch_id, asset_id, note FROM history ORDER BY event_id",
    }
    return {
        name: tuple(tuple(row) for row in con.execute(sql))
        for name, sql in tables.items()
    }


def apply_batch(
    con: sqlite3.Connection,
    batch_id: str,
    records: list[dict[str, str]],
    observations: dict[str, object],
) -> str:
    digest = canonical_digest(records)
    con.execute("BEGIN IMMEDIATE")
    try:
        prior = con.execute(
            "SELECT payload_sha256 FROM imports WHERE batch_id = ?", (batch_id,)
        ).fetchone()
        if prior is not None:
            if prior[0] != digest:
                raise ValueError("batch ID already exists with different contents")
            con.execute("COMMIT")
            return "identical-retry-noop"

        con.execute(
            "INSERT INTO imports(batch_id, payload_sha256) VALUES (?, ?)",
            (batch_id, digest),
        )
        for record in records:
            con.execute(
                "INSERT INTO assets(asset_id, location_id, label) VALUES (?, ?, ?)",
                (record["asset_id"], record["location_id"], record["label"]),
            )
            con.execute(
                "INSERT INTO history(event_id, batch_id, asset_id, note) VALUES (?, ?, ?, ?)",
                (record["event_id"], batch_id, record["asset_id"], record["note"]),
            )
        con.execute("COMMIT")
        return "committed"
    except BaseException:
        observations["transaction_active_at_failure"] = con.in_transaction
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise


def main() -> None:
    observations: dict[str, object] = {}
    print(f"python={sys.version.split()[0]}")
    print(f"sqlite_runtime={sqlite3.sqlite_version}")

    with tempfile.TemporaryDirectory(prefix="sqlite-probe-", dir=Path(__file__).parent) as temp_dir:
        db_path = Path(temp_dir) / "probe.sqlite"
        con = sqlite3.connect(db_path, isolation_level=None)
        con.execute("PRAGMA foreign_keys = ON")
        fk_enabled = con.execute("PRAGMA foreign_keys").fetchone()[0]
        print(f"foreign_keys_after_enable={fk_enabled}")
        if fk_enabled != 1:
            raise RuntimeError("foreign-key enforcement did not enable")

        con.execute(
            "CREATE TABLE locations(location_id TEXT PRIMARY KEY)"
        )
        con.execute(
            "CREATE TABLE imports(batch_id TEXT PRIMARY KEY, payload_sha256 TEXT NOT NULL)"
        )
        con.execute(
            "CREATE TABLE assets("
            "asset_id TEXT PRIMARY KEY, location_id TEXT NOT NULL REFERENCES locations(location_id), "
            "label TEXT NOT NULL)"
        )
        con.execute(
            "CREATE TABLE history("
            "event_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES imports(batch_id), "
            "asset_id TEXT NOT NULL REFERENCES assets(asset_id), note TEXT NOT NULL)"
        )
        con.execute("INSERT INTO locations(location_id) VALUES ('L-1')")
        con.execute("INSERT INTO imports(batch_id, payload_sha256) VALUES ('seed', 'seed')")
        con.execute(
            "INSERT INTO assets(asset_id, location_id, label) VALUES ('A-existing', 'L-1', 'Existing')"
        )
        con.execute(
            "INSERT INTO history(event_id, batch_id, asset_id, note) "
            "VALUES ('E-existing', 'seed', 'A-existing', 'seeded')"
        )
        baseline = snapshot(con)

        conflicting_records = [
            {
                "asset_id": "A-new-first",
                "location_id": "L-1",
                "label": "Would be rolled back",
                "event_id": "E-new-first",
                "note": "first row",
            },
            {
                "asset_id": "A-existing",
                "location_id": "L-1",
                "label": "Conflicting replacement",
                "event_id": "E-conflict",
                "note": "later row",
            },
        ]
        try:
            apply_batch(con, "B-conflict", conflicting_records, observations)
        except sqlite3.IntegrityError as exc:
            after_conflict = snapshot(con)
            if after_conflict != baseline:
                raise AssertionError("failed import changed the baseline database") from exc
            if observations.get("transaction_active_at_failure") is not True:
                raise AssertionError("expected row failure to occur in an active transaction") from exc
            print(
                "later_conflict="
                f"{type(exc).__name__}; transaction_active_at_failure=True; "
                "explicit_rollback=True; baseline_unchanged=True; "
                f"counts={{{', '.join(f'{key}:{len(value)}' for key, value in baseline.items())}}}"
            )
        else:
            raise AssertionError("later unique-key conflict was not rejected")

        bad_fk_records = [
            {
                "asset_id": "A-orphan",
                "location_id": "L-missing",
                "label": "Orphan",
                "event_id": "E-orphan",
                "note": "must fail",
            }
        ]
        try:
            apply_batch(con, "B-bad-fk", bad_fk_records, observations)
        except sqlite3.IntegrityError as exc:
            if snapshot(con) != baseline:
                raise AssertionError("foreign-key failure changed the baseline database") from exc
            print(
                f"foreign_key_violation={type(exc).__name__}; "
                "missing_location_rejected=True; rollback_restored_baseline=True"
            )
        else:
            raise AssertionError("orphan asset was not rejected")

        accepted_records = [
            {
                "asset_id": "A-new",
                "location_id": "L-1",
                "label": "New asset",
                "event_id": "E-new",
                "note": "received",
            }
        ]
        first_result = apply_batch(con, "B-accepted", accepted_records, observations)
        after_first = snapshot(con)
        retry_result = apply_batch(con, "B-accepted", accepted_records, observations)
        after_retry = snapshot(con)
        if first_result != "committed" or retry_result != "identical-retry-noop":
            raise AssertionError("unexpected batch/retry result")
        if after_first != after_retry:
            raise AssertionError("identical retry added or changed rows")
        if len(after_first["assets"]) != len(baseline["assets"]) + 1:
            raise AssertionError("accepted batch did not add exactly one asset")
        if len(after_first["history"]) != len(baseline["history"]) + 1:
            raise AssertionError("accepted batch did not add exactly one history row")
        print(
            "identical_retry="
            "first=committed; retry=identical-retry-noop; "
            "asset_count_stable=True; history_count_stable=True"
        )

        con.close()
        reopened = sqlite3.connect(db_path, isolation_level=None)
        reopened.execute("PRAGMA foreign_keys = ON")
        reopened_fk = reopened.execute("PRAGMA foreign_keys").fetchone()[0]
        persisted = snapshot(reopened)
        if reopened_fk != 1 or persisted != after_first:
            raise AssertionError("committed file-backed state did not survive reopen")
        print(
            "close_reopen="
            f"foreign_keys={reopened_fk}; committed_state_persisted=True; "
            f"assets={len(persisted['assets'])}; history={len(persisted['history'])}"
        )
        reopened.close()

    print("probe_status=PASS")


if __name__ == "__main__":
    main()
