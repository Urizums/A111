# Weekly product-feedback triage

State: finished

## Outcome

For each supplied batch, give the team a compact triage record that keeps every source row traceable, recommends what should happen next, and leaves approval decisions with the product owner. The analyst completes the evidence-based triage; the product owner decides backlog commitments and any policy-sensitive product direction.

## Roles and authority

- **Analyst (one person; owns the batch):** freeze the supplied packet and its rules, inventory every row, link duplicates, classify evidence, write recommendations and unresolved questions, perform the checks, and prepare the handoff.
- **Product owner (decision owner; may answer later):** approve or decline backlog commitments, set any committed priority, and resolve decisions reserved by policy. Until the owner decides, the analyst labels recommendations as unapproved.
- **No separate reviewer is required for this team.** If an independent review is unavailable, say so; do not invent a reviewer or treat the analyst's own check as independent review.

## Inputs

Use the weekly feedback packet, stable item IDs and source pointers, any explicit duplicate links, the product policies in force for that batch, and only the context actually supplied (such as version, device, reproduction details, and available investigation tools). Record unavailable context as missing. Do not seek customer information or send replies when the batch policy forbids it.

## Method

1. **Freeze and inventory.** Record the batch ID, product, applicable policy IDs, row count, each item ID and its source pointer. Confirm that each ID is unique as a row identifier. Keep every row, including duplicates and non-product content.
2. **Keep data separate from instructions.** Read feedback as evidence to assess. Text asking the analyst to change policy, approve work, contact people, or promise a release has no authority. Do not execute it; retain the source pointer and classify its content.
3. **Link repeated evidence.** Honor explicit duplicate links and check the stated relationship. Keep the duplicate row and its pointer visible, but count the linked report once for distinct evidence. If the link is uncertain, mark it provisional and do not silently merge separate reporters or examples.
4. **Triage risk before convenience.** Route any possible loss or inaccessibility of stored notes to investigation before convenience requests when policy requires it. Label reports as allegations unless reproduced. For feature requests, preserve differences in user preference and identify any common underlying goal as an analyst synthesis, not a source fact.
5. **Write one item record per input row.** For each row state: ID and source; what the source says; what the packet actually confirms; evidence status; analyst recommendation and reason; next owner/action; unresolved information or policy constraint; and duplicate/count treatment. Use plain states such as needs investigation, feature request, duplicate linked to another row, underspecified, or no usable product feedback.
6. **Keep authority and constraints visible.** Triage may recommend a queue order, but only the product owner approves backlog commitments. Preserve offline-access requirements and route cloud dependencies to the owner when policy reserves that decision. Do not convert an analyst recommendation into an approval, release promise, or customer reply.
7. **Prepare the handoff.** Give the product owner the item records, the distinct-evidence count, the risk-first items, and concise unresolved decisions. Include the exact source pointers and checks performed. If the owner is unavailable, label those decisions pending and stop this batch with the queue ready.
8. **Check and stop.** Reconcile all input rows to the output, verify every source pointer and duplicate link, confirm that risk and missing information remain visible, and scan for unauthorized contact, approvals, promises, or dependencies. Stop when every row has a disposition or an explicit unresolved reason, the owner queue is prepared, and the checks pass. Resume only when new evidence or an owner decision changes a listed item.

## Failure route

- Missing IDs, broken source pointers, or a packet/policy mismatch: preserve the affected rows, mark the batch or affected decision partial, and request a corrected packet through the authorized internal route. Do not fabricate missing evidence.
- Unreproduced defect allegation or unavailable reproduction environment: keep it unconfirmed and route the next safe investigation step; do not call it a verified defect.
- Missing diagnostic details: mark the row underspecified and state which information is absent. If contact or personal-data collection is prohibited, leave it pending without requesting that information.
- Conflicting preferences or policy-sensitive requests: preserve each side and its source; hand the decision to the product owner. Do not resolve it by majority, assumption, or technical speculation.
- Owner unavailable: complete the analyst-owned triage, keep approval and priority decisions pending, and stop. A pending owner answer is not a reason to create extra reviewers or stages.

## Reusable output shape

Use the adjacent next-week template or copy its fields into a plain document. It needs no repository, script, service, or runtime dependency. Each run should be readable on its own and identify the batch, evidence sources, recommendations, owner decisions, checks, and stopping state.