# Support desk journey J1

Audience: a small team's support coordinator and requester. The repeated task is
creating a clear issue, finding it, moving it through work and checking history.
Mistakes to avoid: losing a draft, overwriting another update, confusing a filter
with an empty database, or applying a late search result to a newer selection.

Hypothesis: a compact desktop queue alongside a narrow creation form keeps both
frequent actions visible; on 390px, one column and ticket cards prevent clipped
controls. Baseline: no application existed. This run tests completion, errors,
persistence and overflow; no user-study improvement or time saving is claimed.

Original layout: 300px form / flexible list, bounded 1240px page, 42px column gap;
760px breakpoint is a local tunable hypothesis, not a device standard. Search and
status counts belong to the queue. Dense desktop rows become mobile cards with
separate action rows. Priority and state always include text. A restrained green
accent marks primary actions and selected state; neutral backgrounds keep ticket
content primary. Semantic color pairs are declared in style.css; target contrast
and actual keyboard focus require browser review.

Create: keep draft on validation/network failure, focus the first missing field,
disable only the submit button while saving, then clear confirmed successful
input and show the new ID. Updating uses the displayed version. A 409 reloads
latest server state and tells the user to confirm and retry; no silent overwrite.
List requests abort predecessors and use a generation check. Loading retains the
existing list; a newer filter cancels prior loading. Empty and recoverable-error
states have clear text. History expands inline without a modal/focus trap.

No decorative animation or artificial delay. Reduced-motion CSS preserves the
same static behavior. Native controls and semantic labels are used. The design
is original and contains no copied third-party components or assets. Skill
experience/motion guidance informed decisions; no external product journey is
claimed observed. Browser acceptance and an independent reviewer must inspect
J1's desktop/mobile hierarchy, draft retention, version conflict and behavior.
