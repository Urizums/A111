# Independent acceptor preparation

## Frozen source boundary

The case raw inputs and acceptance note were read from `runs/R20/forward-case/`, and the case input/evaluation locks were read. The workflow source is `runs/R20/final/candidate/C13/forge-agent-flow/`, with exact source lock at `runs/R20/final/candidate/C13-lock.json`. No production file contents were opened.

## Executable raw reconstruction

`reconstruct_raw.py` verifies every input-lock byte count and SHA-256, distinguishes exact retransmission from new records, rejects forecast candidates unavailable by their declared forecast origin, reconstructs labels available at each decision origin, requires the complete series vector, and recomputes residuals with decimal arithmetic. It also represents the allowed conservative fixed-evaluation-mature policy and leaves an empty pool explicit.

The script was executed once through `scripts/record_command.py`. The complete argv, cwd, timestamps, terminal state, exit code, stdout/stderr and base64 streams are retained in `commands/raw-reconstruction.json`. It finished with exit code 0 and verified the source lock. This is preparation evidence only, not acceptance of production.

## Frozen receiving assertions

`assertions.json` maps source-bound rejection conditions to f1, f2 and f3. It records five source/time assertion classes, both allowed policy choices, no imposed vector-count quota, and a source-derived pair of control designs. Control invocation details will be bound to the real frozen consumer interface before execution.

## Terminal status

PREPARED; waiting for the coordinator's actual production freeze lock. No production file contents were read, no production command or consumer control was run, and no f1–f3 verdict has been assigned. Requested Luna/high remains configuration only; actual provider/model, token use and cost remain unknown/null absent telemetry.
