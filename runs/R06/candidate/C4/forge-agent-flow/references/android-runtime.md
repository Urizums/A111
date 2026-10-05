# Android runtime preflight

Use [`scripts/android_preflight.py`](../scripts/android_preflight.py) before a
native Android smoke when a device or emulator is already reachable through
the host's ADB setup. Provide
the ADB executable, its serial, an output JSON path, and optionally a minimum
SDK level (default 26):

```bash
python3 scripts/android_preflight.py \
  --adb /path/to/platform-tools/adb \
  --serial emulator-5554 \
  --out android-preflight.json \
  --min-sdk 26
```

Exit `0` means all six reported predicates passed; exit `1` means the report is
blocked or could not be written; argparse returns `2` for invalid or missing
arguments. The JSON stores the UTC creation time, schema name/version, exact ADB
argument vectors, return codes, stdout/stderr, timeout status and limit, and
per-check `checked`, `passed`, `blocked`, and any blocking reason. Each probe has
a 15-second ceiling. A failed probe does not stop later probes. The only device
queries are `get-state`, `getprop`, `settings get`, and HOME `resolve-activity`.
The runner uses argument vectors with `shell=False` and does not issue connect,
pair, install, launch, UI, or guest-setting commands. Pass the serial for an
already available device using the host's configured ADB environment.

Readiness requires ADB state `device`, boot-completed `1`, a parseable SDK at or
above the requested minimum, provisioned and setup-complete settings both `1`,
and one explicit HOME component outside CryptKeeper/SetupWizard/FallbackHome and
the exact package `com.android.sdksetup`. Unsupported,
timed-out, nonzero, malformed, missing, or ambiguous results stay blocked; the
checker does not repair or configure the guest. Use
[`scripts/test_android_preflight.py`](../scripts/test_android_preflight.py) for
offline fixture coverage; it does not contact ADB.

`ready` means only these six gates passed. A blocked report applies only to this
preflight route; it does not erase separately collected evidence of a foreground
app launch. Preserve that evidence and scope any follow-on checks to what they
actually establish; a blocked HOME/setup route cannot be called generally ready.
Treat `ready` as a precondition for further testing, never as proof that an app
installed, launched, rendered correctly, persisted state, or reached a backend.
It does not verify a physical phone, hardware, application identity, app-specific
permissions, UI, network services, or backend behavior. Android images can vary
in command support and HOME resolution; unknown output fails closed. One
official fresh API 26 first-boot sample had boot-completed `1`, setup flags
`0/0`, and HOME `com.android.sdksetup/.DefaultActivity`; logcat showed it exited
seconds later as Launcher3 took over. A separate recovered API 26 generic x86
sample resolved `com.android.settings/.CryptKeeper` while the app was observed
in the foreground. These samples motivate checking signals independently; they
do not predict other images or devices. For an asynchronous first-boot change,
the host may wait a bounded interval and run a fresh complete preflight. Keep the
earlier JSON unchanged, and do not write setup flags to manufacture a ready result.
