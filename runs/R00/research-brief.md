# Frozen research question — transactional equipment inventory import

Original requirement: implement and actually validate a data import/migration
challenge distinct from earlier expense CSV and meeting-note tasks. Input will
be versioned JSON equipment/location records; output is a durable SQLite database.

Unknown: with the installed Python sqlite3 runtime and Python 3.10 compatibility,
what explicit transaction and foreign-key sequence keeps an existing database
unchanged when a later input row conflicts, while allowing an identical import
to be retried without duplicate assets or history?

Read the official Python 3.10 sqlite3 documentation and SQLite's current
transaction/foreign-key documentation. Use at most three primary URLs. Record
URL, version/access time, concrete supporting passage and scope. Do not collect
general agent architecture material. Compare two concrete transaction choices,
recommend one with reasons, and run a small harmless SQLite probe in your assigned
directory that demonstrates both rollback and foreign-key enforcement. Freeze
your expectations from the documentation before running the probe.

Deliver research.json, report.md (at most 100 lines), probe.py and actual command
results. Separate observed behavior from proposal; record unsupported concurrency
or provider claims as unknown. Stop researching once those two questions have
direct source and runtime evidence. Do not inspect Root's new delivery fixes,
future challenge implementations/answers, other runs, or other workers.
