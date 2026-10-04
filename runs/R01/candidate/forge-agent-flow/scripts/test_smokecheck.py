"""Portable tests for the smokecheck structure and binding gate."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import flowctl
import smokecheck


def complete_plan():
    return {
        "schema": smokecheck.PLAN_SCHEMA,
        "project_kind": "change",
        "baseline": {
            "id": "release_4",
            "protected_behaviors": [
                {"id": "saved_items_persist", "description": "Saved items remain after relaunch."},
                {"id": "sign_in_works", "description": "A user can sign in with valid credentials."},
            ],
        },
        "candidate_id": "candidate-v5",
        "journeys": [
            {
                "id": "open_home",
                "goal": "Open the home screen",
                "initial_state": "Installed candidate with a signed-in account",
                "steps": ["Launch", "Wait for home content"],
                "expected": ["Home content appears"],
                "kind": "main",
                "required": True,
                "min_level": "runtime",
                "min_backend": "live",
            },
            {
                "id": "recover_offline",
                "goal": "Recover after connectivity returns",
                "initial_state": "Home is open while offline",
                "steps": ["Restore connectivity", "Retry loading"],
                "expected": ["Content loads without losing state"],
                "kind": "recovery",
                "required": True,
                "min_level": "static",
                "min_backend": "none",
            },
            {
                "id": "repeat_open",
                "goal": "Repeat opening the home screen",
                "initial_state": "Candidate is already open once",
                "steps": ["Close", "Launch again"],
                "expected": ["Home content appears again"],
                "kind": "repeat",
                "required": True,
                "min_level": "runtime",
                "min_backend": "mocked",
            },
        ],
    }


def complete_results(plan):
    runs = []
    for round_number in (1, 2):
        for journey in plan["journeys"]:
            runs.append({
                "journey_id": journey["id"],
                "round": round_number,
                "candidate_id": plan["candidate_id"],
                "level": "runtime",
                "backend": "live" if journey["min_backend"] == "live" else "mocked",
                "status": "pass",
                "observations": [f"Round {round_number}: expected state recorded"],
                "evidence": [f"evidence/{journey['id']}/round-{round_number}"],
            })
    return {
        "schema": smokecheck.RESULTS_SCHEMA,
        "plan_hash": flowctl.digest(plan),
        "candidate_id": plan["candidate_id"],
        "baseline_id": plan["baseline"]["id"],
        "claim_scope": smokecheck.CLAIM_SCOPE,
        "runs": runs,
        "regressions": [
            {
                "behavior_id": behavior["id"],
                "candidate_id": plan["candidate_id"],
                "status": "pass",
                "evidence": [f"regression/{behavior['id']}"]
            }
            for behavior in plan["baseline"]["protected_behaviors"]
        ],
    }


class SmokecheckTests(unittest.TestCase):
    def test_two_bound_runtime_rounds_and_protected_regressions_pass(self):
        plan = complete_plan()
        results = complete_results(plan)
        self.assertEqual(smokecheck.assess(plan, results)["status"], "pass")
        plan["project_kind"] = "new"
        plan["baseline"] = {"id": "none", "protected_behaviors": []}
        results = complete_results(plan)
        results["regressions"] = []
        self.assertEqual(smokecheck.assess(plan, results)["status"], "pass")

    def test_earlier_failure_is_preserved_but_later_complete_round_can_pass(self):
        plan = complete_plan()
        results = complete_results(plan)
        first = next(run for run in results["runs"] if run["round"] == 1 and run["journey_id"] == "open_home")
        first["status"] = "fail"
        report = smokecheck.assess(plan, results)
        self.assertEqual(report["status"], "pass")
        self.assertIn(1, report["runtime_rounds"])
        self.assertEqual(report["final_round"], 2)

    def test_no_runs_is_unverified_and_never_passes(self):
        plan = complete_plan()
        results = complete_results(plan)
        results["runs"] = []
        report = smokecheck.assess(plan, results)
        self.assertEqual(report["status"], "unverified")
        self.assertTrue(any("No run records" in reason for reason in report["reasons"]))
        results = complete_results(plan)
        results["runs"] = [run for run in results["runs"] if run["round"] == 1]
        self.assertEqual(smokecheck.assess(plan, results)["status"], "unverified")

    def test_old_plan_hash_is_rejected(self):
        plan = complete_plan()
        results = complete_results(plan)
        results["plan_hash"] = "0" * 64
        self.assertEqual(smokecheck.assess(plan, results)["status"], "invalid")

    def test_plan_candidate_baseline_and_regression_candidate_are_bound(self):
        plan = complete_plan()
        results = complete_results(plan)
        results["candidate_id"] = "candidate-v4"
        self.assertEqual(smokecheck.assess(plan, results)["status"], "invalid")
        results = complete_results(plan)
        results["runs"][0]["candidate_id"] = "candidate-v4"
        self.assertEqual(smokecheck.assess(plan, results)["status"], "invalid")
        results = complete_results(plan)
        results["baseline_id"] = "release_3"
        self.assertEqual(smokecheck.assess(plan, results)["status"], "invalid")
        results = complete_results(plan)
        results["regressions"][0]["candidate_id"] = "candidate-v4"
        self.assertEqual(smokecheck.assess(plan, results)["status"], "invalid")

    def test_simulated_run_cannot_satisfy_runtime_minimum(self):
        plan = complete_plan()
        results = complete_results(plan)
        for run in results["runs"]:
            if run["journey_id"] == "open_home":
                run["level"] = "simulated"
        report = smokecheck.assess(plan, results)
        self.assertEqual(report["status"], "unverified")
        self.assertIn("open_home", report["uncovered_required_journeys"])
        results = complete_results(plan)
        for run in results["runs"]:
            run["level"] = "simulated"
        self.assertEqual(smokecheck.assess(plan, results)["runtime_rounds"], [])

    def test_mock_cannot_satisfy_live_backend_minimum(self):
        plan = complete_plan()
        results = complete_results(plan)
        for run in results["runs"]:
            if run["journey_id"] == "open_home":
                run["backend"] = "mocked"
        report = smokecheck.assess(plan, results)
        self.assertEqual(report["status"], "unverified")
        self.assertIn("open_home", report["uncovered_required_journeys"])

    def test_duplicate_case_in_same_round_is_invalid(self):
        plan = complete_plan()
        results = complete_results(plan)
        results["runs"].append(copy.deepcopy(results["runs"][0]))
        with self.assertRaises(flowctl.FlowError):
            smokecheck.assess(plan, results)

    def test_final_round_failure_blocks_earlier_passes(self):
        plan = complete_plan()
        results = complete_results(plan)
        final_open = next(run for run in results["runs"] if run["round"] == 2 and run["journey_id"] == "open_home")
        final_open["status"] = "blocked"
        report = smokecheck.assess(plan, results)
        self.assertEqual(report["status"], "fail")

    def test_missing_or_failed_protected_behavior_never_passes(self):
        plan = complete_plan()
        results = complete_results(plan)
        results["regressions"].pop()
        report = smokecheck.assess(plan, results)
        self.assertEqual(report["status"], "unverified")
        self.assertIn("sign_in_works", report["unverified_protected_behaviors"])
        results = complete_results(plan)
        results["regressions"][0]["status"] = "fail"
        report = smokecheck.assess(plan, results)
        self.assertEqual(report["status"], "fail")
        self.assertIn(results["regressions"][0]["behavior_id"], report["failed_protected_behaviors"])

    def test_wrong_types_raise_flowerror_instead_of_typeerror(self):
        plan = complete_plan()
        malformed = copy.deepcopy(plan)
        malformed["journeys"] = "not an array"
        with self.assertRaises(flowctl.FlowError):
            smokecheck.require_plan(malformed)
        for field, wrong_value in (("kind", []), ("min_backend", {})):
            malformed = copy.deepcopy(plan)
            malformed["journeys"][0][field] = wrong_value
            with self.assertRaises(flowctl.FlowError):
                smokecheck.require_plan(malformed)
        results = complete_results(plan)
        results["runs"] = [{"round": []}]
        with self.assertRaises(flowctl.FlowError):
            smokecheck.assess(plan, results)
        for field, wrong_value in (("level", []), ("backend", {}), ("status", [])):
            results = complete_results(plan)
            results["runs"][0][field] = wrong_value
            with self.assertRaises(flowctl.FlowError):
                smokecheck.assess(plan, results)
        results = complete_results(plan)
        results["runs"][0]["journey_id"] = []
        with self.assertRaises(flowctl.FlowError):
            smokecheck.assess(plan, results)
        results = complete_results(plan)
        results["regressions"][0]["status"] = []
        with self.assertRaises(flowctl.FlowError):
            smokecheck.assess(plan, results)

    def test_change_plan_requires_protected_behaviors_and_all_three_kinds(self):
        plan = complete_plan()
        plan["baseline"]["protected_behaviors"] = []
        with self.assertRaises(flowctl.FlowError):
            smokecheck.require_plan(plan)
        plan = complete_plan()
        plan["project_kind"] = "new"
        plan["baseline"] = {"id": "none", "protected_behaviors": []}
        smokecheck.require_plan(plan)
        plan = complete_plan()
        plan["journeys"] = [j for j in plan["journeys"] if j["kind"] != "repeat"]
        with self.assertRaises(flowctl.FlowError):
            smokecheck.require_plan(plan)
        plan = complete_plan()
        plan["journeys"][0]["required"] = False
        with self.assertRaises(flowctl.FlowError):
            smokecheck.require_plan(plan)


if __name__ == "__main__":
    unittest.main()
