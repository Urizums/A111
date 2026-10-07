# Second controller review addendum

This is an **informed re-review**, not a blind independent trial. I was told which source changes to expect and rechecked only the two open defects from `addendum.md`, their affected progress/legacy behaviors, and the already identified policy-freezing behavior. The original review and both earlier `delivery.d1_not_met` verdicts remain unchanged as historical evidence.

## Results on the current source

The current 17-test suite passed; its command receipt is `addendum2-tests-command.json`. I also ran a fresh fixture probe, recorded in `addendum2-probe-command.json`.

- **Terminal acceptance is now frozen for both modes.** I completed one `progress_guard` task and one legacy fixed task, then weakened each acceptance assertion. `validate()` reported `changed frozen acceptance` in both cases. This closes the outstanding legacy drift finding in the exercised case.
- **Malformed deadlines now fail closed with structured validation.** Empty string, integer, `false`, empty list, and empty object values each produced `invalid timezone-aware resource deadline`; each task was excluded from ready work. The earlier case where an empty value silently removed the deadline and an integer raised `AttributeError` is repaired in this source version.
- **Policy freezing and mutable path state work together.** Changing a frozen deadline term after `begin()` made `finish()` raise `Changed frozen execution policy`. Changing only `progress_state` to `stalled` left `validate()` clean and caused `finish()` to retain the attempt as `blocked`.
- **Legacy fixed behavior remains intact.** A task without progress policy and with `repair_limit=1` retained the initial attempt plus one repair, then blocked at `repairs_used=1` with no ready task. The progress guard remains opt-in.

## Current conclusion and limits

Both defects left open by the prior addendum appear repaired in current source, and no new required defect was found in this narrow recheck. This does not erase the historical failures or establish that all of delivery.d1 passes: historical R17 bytes, counters, and independent byte/history checks remain unknown because they were outside the allowed read scope. The probes use local synthetic state and record_command receipts; they do not establish provider-side resource enforcement, hard process isolation, semantic progress, or behavior beyond the fields and scenarios exercised.
