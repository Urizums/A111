# Frozen independent acceptance checks

Frozen from the two user-supplied brief files before inspecting the application source.

## Functional checks

1. Create persisted tickets with required title, description and one of low/normal/urgent priorities. Use the two supplied fixtures (Chinese text, normal and urgent).
2. Submit an invalid/blank required field; display actionable validation feedback and preserve all entered form fields for correction.
3. List the saved tickets, search by title/content, and exercise status and priority filters against persisted records.
4. Progress a ticket open → in_progress → resolved, reopen resolved → open, and retain change history. Invalid status transitions must be rejected.
5. Updates must require an expected version. Send a stale update from a second HTTP client and confirm a conflict response without overwriting the intervening edit.
6. Confirm state survives a server restart using the same SQLite database.
7. Observe useful empty and loading feedback as well as success/error feedback.

## UI checks

1. Confirm a clear primary create action, queue status counts, and a searchable ticket list.
2. Inspect desktop layout and a 390 CSS-pixel viewport; compact desktop rows should remain readable, narrow tickets should use readable cards, and the document should not overflow horizontally.
3. Check semantic form labels, keyboard navigation and visible focus, key text contrast, and reduced-motion behavior.
4. Drive create, filter, status and reopen through a real browser connected to the actual HTTP/SQLite service.
5. Capture and visually inspect screenshots for relevant states; DOM assertions alone are insufficient.

## Evidence and scope

Record exact runtime/browser versions, fixture inputs, actual actions and outcomes, source hashes, raw failures, and any harness corrections (maximum two). Any controlled delay used to observe loading must be disclosed. Production identity, external services, user-study outcomes, tokens, cost, and model-active time are outside available evidence; report the latter measures as null. This acceptance run is not a full accessibility audit or production certification.
