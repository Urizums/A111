# Library renewal flow

Reusable `forge-package/2`, Flow IR 1.1. The policy uses one current host agent:
renew 14 days only with no overdue days, no holds and fewer than two renewals;
otherwise prepare a staff-review result with reasons. No library is contacted.

Run the existing package with `packagectl.py start package.json --inputs INPUT
--state NEW_STATE`, then `next`, execute the returned prompt in the actual host,
and `advance --response RESPONSE`. Input fields: borrower_id/book_id strings,
days_overdue/holds/renewals_used nonnegative integers. The prompt rejects negative
counters; the controller enforces types, exact result schema and invocation ID.
No model API or deterministic replacement worker is included.

Root authored this package through the strict factory. Four frozen cases were
executed by the current Root host after reading their dispatches; a machine
checker compared exact results and exercised 12 rejected input/output/stale
responses. This is same-context correctness evidence, not an independent model
quality study. See runs/R02/flow/; the first delivery-record failure and one repair
remain in attempt-1/ and verify-repair-1.json. Factory and package bindings passed.
