"""Tests for incomplete, non-overwriting Forge protocol templates."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import evalplan
import factoryctl as factory
import flowctl as flow
import forge_template as templates
import packagectl as package


ROOT = Path(__file__).resolve().parents[1]


class ForgeTemplateTests(unittest.TestCase):
    def setUp(self):
        self.package_v1 = package.load(ROOT / "assets/example-package.json")
        self.package_v2 = copy.deepcopy(self.package_v1)
        self.plan = {
            "schema": "forge-eval/1",
            "id": "template_contract",
            "criteria": [
                {"id": "shape", "kind": "machine", "required": True,
                 "assertion": "The output has the declared shape."},
                {"id": "meaning", "kind": "human", "required": True,
                 "assertion": "The output follows the task contract."},
            ],
            "cases": [
                {"id": "ordinary", "inputs": {"notes": "Mina will send the draft."},
                 "expected": {"actions": [{"task": "send the draft"}]},
                 "expected_status": "completed", "criteria": ["shape", "meaning"], "required": True},
                {"id": "empty", "inputs": {"notes": "No commitments."},
                 "expected": {"actions": []}, "expected_status": "completed",
                 "criteria": ["shape", "meaning"], "required": True},
            ],
            "baseline": "One host agent extracts explicit actions from supplied notes.",
            "limitations": ["Submitted grades and evidence require independent inspection."],
        }
        self.package_v2["schema"] = "forge-package/2"
        self.package_v2["acceptance"] = evalplan.make_lock(copy.deepcopy(self.plan))
        self.assertTrue(package.validate(self.package_v2)["valid"], package.validate(self.package_v2)["errors"])

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/forge_template.py"), *map(str, args)],
            text=True, capture_output=True,
        )

    def write_json(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def real_dispatch(self):
        state = package.start(self.package_v1, {"notes": "Mina will send the draft."})
        dispatch = package.pending(self.package_v1, state)
        self.assertEqual(dispatch["status"], "ready")
        return state, dispatch

    def test_response_draft_uses_real_dispatch_and_stays_unadvanceable(self):
        state, dispatch = self.real_dispatch()
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            dispatch_path, out = directory / "dispatch.json", directory / "response.json"
            self.write_json(dispatch_path, dispatch)
            original = dispatch_path.read_bytes()
            result = self.run_cli("response", "--dispatch", dispatch_path,
                                  "--outcome", "ok", "--out", out)
            self.assertEqual(result.returncode, 0, result.stderr)
            draft = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(set(draft), {"invocation_id", "outcome", "artifacts", "evidence"})
            self.assertEqual(draft["invocation_id"], dispatch["invocation_id"])
            self.assertEqual(draft["outcome"], "ok")
            self.assertEqual(set(draft["artifacts"]), set(dispatch["outcomes"]["ok"]))
            self.assertEqual(draft["artifacts"], {"actions": []})
            self.assertEqual(draft["evidence"], [])
            self.assertEqual(dispatch_path.read_bytes(), original)
            with self.assertRaisesRegex(flow.FlowError, "evidence"):
                package.advance(self.package_v1, state, draft)

    def test_response_draft_from_stale_dispatch_is_rejected_by_advance(self):
        _, dispatch = self.real_dispatch()
        draft = templates.make_response_draft(dispatch, "ok")
        another_run = package.start(self.package_v1, {"notes": "Mina will send the draft."})
        self.assertNotEqual(package.pending(self.package_v1, another_run)["invocation_id"],
                            draft["invocation_id"])
        with self.assertRaisesRegex(flow.FlowError, "Stale or duplicate invocation_id"):
            package.advance(self.package_v1, another_run, draft)

    def test_response_template_accepts_descriptor_extensions_without_schema_generation(self):
        _, dispatch = self.real_dispatch()
        extended = copy.deepcopy(dispatch)
        extended["artifact_types"]["actions"]["schema"] = {
            "type": "array", "items": {
                "type": "object", "properties": {"task": {"type": "string"}},
                "required": ["task"], "additionalProperties": False,
            }
        }
        draft = templates.make_response_draft(extended, "ok")
        self.assertEqual(draft["artifacts"], {"actions": []})
        self.assertEqual(extended["artifact_types"]["actions"]["schema"]["items"]["required"], ["task"])

    def test_response_template_accepts_real_v2_package_dispatch(self):
        case = self.plan["cases"][0]
        state = package.start(self.package_v2, case["inputs"])
        dispatch = package.pending(self.package_v2, state)
        self.assertEqual(dispatch["status"], "ready")
        self.assertEqual(dispatch["plan_hash"], self.package_v2["acceptance"]["plan_hash"])
        draft = templates.make_response_draft(dispatch, "ok")
        self.assertEqual(draft["invocation_id"], dispatch["invocation_id"])
        self.assertEqual(draft["artifacts"], {"actions": []})

    def test_response_template_accepts_real_factory_dispatch_and_checks_material_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source = directory / "source.zip"
            source.write_bytes(b"Fixture source snapshot\n")
            manifest = {
                "schema": "forge-materials/1", "intent": "source_only",
                "source": {"path": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                           "role": "target_source", "identity": "fixture app", "stack": "python",
                           "platform": "test", "fingerprint_scope": "complete_source_snapshot"},
                "binary": None, "references": [], "provenance": None,
            }
            manifest_path = directory / "materials.json"
            manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
            state = factory.start(
                {"request": "Inspect the supplied fixture.", "environment": {"fixture": True}},
                manifest_path, "modify",
            )
            dispatch = factory.pending(state)
            self.assertEqual(dispatch["status"], "ready")
            self.assertEqual(dispatch["materials_assessment"]["decision"], "allow")
            self.assertEqual(dispatch["materials_assessment"]["operation"], "modify")
            self.assertIn("modify", dispatch["materials_assessment"]["allowed_operations"])
            draft = templates.make_response_draft(dispatch, "ok")
            self.assertEqual(draft["invocation_id"], dispatch["invocation_id"])

            denied = copy.deepcopy(dispatch)
            denied["materials_assessment"]["decision"] = "blocked"
            denied["materials_assessment"]["allowed_operations"] = []
            denied["materials_assessment"]["gate_blockers"] = ["operation not allowed"]
            with self.assertRaisesRegex(templates.TemplateError, "does not allow operation"):
                templates.make_response_draft(denied, "ok")

    def test_factory_pending_without_material_configuration_is_supported(self):
        state = factory.start({"request": "Design a fixture flow.", "environment": {"fixture": True}})
        dispatch = factory.pending(state)
        self.assertEqual(dispatch["materials_assessment"]["decision"], "not_configured")
        draft = templates.make_response_draft(dispatch, "ok")
        self.assertEqual(draft["invocation_id"], dispatch["invocation_id"])

    def test_bad_dispatches_and_outcomes_fail_without_touching_inputs_or_creating_output(self):
        _, dispatch = self.real_dispatch()
        cases = [
            ("blocked", dispatch),
            ("terminal", {"status": "completed"}),
            ("missing-field", {key: value for key, value in dispatch.items() if key != "artifact_types"}),
            ("bad-outcome", dispatch),
            ("unknown-descriptor-extension", dispatch),
        ]
        for label, body in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder)
                source, out = directory / "dispatch.json", directory / "response.json"
                value = copy.deepcopy(body)
                outcome = "ok"
                if label == "blocked":
                    value["status"] = "blocked"
                elif label == "bad-outcome":
                    outcome = "not-a-route"
                elif label == "unknown-descriptor-extension":
                    value = copy.deepcopy(value)
                    value["artifact_types"]["actions"]["x-extra"] = "must be rejected"
                self.write_json(source, value)
                original = source.read_bytes()
                result = self.run_cli("response", "--dispatch", source,
                                      "--outcome", outcome, "--out", out)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(out.exists())
                self.assertEqual(source.read_bytes(), original)

    def test_response_output_never_overwrites_input_or_existing_file(self):
        _, dispatch = self.real_dispatch()
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source = directory / "dispatch.json"
            self.write_json(source, dispatch)
            original = source.read_bytes()
            same_path = self.run_cli("response", "--dispatch", source,
                                     "--outcome", "ok", "--out", source)
            self.assertEqual(same_path.returncode, 2)
            self.assertEqual(source.read_bytes(), original)

            out = directory / "already-there.json"
            out.write_text("keep this file\n", encoding="utf-8")
            previous = out.read_bytes()
            exists = self.run_cli("response", "--dispatch", source,
                                  "--outcome", "ok", "--out", out)
            self.assertEqual(exists.returncode, 2)
            self.assertEqual(out.read_bytes(), previous)
            self.assertEqual(source.read_bytes(), original)

    def test_results_template_covers_exact_plan_and_assessment_is_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            package_path, out = directory / "package.json", directory / "results.json"
            self.write_json(package_path, self.package_v2)
            original = package_path.read_bytes()
            result = self.run_cli("results", "--package", package_path, "--out", out)
            self.assertEqual(result.returncode, 0, result.stderr)
            draft = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(draft["package_hash"], flow.digest(self.package_v2))
            self.assertEqual(draft["plan_hash"], self.package_v2["acceptance"]["plan_hash"])
            self.assertEqual([row["case_id"] for row in draft["cases"]],
                             [case["id"] for case in self.plan["cases"]])
            criteria = {c["id"]: c["kind"] for c in self.plan["criteria"]}
            for row, case in zip(draft["cases"], self.plan["cases"]):
                self.assertEqual(row["run"], None)
                self.assertEqual(
                    row["checks"],
                    [{"id": cid, "kind": criteria[cid], "status": "not_run", "evidence": []}
                     for cid in case["criteria"]],
                )
            assessed = package.assess(self.package_v2, draft)
            self.assertEqual(assessed["verdict"], "pending")
            self.assertEqual(package_path.read_bytes(), original)

    def test_v1_or_invalid_package_rejected_without_output_or_input_change(self):
        for label, body in (("v1", self.package_v1), ("invalid-v2", {**self.package_v2, "design": {}})):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder)
                source, out = directory / "package.json", directory / "results.json"
                self.write_json(source, body)
                original = source.read_bytes()
                result = self.run_cli("results", "--package", source, "--out", out)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(out.exists())
                self.assertEqual(source.read_bytes(), original)

    def test_strict_json_errors_do_not_create_drafts(self):
        invalid_inputs = ("{", '{"status":"ready","status":"blocked"}', '{"x":NaN}', '{"x":1e999}')
        for raw in invalid_inputs:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder)
                source, out = directory / "dispatch.json", directory / "response.json"
                source.write_text(raw, encoding="utf-8")
                original = source.read_bytes()
                result = self.run_cli("response", "--dispatch", source,
                                      "--outcome", "ok", "--out", out)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(out.exists())
                self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
