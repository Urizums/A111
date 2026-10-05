# Retest v2 command record

1. `python -m http.server 8766 --bind 127.0.0.1 --directory /workspace/A111/runs/future/versioned_preset_catalog/candidate/v2`
2. `python /workspace/A111/runs/future/versioned_preset_catalog/independent/retest-v2/browser_validate.after-correction-2.py 2>&1 | tee /workspace/A111/runs/future/versioned_preset_catalog/independent/retest-v2/logs/run-1.log`
3. Stop server session with Ctrl-C after the browser run; retain its output in `logs/server.log`.

No external network, other server, business effect, source modification, or delegation is in scope.
