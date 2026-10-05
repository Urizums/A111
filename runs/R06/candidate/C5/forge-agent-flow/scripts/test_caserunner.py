"""Real subprocess and controller regressions for program-mode acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import caserunner as c
import projectctl as p


class CaseRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.adapter = self.root / "adapter.py"
        self.adapter.write_text('import json,sys\nr=json.load(sys.stdin)\nprint(json.dumps({"status":"completed","output":r["inputs"]}))\n')
        self.plan = {"schema": "forge-eval/1", "id": "runtime_eval",
                     "criteria": [{"id": "behavior", "kind": "machine", "required": True,
                                   "assertion": "Actual output equals the specified value"}],
                     "cases": [{"id": "primary", "inputs": {"value": 4}, "expected": {"value": 4},
                                "expected_status": "completed", "criteria": ["behavior"], "required": True}],
                     "baseline": "A local process", "limitations": []}

    def execute(self, code=None, plan=None, name="run", timeout=2):
        if code is not None:
            self.adapter.write_text(code)
        return c.run(plan or self.plan, [sys.executable, str(self.adapter)], self.root,
                     [self.adapter], self.root / name, timeout)

    def test_real_success_preserves_request_without_expectations(self):
        result = self.execute()
        self.assertEqual(result["assessment"]["status"], "pass")
        request = p.load_json(self.root / "run/primary/input.json")
        self.assertEqual(request, {"case_id": "primary", "inputs": {"value": 4}})
        self.assertTrue((self.root / "run/primary/stderr.txt").exists())

    def test_wrong_values_and_boolean_number_do_not_pass(self):
        for i, expected in enumerate(({"value": 5}, {"value": True})):
            plan = deepcopy(self.plan)
            plan["cases"][0]["expected"] = expected
            self.assertEqual(self.execute(plan=plan, name=f"run{i}")["assessment"]["status"], "fail")

    def test_expected_product_failure_requires_successful_adapter_execution(self):
        self.plan["cases"][0].update(expected_status="failed", expected={"error": "invalid"})
        code = 'print(\'{"status":"failed","output":{"error":"invalid"}}\')\n'
        self.assertEqual(self.execute(code)["assessment"]["status"], "pass")
        self.assertEqual(self.execute(code + 'raise SystemExit(3)\n', name="nonzero")["assessment"]["status"], "fail")

    def test_timeout_and_invalid_outputs_fail(self):
        snippets = ['import time; time.sleep(3)', 'print("not JSON")',
                    'print(\'{"status":"completed","output":{"value":4,"value":4}}\')',
                    'print(\'{"status":"completed","output":{"value":NaN}}\')']
        for i, snippet in enumerate(snippets):
            result = self.execute(snippet, name=f"bad{i}", timeout=0.08)
            self.assertEqual(result["assessment"]["status"], "fail")

    def test_human_criteria_cannot_be_automatically_passed(self):
        self.plan["criteria"][0]["kind"] = "human"
        self.assertEqual(self.execute()["assessment"]["status"], "needs_review")

    def test_source_snapshot_keeps_original_bytes_after_repair(self):
        original = self.adapter.read_bytes()
        result = self.execute()
        manifest = p.load_json(self.root / "run/source-snapshot/manifest.json")
        self.adapter.write_text("# repaired source\n")
        copied = manifest["files"][0]["snapshot"]
        self.assertEqual(Path(copied["path"]).read_bytes(), original)
        p.check_evidence(copied, "historical source snapshot")
        with self.assertRaises(p.ProjectError):
            c.grade(self.plan, p.load_json(result["report"]))

    def test_drift_missing_and_forged_input_are_rejected(self):
        result = self.execute()
        report = p.load_json(result["report"])
        original = self.adapter.read_text()
        self.adapter.write_text(original + "# changed\n")
        with self.assertRaises(p.ProjectError):
            c.grade(self.plan, report)
        self.adapter.write_text(original)
        input_path = self.root / "run/primary/input.json"
        p.save(input_path, {"case_id": "primary", "inputs": {"value": 999}})
        report["cases"][0]["input"] = c.ref(input_path)
        with self.assertRaisesRegex(p.ProjectError, "input differs"):
            c.grade(self.plan, report)
        report["cases"] = []
        with self.assertRaisesRegex(p.ProjectError, "cover exactly"):
            c.grade(self.plan, report)

    def project(self):
        plan = {"schema_version": p.SCHEMA, "id": "program", "goal": "Deliver actual behavior",
                "deliverable_kind": "software_system",
                "requirements": [{"id": "req", "text": "Provide runtime behavior", "origin": "explicit",
                                  "basis": "Fixture brief", "acceptance_ids": ["behavior"]}],
                "acceptance": [{"id": "behavior", "assertion": "Actual value is correct",
                                "required": True, "level": "runtime"}],
                "tasks": [{"id": "implement", "title": "Implement", "depends_on": [], "owner": None,
                           "write_paths": ["src/"], "acceptance_ids": ["behavior"]}]}
        path = self.root / "state.json"
        p.init(plan, path, self.plan)
        state = p.load_state(path)
        begun = p.begin(state, "implement")
        evidence = self.root / "task.txt"
        evidence.write_text("Actual fixture work")
        p.finish(state, "implement", begun["attempt_id"], "done", results={
            "evaluation_plan_hash": p.digest(self.plan), "acceptance_results": {
                "behavior": {"status": "pass", "level": "runtime", "evidence": [c.ref(evidence)]}}})
        return state

    def test_controller_requires_cases_even_when_tasks_done_and_detects_later_drift(self):
        state = self.project()
        self.assertEqual(p.next_tasks(state)["status"], "needs_acceptance")
        result = self.execute()
        self.assertEqual(p.assess_cases(state, result["report"])["status"], "pass")
        p.save(self.root / "state.json", state)
        self.assertEqual(p.next_tasks(p.load_state(self.root / "state.json"))["status"], "completed")
        (self.root / "run/primary/stdout.txt").write_text("changed")
        self.assertEqual(p.status(state)["product_acceptance_status"], "unverified")

    def test_failure_routes_to_task_and_revision_invalidates_assessment(self):
        state = self.project()
        result = self.execute('print(\'{"status":"completed","output":{"value":8}}\')')
        self.assertEqual(p.assess_cases(state, result["report"])["status"], "fail")
        pending = p.next_tasks(state)
        self.assertEqual(pending["status"], "acceptance_failed")
        self.assertEqual(pending["acceptance_repairs"][0]["task_ids"], ["implement"])
        p.reopen(state, "implement", "Repair observed runtime mismatch")
        self.assertEqual(p.status(state)["product_acceptance_status"], "stale")
        self.assertEqual(p.next_tasks(state)["ready"][0]["task_id"], "implement")

    def test_old_report_cannot_bind_new_case_plan(self):
        result = self.execute()
        plan = deepcopy(self.plan)
        plan["cases"][0]["inputs"]["value"] = 5
        with self.assertRaisesRegex(p.ProjectError, "frozen plan"):
            c.grade(plan, p.load_json(result["report"]))

    def test_acceptance_repairs_keep_two_attempt_bound_and_old_history(self):
        state = self.project()
        for index in range(3):
            result = self.execute('print(\'{"status":"completed","output":{"value":8}}\')', name=f"failure{index}")
            p.assess_cases(state, result["report"])
            if index == 2:
                with self.assertRaisesRegex(p.ProjectError, "two repair attempts"):
                    p.reopen(state, "implement", "Still incorrect")
                break
            p.reopen(state, "implement", "Repair observed failure")
            begun = p.begin(state, "implement")
            evidence = self.root / f"repair{index}.txt"
            evidence.write_text("Bounded repair fixture; product still deliberately incorrect")
            p.finish(state, "implement", begun["attempt_id"], "done", results={
                "evaluation_plan_hash": p.digest(self.plan), "acceptance_results": {
                    "behavior": {"status": "pass", "level": "runtime", "evidence": [c.ref(evidence)]}}})
        self.assertEqual(len(state["case_assessments"]), 3)
        self.assertEqual(len(state["tasks"]["implement"]["attempts"]), 3)
        self.assertEqual(state["tasks"]["implement"]["repair_attempts"], 2)
        self.assertEqual(p.status(state)["product_acceptance_status"], "fail")
        pending = p.next_tasks(state)
        self.assertEqual(pending["status"], "blocked")
        self.assertTrue(pending["acceptance_repairs"][0]["repair_budget_exhausted"])


if __name__ == "__main__":
    unittest.main()
