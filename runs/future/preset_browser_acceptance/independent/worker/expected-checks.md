# Frozen expected checks

Frozen before target inspection, from the original brief and required journey list.

1. Load the original preset with exactly its original three sample rows visible and record their labels/statuses.
2. Filter by text and by status; verify a no-match/empty state, then clear filters and recover rows.
3. Open a row's detail view; close using its named control and Escape; verify focus returns to the opening control.
4. Run again from a selected workflow; verify one matching new run is added and the initial selected workflow is the one executed.
5. Delete a row and cancel; verify the row remains. Confirm deletion; verify only the selected row is removed.
6. Trigger refresh; verify busy/current rows feedback, cancel, retry and successful recovery. Trigger a recoverable error and retry; verify recovery.
7. Change palette and density independently; verify changing one preserves the other.
8. Toggle drawer motion and test with reduced motion enabled; verify controls and contents remain usable.
9. Exercise desktop and 390px narrow layouts with keyboard and pointer. Check horizontal overflow and that any internal scrolling retains access to all controls/content.
10. Inspect the live rendered key text contrast, semantic labels, keyboard focus visibility, and representative screenshots.
11. Record original source hashes, original sample data, exact commands, browser/viewport and interactions, screenshots opened and visually reviewed, raw errors and all attempts. Do not infer acceptance from process exit status alone.
12. Do not assert a user study, global performance result, or real business/backend behavior from this local sample.

Acceptance applies only to the assigned original ui-presets.html and ui-presets.css. Visible internal scrolling is not itself a defect. Distinguish not-run from failed and cite exact source clauses plus evidence for any actual defect.
