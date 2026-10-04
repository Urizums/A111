# Independent support desk browser acceptance

This run verified real-browser ticket creation, required-field feedback, search and status filtering against the local HTTP/SQLite service. A separate post-restart API probe confirmed persistence, version conflicts, transition rules, and history. The browser workflow stopped after its first status change because the harness tried to find that ticket in the still-selected open-only filter. The server log and a read-only probe confirm the change itself succeeded. This is a harness limitation, not a confirmed product defect.

## Environment and setup

- Runtime: Python 3.12.14; installed Python Playwright; `/usr/bin/chromium` 151.0.7922.173, headless.
- The app was started with `--port 0` and a fresh database for each browser attempt. Ports were 43725, 45511, and 46559. The final database `tickets-final.sqlite3` was reused after a server restart on port 40053.
- Browser requests stayed on `127.0.0.1`; no external network or business service was used.
- Loading was observed with a disclosed 800 ms Playwright delay. The route handler fetched the actual server response first, waited, then fulfilled with that same response.
- The frozen checks are in `expected-checks.md`. Target source hashes are listed in `results.json` and remained unchanged after the run.

## Observed browser behavior

On the final browser run, the initial empty state showed zero counts and a clear “no tickets” prompt. The delayed initial request exposed the loading message. The form had semantic labels for title, description, priority, and search. Submitting a draft with title `保留输入验证草稿`, urgent priority, and no description showed `请填写问题说明。已保留其他内容。`; the title and priority remained entered, focus moved to description, and description had `aria-invalid="true"`.

The browser created both supplied fixtures through real POST requests: `打印队列卡住` / `二楼共享打印机无法继续` / normal, and `会议室视频无声` / `音频输出设备丢失` / urgent. The list showed both tickets and counts of two open. Selecting the open status returned two items; searching `打印队列卡住` returned that one persisted ticket.

The browser then clicked “开始处理” for the print ticket. The server returned 200 and changed it to `in_progress`, version 2. Because the UI remained filtered to open, the ticket disappeared from the rendered list as expected. The harness incorrectly waited for the ticket to display `处理中` inside that open-only result, timed out, and ended that browser run. I did not make a third harness correction after the two allowed corrections.

I restarted the real server against the same SQLite file. The ticket remained `in_progress`, version 2. A separate urllib client with a stale expected version got HTTP 409 and did not overwrite the current row. The API then accepted `in_progress → resolved → open`, rejected `open → resolved` with HTTP 400, and returned all four history entries. This validates backend transitions, persistence, conflict handling, and history; the later transitions and history were exercised through HTTP clients, not through the browser UI.

## Visual and UI review

I opened and visually inspected the final run's 1440px loading, empty, and populated screenshots. They show a clear primary create action, readable queue counts, compact desktop ticket rows, and a clear empty prompt. The populated capture also shows a visible focus outline on the title field after the create flow moved focus there; it does not establish keyboard navigation behavior.

The final browser run did not reach its 390px layout, keyboard Tab, rendered contrast, or reduced-motion measurements. Palette contrast calculated from the inspected CSS values was 13.74:1 for body text, 5.66:1 for muted text, 4.61:1 for the placeholder, 8.38:1 for primary button text, 7.69:1 for error text, and 6.25:1 for urgent badge text. Those are source-palette calculations, not rendered-browser measurements.

The frozen worksheet mentions priority filtering as an inferred dimension. The original briefs require generic persisted-ticket filtering and specifically call out queue status counts; this UI exposes status filters and text search but no separate priority filter. I treated the exercised status/search behavior as meeting the stated filter requirement and did not report the inferred priority control as a product defect.

## Failures and harness corrections

The first browser attempt recorded five passing early checks, then timed out because it captured locators from a list that an asynchronous search replaced. I retained its JSON and screenshots. Correction 1 added explicit ticket-count waits and sampled `aria-invalid` from the invalid field. The next run hit the app's `script-src 'self'` policy because Playwright's `wait_for_function` string evaluation required `unsafe-eval`. I retained that JSON and screenshots. Correction 2 replaced that wait with Python-side locator polling.

The final run passed six early checks but then made the open-filter workflow error described above. This was after the two permitted corrections, so the browser harness was left unchanged. The first failures and all partial evidence remain in the worker directory and are indexed in `command-record.md`.

No confirmed product defect was reproduced in the exercised scope. The browser stale-conflict message, complete status/reopen/history journey in the UI, 390px overflow, keyboard navigation, and reduced-motion response remain unverified. This target acceptance run is not a full accessibility audit or production certification.

## Artifacts

- `results.json`: structured checks, runtime, hashes, outcomes, and limits.
- `browser_acceptance.py`: executable real-browser harness.
- `restart_api_probe.py` and `restart-api-probe.json`: post-restart persistence and separate-client API evidence.
- `command-record.md`: commands, results, server lifecycle, failed attempts, and corrections.
- `final-desktop-loading.png`, `final-desktop-empty.png`, `final-desktop-two-tickets.png`: screenshots opened and visually reviewed.
- `browser-evidence-attempt1.json`, `browser-evidence-correction1.json`, `browser-evidence-final.json` and matching attempt screenshots: retained partial runs and failures.
- `post-failure-probe.json`: read-only state/history snapshot after the browser status action.

Tokens, cost, model-active time, user-study usability, and provider speed gain were unavailable and are recorded as null.
