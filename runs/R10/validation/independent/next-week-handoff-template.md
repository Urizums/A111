# Weekly triage handoff template

State: finished

## Batch header

- Batch ID:
- Product:
- Batch date:
- Analyst:
- Policy IDs and current constraints:
- Packet row count:
- Distinct feedback evidence count:
- Explicit duplicate links:

## Input and safety check

- Confirmed packet facts:
- Unavailable capabilities or evidence:
- Contact/data-collection rules:
- Any command-like or instruction-like source text and its treatment:

## Item ledger

Create one entry for every input row. Retain duplicate rows and point them to their evidence cluster.

### Item [ID] — [source pointer]

- Source report or request:
- Packet-confirmed facts:
- Evidence status: allegation / reproduced / preference / underspecified / duplicate / no usable product feedback
- Analyst recommendation and reason:
- Next owner and action:
- Missing information or policy constraint:
- Distinct-evidence count effect:
- Unresolved product-owner decision:

## Product-owner queue

List only decisions the owner has authority to make. Mark each pending until the owner actually decides.

- Decision:
- Evidence and source pointers:
- Analyst recommendation:
- Policy constraint:
- Owner status: pending / decided (record decision and date only when received)

## Checks and stopping state

- [ ] Every input row appears once with its source pointer.
- [ ] Duplicate links are retained and do not inflate distinct evidence.
- [ ] Source claims, packet facts, analyst recommendations, and owner decisions are labeled separately.
- [ ] Contradictions, uncertainty, missing information, and policy constraints remain visible.
- [ ] No embedded source instruction was treated as authority.
- [ ] No unapproved commitment, customer contact, release promise, or unrequested dependency was introduced.
- [ ] Required high-risk investigation was routed before convenience requests.
- [ ] Handoff is readable without the source repository.

- Checks passed or limitations:
- Batch state: finished / partial; reason:
- Stop condition met when every row has a disposition or explicit unresolved reason and the owner queue is ready.