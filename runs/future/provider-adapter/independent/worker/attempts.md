# Harness attempts

1. Original command: `python3.12 /workspace/A111/runs/future/provider-adapter/independent/worker/validate.py`
   - Result: failed before any CLI acceptance command ran; Python reported `SyntaxError: ':' expected after dictionary key` at the `concurrent-submit-one-dispatch-only` check dictionary (line 268 in the first harness version).
   - Correction 1: added the missing `description` key to that check record. No adapter/core files changed.


3. Workspace reset command attempt: an `exec_command` containing `rm -rf .../py3.12` was rejected by the command guard before shell execution (`rm -f style commands are not permitted`). No files changed in that attempt. To preserve the first failed run and avoid deletion, the corrected acceptance run uses a separate `py3.12-acceptance/` directory; the original `py3.12/` and a retained copy in `failed-harness-run-2/` remain available.

4. Second-correction acceptance run command: `python3.12 /workspace/A111/runs/future/provider-adapter/independent/worker/validate.py`
   - Harness stdout before failure:
     ```text
     RUNTIME 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]
     EXECUTABLE /opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
     ADAPTER_SHA256 b6fb2ae7b74079017d105f072892cddab5c0c6341c5348331c6c34d8a86171cd
     CONTRACT_SHA256 625797bfcda0365b1669dc2d02e5ee4e17e902427c7a3449d22e3a437ff8036a
     ```
   - It reached the `main-altered-content-same-idempotency` CLI call, then failed while serializing the in-memory callable predicate to `commands.partial.json` (`TypeError: Object of type function is not JSON serializable`). The child output for that process was not persisted. Its request-conflict transaction did not alter the database. The partial command log and DB remain in `py3.12-acceptance/`.
   - This was fixed within correction round 2 by serializing predicate metadata as descriptive text. The final clean run uses `py3.12-acceptance-rerun/`; the earlier partial run remains untouched.

5. Final successful acceptance commands:
   - `python3.12 /workspace/A111/runs/future/provider-adapter/independent/worker/validate.py` -> 62/62 harness assertions passed; 55 CLI subprocesses recorded in `py3.12-acceptance-rerun/results.json`.
   - `python3.10 /workspace/A111/runs/future/provider-adapter/independent/worker/validate.py` -> 62/62 harness assertions passed; 55 CLI subprocesses recorded in `py3.10-acceptance-rerun/results.json`.
   - Final runtime logs retain all exact subprocess argument vectors, stdout/stderr, exit codes, and post-process SQLite states. Candidate SHA-256 remained `b6fb2ae7b74079017d105f072892cddab5c0c6341c5348331c6c34d8a86171cd`.

No parent questions were asked. Tokens, cost, provider identity, and model-active-time were unavailable and are recorded as null.
