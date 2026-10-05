# SQLite import transaction research

## Finding

Use `sqlite3.connect(path, isolation_level=None)`, then on that connection run `PRAGMA foreign_keys=ON` and verify `PRAGMA foreign_keys` returns `1` before beginning. Start one explicit `BEGIN IMMEDIATE`; apply the import ledger, locations, assets, and history inside it; `COMMIT` once on success. On any import or commit exception, issue `ROLLBACK` if a transaction remains active, then re-raise. Parse and validate JSON before acquiring the write transaction, but keep database-dependent conflict checks and all writes inside it.

This keeps earlier rows from the failed batch out of the existing database after a later row conflict. The probe observed the conflict leave the transaction active, then verified explicit rollback restored the full baseline. The probe also rejected a child row with a missing location.

## Source evidence and scope

- [Python 3.10 sqlite3](https://docs.python.org/3.10/library/sqlite3.html), official Python 3.10 docs, snapshot accessed 2026-10-04 04:43:18 UTC. In “Transaction control,” `isolation_level=None` means “no transactions are implicitly opened” and permits “own transaction handling using explicit SQL statements”; `commit()` and `rollback()` commit/roll back pending transactions. In “Connection context manager,” normal exit commits and an uncaught body exception rolls back. This documents the compatibility API; Python 3.10 was not installed here.
- [SQLite transactions](https://www.sqlite.org/lang_transaction.html), current official page snapshot accessed 2026-10-04 04:43:19 UTC; the page gives no release number. It says manual transactions persist until `COMMIT` or `ROLLBACK`; SQLite may undo one statement while leaving earlier transaction changes, and an application may issue `ROLLBACK`. `BEGIN IMMEDIATE` starts a write transaction immediately and may return `SQLITE_BUSY` if another writer is active. `DEFERRED` begins on first access and a read-to-write upgrade may return `SQLITE_BUSY`.
- [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html), current official page snapshot accessed 2026-10-04 04:43:19 UTC; the page gives no release number. “Enabling Foreign Key Support” says enforcement must be enabled per connection with `PRAGMA foreign_keys`, and changing it in a multi-statement transaction has no effect. Set and check the pragma before `BEGIN`.

The three source snapshots and SHA-256 hashes are recorded in `research.json`. The recommendation uses only these documentation claims and the local probe; no new source URL was fetched.

## Transaction choices

1. **Explicit `BEGIN IMMEDIATE` with `isolation_level=None` (recommended).** The batch boundary and rollback are visible in code, and write contention is encountered at begin instead of after partial batch work. The tradeoff is taking SQLite's single writer slot earlier; keep non-database parsing outside the transaction.
2. **`with con:` using Python's default DEFERRED transaction behavior.** An uncaught exception leaving the block rolls back, and normal exit commits. This is shorter, but the transaction opens implicitly at DML; catching a row conflict inside the block can let the block exit normally and commit prior rows. Deferred read-to-write upgrades may also fail with `SQLITE_BUSY`.

Do not use `executescript()` for batch work inside a pending transaction: Python 3.10 documents that it first commits a pending transaction.

## Retry proposal (not a documented input contract)

Require a stable batch ID and canonical payload digest. Store them under a unique import-ledger key in the same transaction as all imported rows. If the same ID and digest already committed, return success without writes; reject the same ID with a different digest. Give locations, assets, and history events stable unique source IDs. For an already-present asset or event, compare its persisted fields with the input and skip only an exact match; reject changed values. This prevents duplicate assets/history while preserving a conflict error for changed records. The JSON fields and conflict policy were not supplied, so this is a design proposal, not an implemented production schema.

## Runtime observation

`python3 probe.py` exited 0 on Python 3.12.14 / SQLite 3.53.1. It enabled and verified foreign keys, inserted one new row before a later primary-key conflict, observed `IntegrityError` with the transaction still active, rolled back, and found baseline counts unchanged (1 location, 1 asset, 1 import, 1 history). It rejected a missing location, committed one valid asset/history row, retried that exact batch with stable counts, then closed and reopened the file-backed database and found the committed rows persisted. Exact command output is in `commands.log`; the implementation is `probe.py`.

## Limits and process record

No Python 3.10 interpreter, ORM/provider, multi-process concurrency, alternate journal mode, or production workload was tested. The JSON schema and ID policy remain unspecified. The initial runtime query emitted a deprecation warning for `sqlite3.version`; the corrected measurement used `sqlite3.sqlite_version` and `sqlite3.sqlite_version_info`. A broad source search was truncated, then exact sections were read with targeted `sed`. One attempt to append the final files in a command containing `rm -rf __pycache__` was rejected before execution; the write was repeated without that cleanup and succeeded. No research source or probe attempt failed. No parent question or user clarification was needed. Unavailable measurements: tokens=null, cost=null, model-active-time=null.
