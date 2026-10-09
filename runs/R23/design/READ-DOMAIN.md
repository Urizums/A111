# Read domain and source boundary

This is the designer's read log for this bounded workflow probe. The read boundary is a collaboration contract, not OS-enforced isolation.

## Authorized material read

- `AGENTS.md` for repository continuation and command-recording rules.
- `runs/R23/brief/TASK.md` and `runs/R23/brief/INPUTS.json`.
- The nine C13 Forge files under `runs/R20/final/candidate/C13/forge-agent-flow/`, plus `runs/R20/final/candidate/C13-lock.json`.
- R21 raw CSV/JSON files and reference `BASELINE.md`, `experiment.json`, and `run.py`.
- `runs/R21/input-lock.json` metadata only. Its REQUEST and PROBLEM file contents were not opened.
- `scripts/record_command.py` was invoked as directed; its source was not read.

The raw input lock identities were used to identify source bytes; the probe summary includes raw input hashes. C13 lock is an exact-byte identity claim, not acceptance of this workflow. The baseline reference is a migration specification; its previous selection/output claims were not adopted.

## Excluded material

No R21 REQUEST/PROBLEM content; no prior execution, research plan, paper, result, review, evaluation, generator, private future data, or other actor summary; no R22 protocol/audit/results/papers/reviews; and no R23 plan, acceptance, source-lock, or audit content was read. No external search or personal skill installation was used.

## Evidence receipts

All shell commands in this work were routed through `scripts/record_command.py`. Each command attempt has a unique file under `runs/R23/design/receipts/`; initial read, failed command constructions, a failed first self-check, and successful recoveries are retained. The first probe source/output is retained as `versions/probe-v1.py` and `probe-output/`; the current lineage-emitting version and output are `probe.py` and `probe-output-v2/`.
