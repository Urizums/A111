# Local run evidence ledger

`scripts/runledger.py` stores recovery evidence for delegated host attempts. It is
a local, single-writer JSON ledger: it never calls a provider, dispatches work,
or retries an attempt. Initialize a ledger once:

```sh
python3 scripts/runledger.py init --ledger .forge/runs.json
```

The file is created atomically and an existing ledger is never overwritten. Keep
one writer for a ledger; atomic replacement protects a single update from a
partial write, but this tool does not coordinate concurrent writers.

Each job contains an ordered chain of attempts. Give every attempt a new stable
`attempt_id`; after the first, set `--parent-attempt` to the immediately previous
attempt ID. A requested attempt records its input SHA256, model, reasoning
setting, and a local file containing the actual host receipt. For example:

```sh
python3 scripts/runledger.py record \
  --ledger .forge/runs.json --job-id review-42 --attempt-id review-42-1 \
  --status requested --input-hash "$INPUT_SHA256" \
  --model gpt-example --reasoning medium \
  --receipt /absolute/path/host-receipt.json \
  --receipt-sha256 "$RECEIPT_SHA256"
```

Append `running`, `completed`, `failed`, or `interrupted` with another `record`
command for the same attempt. Every event requires a saved local host receipt
and its SHA256. A `completed` event also requires the saved host reply and its
SHA256, supplied as `--response` and `--response-sha256`. The tool checks each
file's current bytes before recording it. Later status checks re-hash all
referenced files. Keep those files at their recorded paths for as long as the
ledger is used.

The event chain is the source of status. Events only append through legal
transitions: `requested` to `running`, `failed`, or `interrupted`; and `running`
to `completed`, `failed`, or `interrupted`. Terminal events cannot be changed or
overwritten. To try again after a terminal failure or interruption, use a new
attempt ID linked to the previous attempt so its history remains available.

Check recovery for the exact input hash before deciding what to do:

```sh
python3 scripts/runledger.py status \
  --ledger .forge/runs.json --job-id review-42 --input-hash "$INPUT_SHA256"
```

Read the JSON `action` field. `reuse` is returned only for an intact completed
attempt with the same input hash. `reconcile` means a requested or running
attempt may already have caused an external effect; inspect the host and never
redispatch automatically. `reconcile_before_retry` means a failed or interrupted
attempt may have left external side effects; check those effects with the host
or operator before starting a new attempt. The ledger cannot verify that this
external reconciliation happened. `retry_eligible` means no matching completed
attempt is available and the tool found no failed or interrupted latest attempt
that requires that warning; it is guidance, not a dispatch command. A changed
input hash never reuses a previous completion. `evidence_invalid` means a
receipt or reply is missing, unreadable, or changed; the tool will not claim
completion or retry eligibility and will refuse a new attempt until the history
is reconciled.

All timestamps are local ledger-recording times. SHA256 detects changed bytes;
it does not authenticate the provider, prove that a file came from a host, or
show that the host's output is correct. The ledger itself is also an ordinary
local file, not a tamper-proof log. Preserve the original receipt and reply
artifacts. A receipt or reply entered after the fact is a retrospective record;
its local hash does not prove that it was saved or recorded at execution time.

Invalid command input or malformed ledger data returns exit code `2` with a JSON
error on stderr. `status` is read-only, and no ledger command performs a host
call.
