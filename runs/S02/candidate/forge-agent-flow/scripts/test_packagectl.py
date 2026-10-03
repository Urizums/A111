"""Regression tests for package boundaries, preservation and honest assessment."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import flowctl as flow
import packagectl as package


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.p = package.load(Path(__file__).resolve().parents[1] / "assets/example-package.json")

    def requirement(self, kind, value, status="verified"):
        return {"id": kind + "_extract", "scope": "extract", "kind": kind, "value": value,
                "status": status, "binding": "synthetic-test-binding" if status == "verified" else "",
                "evidence": ["Synthetic fixture; not a real host verification."] if status == "verified" else []}

    def results(self, status="pass"):
        return {"package_hash": flow.digest(self.p), "checks": [
            {"id": c["id"], "kind": c["kind"], "status": status, "evidence": ["fixture-record"]}
            for c in self.p["acceptance"]["criteria"]]}

    def test_small_package_is_valid_and_round_trips_without_field_loss(self):
        self.assertTrue(package.validate(self.p)["declared_ready"])
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "new"
            result = package.compile_package(self.p, out)
            self.assertTrue(result["declared_ready"])
            self.assertEqual(package.load(out / "package.json"), self.p)
            self.assertEqual(package.load(out / "flow.json"), self.p["flow"])

    def test_structural_failure_prevents_compile_and_start_and_cannot_be_graded_away(self):
        self.p["flow"]["nodes"].append(copy.deepcopy(self.p["flow"]["nodes"][0]))
        self.assertFalse(package.validate(self.p)["valid"])
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "new"
            with self.assertRaises(flow.FlowError):
                package.compile_package(self.p, out)
            self.assertFalse(out.exists())
        with self.assertRaises(flow.FlowError):
            package.start(self.p, {"notes": ""})
        self.assertEqual(package.assess(self.p, self.results())["verdict"], "fail")

    def test_requested_model_is_blocked_until_exact_mapping_exists(self):
        self.p["execution"]["node_settings"]["extract"]["model"] = "fixture-model"
        self.assertFalse(package.validate(self.p)["declared_ready"])
        with self.assertRaises(flow.FlowError):
            package.start(self.p, {"notes": ""})
        self.p["execution"]["requirements"] = [self.requirement("model", "different-model")]
        self.assertFalse(package.validate(self.p)["declared_ready"])
        self.p["execution"]["requirements"] = [self.requirement("model", "fixture-model")]
        state = package.start(self.p, {"notes": ""})
        dispatch = package.pending(self.p, state)
        self.assertEqual(dispatch["execution_settings"]["model"], "fixture-model")
        self.assertEqual(dispatch["host_requirements"], self.p["execution"]["requirements"])
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "compiled"
            package.compile_package(self.p, out)
            self.assertIn("fixture-model", (out / "prompts/extract.md").read_text())

    def test_write_scope_requires_exact_mapping_and_survives_dispatch(self):
        self.p["execution"]["node_settings"]["extract"]["write_scope"] = ["task/output/"]
        self.p["execution"]["requirements"] = [self.requirement("write_scope", ["other/"])]
        self.assertFalse(package.validate(self.p)["declared_ready"])
        self.p["execution"]["requirements"] = [self.requirement("write_scope", ["task/output/"])]
        dispatch = package.pending(self.p, package.start(self.p, {"notes": ""}))
        self.assertEqual(dispatch["execution_settings"]["write_scope"], ["task/output/"])

    def test_contradictory_model_or_scope_requirement_is_invalid_even_with_default_settings(self):
        for kind, value in (("model", "contradictory-model"), ("write_scope", ["unrequested/"])):
            with self.subTest(kind=kind):
                self.p["execution"]["requirements"] = [self.requirement(kind, value)]
                self.assertFalse(package.validate(self.p)["valid"])
                with self.assertRaises(flow.FlowError):
                    package.start(self.p, {"notes": ""})
        self.p["execution"]["requirements"][0]["scope"] = "flow"
        self.assertFalse(package.validate(self.p)["valid"])

    def test_local_write_tool_cannot_use_empty_scope(self):
        self.p["flow"]["capabilities"] = {"workspace": {"binding": "fixture", "effect": "local_write", "available": True, "authorization": "granted", "evidence": "test fixture"}}
        self.p["flow"]["nodes"][0]["tools"] = ["workspace"]
        validation = package.validate(self.p)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("write_scope" in e for e in validation["errors"]))

    def test_flow_wide_scope_cannot_be_confused_with_a_node_id(self):
        self.p["flow"]["nodes"][0]["id"] = "flow"
        self.p["flow"]["entry"] = "flow"
        self.p["execution"]["node_settings"]["flow"] = self.p["execution"]["node_settings"].pop("extract")
        self.assertFalse(package.validate(self.p)["valid"])

    def test_verified_requirement_needs_binding_and_evidence(self):
        r = self.requirement("guard", "deny fixture operation")
        self.p["execution"]["requirements"] = [r]
        for field, value in (("binding", ""), ("evidence", [])):
            with self.subTest(field=field):
                saved = r[field]
                r[field] = value
                self.assertFalse(package.validate(self.p)["valid"])
                r[field] = saved

    def test_unverified_unsupported_and_unresolved_block_execution(self):
        for status in ("unverified", "unsupported"):
            with self.subTest(status=status):
                self.p["execution"]["requirements"] = [self.requirement("guard", "deny fixture operation", status)]
                self.assertTrue(package.validate(self.p)["valid"])
                with self.assertRaises(flow.FlowError):
                    package.start(self.p, {"notes": ""})
        self.p["execution"]["requirements"] = []
        self.p["execution"]["unresolved"] = ["Unmapped legacy budget"]
        with self.assertRaises(flow.FlowError):
            package.start(self.p, {"notes": ""})
        self.assertEqual(package.assess(self.p, self.results())["verdict"], "pending")

    def test_unsupported_adapter_and_parallelism_are_design_only(self):
        for key, value in (("adapter", "native-unknown"), ("parallelism", 2)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                changed = copy.deepcopy(self.p)
                changed["execution"][key] = value
                self.assertFalse(package.compile_package(changed, Path(folder) / "out")["declared_ready"])
                with self.assertRaises(flow.FlowError):
                    package.start(changed, {"notes": ""})

    def test_full_design_needs_all_unique_dimensions(self):
        self.p["design"]["mode"] = "full"
        self.assertFalse(package.validate(self.p)["valid"])
        decision = self.p["design"]["decisions"][0]
        self.p["design"]["decisions"] = [{**decision, "id": f"D{i:02}"} for i in range(1, 15)]
        self.assertTrue(package.validate(self.p)["valid"])
        self.p["design"]["decisions"].append(copy.deepcopy(decision))
        self.assertFalse(package.validate(self.p)["valid"])

    def test_complete_run_and_duplicate_advancement(self):
        state = package.start(self.p, {"notes": "No commitments."})
        dispatch = package.pending(self.p, state)
        response = {"invocation_id": dispatch["invocation_id"], "outcome": "ok", "artifacts": {"actions": []}, "evidence": ["fixture: no commitments"]}
        end = package.advance(self.p, state, response)
        self.assertEqual(package.pending(self.p, end)["status"], "completed")
        with self.assertRaises(flow.FlowError):
            package.advance(self.p, end, response)

    def test_resume_rejects_design_or_policy_or_criteria_change(self):
        state = package.start(self.p, {"notes": ""})
        changes = [lambda p: p["design"]["source_refs"].append("changed"),
                   lambda p: p["execution"]["requirements"].append(self.requirement("guard", "changed")),
                   lambda p: p["acceptance"]["criteria"][0].update(assertion="changed")]
        for change in changes:
            with self.subTest(change=change):
                changed = copy.deepcopy(self.p)
                change(changed)
                with self.assertRaisesRegex(flow.FlowError, "Package changed"):
                    package.pending(changed, state)

    def test_required_failure_and_missing_results_remain_visible(self):
        result = self.results()
        result["checks"][0]["status"] = "fail"
        self.assertEqual(package.assess(self.p, result)["verdict"], "fail")
        result["checks"] = result["checks"][1:]
        self.assertEqual(package.assess(self.p, result)["verdict"], "pending")
        self.assertEqual(package.assess(self.p, self.results())["verdict"], "pass")

    def test_optional_unrun_or_failed_is_limited(self):
        self.p["acceptance"]["criteria"].append({"id": "optional", "kind": "human", "required": False, "assertion": "Optional check"})
        results = self.results()
        results["checks"].pop()
        self.assertEqual(package.assess(self.p, results)["verdict"], "limited")

    def test_cannot_override_machine_result_with_manual_or_duplicate(self):
        results = self.results()
        results["checks"][0]["kind"] = "human"
        with self.assertRaisesRegex(flow.FlowError, "grader kind"):
            package.assess(self.p, results)
        results = self.results()
        results["checks"].append({**results["checks"][0], "status": "fail"})
        with self.assertRaisesRegex(flow.FlowError, "duplicate result"):
            package.assess(self.p, results)
        results = self.results()
        results["package_hash"] = "wrong"
        with self.assertRaisesRegex(flow.FlowError, "package_hash"):
            package.assess(self.p, results)

    def test_malformed_duplicate_and_nonfinite_json_cli_fail_without_output(self):
        for raw in ("{", '{"schema":"forge-package/1","schema":"forge-package/1"}', '{"x":NaN}', '{"x":1e999}'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as folder:
                source, out = Path(folder) / "bad.json", Path(folder) / "out"
                source.write_text(raw)
                result = subprocess.run([sys.executable, package.__file__, "compile", str(source), "--out", str(out)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(out.exists())
                self.assertNotIn("Traceback", result.stderr)

    def test_unknown_fields_are_rejected_not_silently_ignored(self):
        self.p["execution"]["automatic_permission_override"] = True
        self.assertFalse(package.validate(self.p)["valid"])

    def test_malformed_checkpoint_fails_cleanly_and_is_not_rewritten(self):
        for state in ([], None, {"package_hash": flow.digest(self.p), "flow_state": []}):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as folder:
                p, checkpoint = Path(folder) / "package.json", Path(folder) / "state.json"
                p.write_text(json.dumps(self.p))
                original = json.dumps(state)
                checkpoint.write_text(original)
                result = subprocess.run([sys.executable, package.__file__, "next", str(p), "--state", str(checkpoint)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(checkpoint.read_text(), original)


if __name__ == "__main__":
    unittest.main()
