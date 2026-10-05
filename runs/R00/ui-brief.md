# Independent target-browser acceptance — local support desk

Validate the original requirements in /workspace/A111/runs/R03/materials/ticket-brief.json
and /workspace/A111/runs/R03/materials/ui-brief.json. Read these first and freeze
your independent expected checks before running the app. No Root diagnoses or
expected result files are supplied. Target source is /workspace/A111/challenges/ticket-desk
(app.py, index.html, app.js, style.css); you may inspect it only after freezing
requirements. Do not read sibling reports, state history or other worker output.

Launch that real Python HTTP app with --port 0 and a fresh SQLite database under
your assigned worker directory, capture the returned loopback port, and use the
installed Python Playwright plus /usr/bin/chromium. Local loopback HTTP to your
own test server is explicitly allowed; no external network, real business effects
or native delegation. Write only your assigned directory and stop your server
when finished. Do not edit product/core/skill or shared state.

Exercise real browser creation, validation with draft retention, filters/search,
status progression/reopen/history and a stale-version conflict using a second
HTTP client, plus loading/empty feedback. Inspect desktop and 390px narrow layout,
keyboard focus, semantic labels, overflow, key text contrast and reduced-motion
behavior. Capture screenshots and actually view them; DOM checks alone are not
visual review. Any interaction harness must call the real backend, not mock a
successful product. A controlled delayed response for loading observation must
be disclosed. Record exact browser/runtime, inputs, actual actions, findings and
limits, source hashes, raw failures and at most two harness corrections. Do not
patch the app; report actionable defects to Root with source requirement and
reproduction. Tokens/cost/user-study outcomes unavailable => null.

Deliver report.md, results.json, screenshots, executable browser script and raw
command record(s). Keep sources and evidence immutable after your final reply.
This is target acceptance, not a full accessibility audit or production certification.
