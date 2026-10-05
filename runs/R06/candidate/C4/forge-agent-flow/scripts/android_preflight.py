#!/usr/bin/env python3
"""Bounded, read-only Android runtime checks over ADB."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_NAME = "android-runtime-preflight"
SCHEMA_VERSION = 1
COMMAND_TIMEOUT_SECONDS = 15

# Keep all guest operations in one auditable table. Each is a read-only query.
COMMANDS = (
    ("adb_state", ("get-state",)),
    ("boot_completed", ("shell", "getprop", "sys.boot_completed")),
    ("sdk_version", ("shell", "getprop", "ro.build.version.sdk")),
    ("device_provisioned", ("shell", "settings", "get", "global", "device_provisioned")),
    ("user_setup_complete", ("shell", "settings", "get", "secure", "user_setup_complete")),
    (
        "home_activity",
        (
            "shell", "cmd", "package", "resolve-activity", "--brief",
            "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME",
        ),
    ),
)
COMMAND_IDS = tuple(command_id for command_id, _ in COMMANDS)
PACKAGE_RE = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
CLASS_RE = r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*"
COMPONENT_RE = re.compile(rf"^({PACKAGE_RE})/(\.?{CLASS_RE})$")
BRIEF_META_FIELD = r"(?:priority=-?\d+|preferredOrder=-?\d+|match=0x[0-9a-fA-F]+|specificIndex=-?\d+|isDefault=(?:true|false))"
BRIEF_META_RE = re.compile(rf"^(?=.*\bpriority=-?\d+(?:\s|$)){BRIEF_META_FIELD}(?:\s+{BRIEF_META_FIELD})*$")
ADB_STARTUP_RE = re.compile(r"^(?:\* daemon not running; starting now at tcp:\d+|\* daemon started successfully)$")
NO_HOME_RE = re.compile(r"no\s+(?:activities?|activity)\s+found|unable\s+to\s+resolve|no\s+matching\s+activity", re.IGNORECASE)


def _text(value: str | bytes | None) -> str:
    return "" if value is None else value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def collect_commands(adb: str, serial: str) -> list[dict]:
    """Run every probe independently; a failure never skips later probes."""
    records = []
    for command_id, suffix in COMMANDS:
        argv = [adb, "-s", serial, *suffix]
        result = {
            "id": command_id,
            "command": argv,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "timeout_seconds": COMMAND_TIMEOUT_SECONDS,
        }
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                shell=False,
                timeout=COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            result["timeout"] = True
            result["stdout"] = _text(exc.stdout)
            result["stderr"] = _text(exc.stderr) or f"Timed out after {COMMAND_TIMEOUT_SECONDS} seconds."
        except OSError as exc:
            result["stderr"] = f"{type(exc).__name__}: {exc}"
        else:
            result.update(returncode=proc.returncode, stdout=proc.stdout or "", stderr=proc.stderr or "")
        records.append(result)
    return records


def _home_component(stdout: str, stderr: str) -> tuple[str | None, str | None, str | None]:
    if NO_HOME_RE.search(stdout + "\n" + stderr):
        return None, "home_no_activity", "Android did not resolve a HOME activity."
    if re.search(r"\b(?:error|exception)\b", stderr, re.IGNORECASE):
        return None, "home_stderr_error", "HOME command stderr contains an error or exception."
    bad_stderr = next((line.strip() for line in stderr.splitlines()
                       if line.strip() and not ADB_STARTUP_RE.fullmatch(line.strip())), None)
    if bad_stderr:
        return None, "home_unrecognized_stderr", f"Unrecognized HOME stderr line: {bad_stderr}"
    components = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        match = COMPONENT_RE.fullmatch(line)
        if match:
            components.append(f"{match.group(1)}/{match.group(2)}")
        elif not BRIEF_META_RE.fullmatch(line):
            return None, "home_unrecognized_output", f"Unrecognized HOME stdout line: {line}"
    if not components:
        return None, "home_unparseable", "HOME output has no explicit component."
    if len(components) != 1:
        return None, "home_ambiguous", "HOME output has multiple component rows."
    return components[0], None, None


def evaluate(records: list[dict], min_sdk: int) -> dict:
    """Purely assess collected records; never invokes ADB or changes the guest."""
    if isinstance(min_sdk, bool) or not isinstance(min_sdk, int) or min_sdk < 1:
        raise ValueError("min_sdk must be a positive integer")

    by_id, duplicates = {}, set()
    for record in records:
        if isinstance(record, dict) and isinstance(record.get("id"), str):
            command_id = record["id"]
            if command_id in by_id:
                duplicates.add(command_id)
            else:
                by_id[command_id] = record

    checks = []

    def block(command_id: str, code: str, reason: str, **extra) -> None:
        checks.append({
            "id": command_id,
            "checked": command_id in by_id,
            "passed": False,
            "blocked": True,
            "reason_code": code,
            "reason": reason,
            **extra,
        })

    def output(command_id: str) -> tuple[dict | None, str | None]:
        record = by_id.get(command_id)
        if command_id in duplicates:
            block(command_id, "duplicate_record", "Multiple command records make this result ambiguous.")
        elif record is None:
            block(command_id, "missing_record", "No command result was supplied.")
        elif type(record.get("timeout")) is not bool:
            block(command_id, "invalid_timeout", "Command timeout status is missing or invalid.")
        elif record["timeout"]:
            seconds = record.get("timeout_seconds", COMMAND_TIMEOUT_SECONDS)
            block(command_id, "timeout", f"ADB command timed out after {seconds} seconds.")
        elif type(record.get("returncode")) is not int:
            block(command_id, "missing_returncode", "ADB command has no valid return code.")
        elif record["returncode"] != 0:
            block(command_id, "nonzero_exit", f"ADB command exited with code {record['returncode']}.")
        elif not isinstance(record.get("stdout"), str):
            block(command_id, "missing_stdout", "ADB command returned no readable stdout.")
        else:
            return record, record["stdout"].strip()
        return None, None

    expected = {
        "adb_state": ("device", "ADB state is not 'device'"),
        "boot_completed": ("1", "sys.boot_completed is not '1'"),
        "device_provisioned": ("1", "device_provisioned is not '1'"),
        "user_setup_complete": ("1", "user_setup_complete is not '1'"),
    }
    for command_id, _ in COMMANDS:
        record, value = output(command_id)
        if record is None:
            continue
        if command_id in expected:
            wanted, description = expected[command_id]
            passed = value == wanted
            checks.append({
                "id": command_id,
                "checked": True,
                "passed": passed,
                "blocked": not passed,
                "observed": value,
                **({} if passed else {
                    "reason_code": "value_not_ready",
                    "reason": f"{description}; observed {value!r}.",
                }),
            })
        elif command_id == "sdk_version":
            if not re.fullmatch(r"[0-9]+", value):
                block(command_id, "sdk_unparseable", "SDK output is unknown or not a plain integer.", observed=value)
            else:
                try:
                    sdk = int(value)
                except ValueError:
                    block(command_id, "sdk_unparseable", "SDK output is outside the supported integer range.", observed=value)
                else:
                    passed = sdk >= min_sdk
                    checks.append({
                        "id": command_id,
                        "checked": True,
                        "passed": passed,
                        "blocked": not passed,
                        "observed": sdk,
                        "min_sdk": min_sdk,
                        **({} if passed else {
                            "reason_code": "sdk_below_minimum",
                            "reason": f"SDK {sdk} is below the required minimum {min_sdk}.",
                        }),
                    })
        else:  # HOME resolution
            stderr = record.get("stderr", "")
            component, code, reason = _home_component(
                record["stdout"], stderr if isinstance(stderr, str) else ""
            )
            if code:
                block(command_id, code, reason)
            elif component.split("/", 1)[0].casefold() == "com.android.sdksetup" or any(
                term in component.casefold() for term in ("cryptkeeper", "setupwizard", "fallbackhome")
            ):
                block(command_id, "home_setup_flow", f"HOME resolves to setup/credential flow {component}.", component=component)
            else:
                checks.append({"id": command_id, "checked": True, "passed": True,
                               "blocked": False, "component": component})

    checks.sort(key=lambda item: COMMAND_IDS.index(item["id"]))
    return {"checks": checks, "overall": "ready" if all(item["passed"] for item in checks) else "blocked"}


def _nonblank(value: str) -> str:
    if not value.strip(): raise argparse.ArgumentTypeError("must not be blank")
    return value


def _serial(value: str) -> str:
    if not value or any(char.isspace() for char in value) or value.startswith("-"):
        raise argparse.ArgumentTypeError("serial must be non-empty and contain no whitespace")
    return value


def _positive_int(value: str) -> int:
    try:
        number = int(value, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run read-only ADB preflight checks; ready is not an app test."
    )
    parser.add_argument("--adb", required=True, type=_nonblank, help="ADB executable path")
    parser.add_argument("--serial", required=True, type=_serial, help="existing device/emulator serial")
    parser.add_argument("--out", required=True, type=_nonblank, help="JSON report path")
    parser.add_argument("--min-sdk", type=_positive_int, default=26, help="minimum SDK (default: 26)")
    args = parser.parse_args(argv)

    commands = collect_commands(args.adb, args.serial)
    assessment = evaluate(commands, args.min_sdk)
    report = {
        "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION},
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "target": {"adb": args.adb, "serial": args.serial, "min_sdk": args.min_sdk},
        "commands": commands,
        **assessment,
    }
    try:
        Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"Could not write preflight report: {exc}", file=sys.stderr)
        return 1
    return 0 if assessment["overall"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
