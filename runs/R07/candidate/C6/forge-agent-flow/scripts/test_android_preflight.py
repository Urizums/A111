#!/usr/bin/env python3
"""Fixture tests for the read-only Android runtime preflight."""

from __future__ import annotations

import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True

from android_preflight import COMMAND_IDS, COMMAND_TIMEOUT_SECONDS, collect_commands, evaluate


def make_records(**overrides):
    defaults = {
        "adb_state": ("device\n", 0, False),
        "boot_completed": ("1\n", 0, False),
        "sdk_version": ("34\n", 0, False),
        "device_provisioned": ("1\n", 0, False),
        "user_setup_complete": ("1\n", 0, False),
        "home_activity": (
            "priority=0 preferredOrder=0 match=0x108000\n"
            "com.android.launcher3/.Launcher\n",
            0,
            False,
        ),
    }
    defaults.update(overrides)
    return [
        {
            "id": command_id,
            "command": ["adb", "-s", "emulator-5554", command_id],
            "returncode": defaults[command_id][1],
            "stdout": defaults[command_id][0],
            "stderr": "probe error" if defaults[command_id][1] else "",
            "timeout": defaults[command_id][2],
            "timeout_seconds": COMMAND_TIMEOUT_SECONDS,
        }
        for command_id in COMMAND_IDS
    ]


def check_map(result):
    return {check["id"]: check for check in result["checks"]}


