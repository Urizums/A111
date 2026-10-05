# Task plan

Delivery: `software_system`, reduced to a one-file local Python CLI because the requested outcome is a runnable tool on the supplied fixed batch. The original goal and acceptance files are byte-copied in `inputs/`; hashes are in `inputs/manifest.json`.

Requirements: (1) Run a local equipment-allocation recommendation tool on the three supplied CSV/JSON materials and retain every request with advice, source row, priority, status, reason, and rule basis. (2) Keep rules local; no real approvals, notifications, or other business effects. (3) Obtain an independent native-agent source review. (4) Actually generate a duty-staff missing-information checklist from the run output.

Defaults: Python standard library CLI; JSON result; Markdown checklist. Incomplete rows never consume stock per source rules. The output scope repeats that it is advice only. Unknown/out-of-scope business policy remains unimplemented.

Scope/budget: only the five supplied inputs may influence results. Local file writes and one explicitly requested native reviewer are in scope. Original cutoff recorded in `history.md`; implementation repairs 0/2 at recovery start.
