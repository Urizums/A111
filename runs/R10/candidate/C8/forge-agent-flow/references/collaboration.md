# Roles and handoffs

Read when delegating or integrating outputs from multiple owners.

Assign the smallest separable unit that produces an independently checkable
output. Give each actor the original relevant requirements and minimum raw
material, permitted tools/effects, read/write assignment, output location, checks
and existing budget. Confirm the host actually supports the intended operation.
Do not choose a model or create a new conversation merely because a template
names one; follow the user's choices and host authorization.

The coordinator owns core workflow decisions, shared state and integration.
Workers return evidence and proposed changes to their assigned outputs. Parallel
workers should not edit the same shared artifact; serialize integration and
check affected dependencies. Instructions assigning directories are cooperative
boundaries, not proof of enforced security isolation.

A useful handoff contains:

- Task and requirement identities; inputs actually used, with source pointers.
- Produced artifact and any assumptions or unresolved conflicts.
- Checks actually performed, results and limits; failure and budget history.
- Current state and next action, including what the receiver must verify.

Check the handoff against its original acceptance and raw material before reuse.
Do not accept a worker's prose completion claim as proof that files or effects
exist. For review, distinguish mandatory requirements from optional improvements.

When independent verification is required, use a fresh context with the frozen
request, candidate and raw inputs. Withhold expected answers, author diagnoses
and prior verdicts. A same-context critique remains a self-check; report it as
such. If independent execution is unavailable, preserve that gap rather than
silently relaxing the requirement.

Retain actual task identity and return/status when creating an actor. If creation
or termination is unknown, reconcile the existing operation before a duplicate
call. Use the host's available status/cancellation facilities; do not fabricate
capabilities or assume a local workflow controls provider-wide concurrency.
Record unavailable model, token, cost or timing information as unknown/null.
