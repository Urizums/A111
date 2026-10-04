# Frozen acceptance checks

Frozen before inspecting `adapter.py`, using only `contract.json` as the protocol source.

Candidate scope: `contract.json` and `adapter.py` only. No live provider, network, credentials, or external effects. Declared limits are local adapter limits, not claims of provider/global enforcement.

For each CLI interaction, use a real Python subprocess and a SQLite path inside this assigned worker directory. Capture exact command, exit status, stdout, and stderr; inspect resulting database/history after close and reopen. Retain first failures and all harness corrections (maximum two).

Checks:
1. Record Python runtime and source/contract SHA-256; discover and record exact CLI usage and declared limits from the allowed files.
2. Submit a valid request and verify its durable record exists before/at dispatch result. Repeat identical idempotency key and full request payload; verify stable request identity and no second dispatch/effect. Reuse the key with changed content; require refusal.
3. Reject malformed JSON, duplicate JSON object keys, non-finite numbers, unknown request fields, booleans as token limits, invalid/exceeded declared limits, and missing/invalid required fields. Verify no invalid request becomes dispatched.
4. Exercise event shape/status validation and event identity binding to request/provider run. Verify unknown/unbound identity or drift is rejected.
5. Apply an event twice identically and require idempotence. Reuse event identity with changed content and require refusal. Reject contradictory terminal observations.
6. Cause ambiguous dispatch/timeout; require durable `unknown` and retry/reopen without redispatch. Apply matching provider observation and verify durable reconciliation.
7. Request cancellation; require cancellation intent alone not to claim terminal cancellation. Exercise later success race and verify success settles consistently. Separately exercise explicit cancellation acknowledgement and verify cancelled terminal state.
8. Verify unavailable usage remains JSON/SQLite null, never zero or invented provider identity.
9. Close all CLI processes, reopen the same SQLite database in fresh processes, and inspect durable request/event/terminal history and idempotency outcomes.

Acceptance is local protocol evidence only. A mismatch will be tied to the exact frozen contract invariant and a captured reproduction. Unavailable tokens, cost, provider identity, and model-active-time are reported as null.
