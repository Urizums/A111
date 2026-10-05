# Provider-neutral local adapter boundary

Request identity, caller dispatch responsibility, observed provider event, cancel intent and usage are separate. A SQLite ledger persists intent before an external caller is allowed to dispatch once. The library never calls a provider and never converts an unknown timeout into permission to repeat work. A matching provider event can reconcile an unknown state. Cancellation sets intent; only a terminal observed event establishes outcome, including success racing with cancel.

Strict JSON rejects duplicate keys and non-finite values. Local transactions enforce request/event idempotency and terminal consistency. The caller must preserve the returned request_id and provider_run_id. This solves the offline protocol boundary; credentials, actual SDK calls, provider-global limits and natural network events remain separate required live tests.