class AndroidPreflightTests(unittest.TestCase):
    def test_normal_runtime_is_ready(self):
        result = evaluate(make_records(), 26)
        self.assertEqual(result["overall"], "ready")
        self.assertTrue(all(item["checked"] and item["passed"] for item in result["checks"]))
        self.assertEqual(check_map(result)["home_activity"]["component"], "com.android.launcher3/.Launcher")

    def test_booted_but_unprovisioned_cryptkeeper_is_blocked(self):
        records = make_records(
            device_provisioned=("0\n", 0, False),
            home_activity=(
                "priority=10 preferredOrder=0 isDefault=true\n"
                "com.android.settings/.CryptKeeper\n",
                0,
                False,
            ),
        )
        result = evaluate(records, 26)
        checks = check_map(result)
        self.assertEqual(result["overall"], "blocked")
        self.assertTrue(checks["boot_completed"]["passed"])
        self.assertEqual(checks["device_provisioned"]["reason_code"], "value_not_ready")
        self.assertIn("device_provisioned", checks["device_provisioned"]["reason"])
        self.assertEqual(checks["home_activity"]["reason_code"], "home_setup_flow")
        self.assertIn("CryptKeeper", checks["home_activity"]["reason"])
        wizard = evaluate(
            make_records(home_activity=("com.google.android.setupwizard/.SetupWizardActivity\n", 0, False)),
            26,
        )
        self.assertEqual(check_map(wizard)["home_activity"]["reason_code"], "home_setup_flow")
        fallback = evaluate(
            make_records(home_activity=("com.android.internal.app/.FallbackHome\n", 0, False)), 26
        )
        self.assertEqual(check_map(fallback)["home_activity"]["reason_code"], "home_setup_flow")
        for component, expected in (
            ("com.android.sdksetup/.DefaultActivity", "home_setup_flow"),
            ("com.example.launcher/.DefaultActivity", None),
        ):
            with self.subTest(component=component):
                sample = evaluate(make_records(home_activity=(f"{component}\n", 0, False)), 26)
                home = check_map(sample)["home_activity"]
                self.assertEqual(home.get("reason_code"), expected)
                self.assertEqual(home["passed"], expected is None)

    def test_home_without_explicit_activity_is_blocked_even_with_zero_exit(self):
        records = make_records(home_activity=("No activity found\n", 0, False))
        result = evaluate(records, 26)
        home = check_map(result)["home_activity"]
        self.assertEqual(result["overall"], "blocked")
        self.assertTrue(home["checked"])
        self.assertFalse(home["passed"])
        self.assertEqual(home["reason_code"], "home_no_activity")

    def test_home_rejects_unclear_lines_and_accepts_brief_metadata_and_adb_startup(self):
        component = "com.android.launcher3/.Launcher"
        for line in (
            "Error: resolver unavailable",
            "Unknown resolver state",
            "bad..package/.Launcher",
            "com.android.launcher3/..Foo",
        ):
            with self.subTest(line=line):
                records = make_records(home_activity=(f"{line}\n{component}\n", 0, False))
                home = check_map(evaluate(records, 26))["home_activity"]
                self.assertFalse(home["passed"])
                self.assertEqual(home["reason_code"], "home_unrecognized_output")

        duplicate = make_records(home_activity=(f"{component}\n{component}\n", 0, False))
        self.assertEqual(check_map(evaluate(duplicate, 26))["home_activity"]["reason_code"], "home_ambiguous")

        valid = make_records(
            home_activity=(f"isDefault=true priority=0\n{component}\n", 0, False)
        )
        valid[-1]["stderr"] = (
            "* daemon not running; starting now at tcp:5037\n"
            "* daemon started successfully\n"
        )
        self.assertEqual(evaluate(valid, 26)["overall"], "ready")
        mystery = make_records(home_activity=(f"{component}\n", 0, False))
        mystery[-1]["stderr"] = "mystery diagnostic\n"
        self.assertEqual(
            check_map(evaluate(mystery, 26))["home_activity"]["reason_code"],
            "home_unrecognized_stderr",
        )
        for diagnostic in ("Error: resolver unavailable", "Exception: resolver crashed"):
            with self.subTest(stderr=diagnostic):
                failed = make_records(home_activity=(f"{component}\n", 0, False))
                failed[-1]["stderr"] = diagnostic
                self.assertEqual(
                    check_map(evaluate(failed, 26))["home_activity"]["reason_code"],
                    "home_stderr_error",
                )

    def test_timeout_and_nonzero_exit_block_but_other_results_are_evaluated(self):
        records = make_records(
            boot_completed=("", None, True),
            user_setup_complete=("", 2, False),
        )
        result = evaluate(records, 26)
        checks = check_map(result)
        self.assertEqual(result["overall"], "blocked")
        self.assertEqual(checks["boot_completed"]["reason_code"], "timeout")
        self.assertEqual(checks["user_setup_complete"]["reason_code"], "nonzero_exit")
        self.assertTrue(checks["home_activity"]["passed"])
        for timeout in (None, "true", "false"):
            with self.subTest(timeout=timeout):
                malformed = make_records()
                home_record = next(item for item in malformed if item["id"] == "home_activity")
                if timeout is None:
                    del home_record["timeout"]
                else:
                    home_record["timeout"] = timeout
                self.assertEqual(
                    check_map(evaluate(malformed, 26))["home_activity"]["reason_code"],
                    "invalid_timeout",
                )

    def test_sdk_must_be_parseable_and_meet_minimum(self):
        invalid = evaluate(make_records(sdk_version=("unknown\n", 0, False)), 26)
        low = evaluate(make_records(sdk_version=("25\n", 0, False)), 26)
        self.assertEqual(check_map(invalid)["sdk_version"]["reason_code"], "sdk_unparseable")
        self.assertEqual(check_map(low)["sdk_version"]["reason_code"], "sdk_below_minimum")
        self.assertEqual(invalid["overall"], "blocked")
        self.assertEqual(low["overall"], "blocked")

    def test_returncode_zero_alone_never_means_ready(self):
        records = make_records(
            adb_state=("offline\n", 0, False),
            boot_completed=("0\n", 0, False),
            device_provisioned=("0\n", 0, False),
            user_setup_complete=("unknown\n", 0, False),
            home_activity=("resolver returned no component\n", 0, False),
        )
        self.assertTrue(all(record["returncode"] == 0 for record in records))
        result = evaluate(records, 26)
        self.assertEqual(result["overall"], "blocked")
        self.assertFalse(all(check["passed"] for check in result["checks"]))

    def test_collection_continues_after_timeout_and_bounds_each_adb_call(self):
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            if len(calls) == 2:
                raise subprocess.TimeoutExpired(argv, COMMAND_TIMEOUT_SECONDS, output=b"")
            return SimpleNamespace(
                returncode=1 if len(calls) == 4 else 0,
                stdout="ok\n",
                stderr="failure" if len(calls) == 4 else "",
            )

        with patch("android_preflight.subprocess.run", side_effect=fake_run):
            records = collect_commands("/opt/android/platform-tools/adb", "emulator-5554")
        self.assertEqual(len(records), 6)
        self.assertEqual(len(calls), 6)
        self.assertTrue(records[1]["timeout"])
        self.assertEqual(records[3]["returncode"], 1)
        self.assertEqual(records[4]["returncode"], 0)
        for _, kwargs in calls:
            self.assertLessEqual(kwargs["timeout"], 15)
            self.assertIs(kwargs["shell"], False)
        self.assertEqual(records[0]["command"][:3], ["/opt/android/platform-tools/adb", "-s", "emulator-5554"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
