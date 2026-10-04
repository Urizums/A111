"""Focused tests for the loss-preserving legacy design importer."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import import_cluster


def design_fixture() -> dict:
    """Small legacy input that keeps these unit tests self-contained."""
    return {
        "schema": import_cluster.LEGACY_SCHEMA,
        "name": "minimal fixture",
        "roles": [
            {
                "id": "extractor",
                "prompt": "Read the supplied files and extract their key facts.",
                "model_level": "gpt-6-luna",
                "tools": ["read_file", {"name": "search", "scope": "workspace"}],
                "write_scope": {"paths": ["/workspace/output"], "allow_delete": False},
                "budget": {"max_tokens": 1200, "max_tool_calls": 4},
            },
            {
                "id": "reviewer",
                "prompt": "Check the extracted facts against the source.",
                "model_level": "gpt-6-luna",
                "tools": ["read_file"],
                "write_scope": {"paths": [], "allow_delete": False},
                "budget": {"max_tokens": 800, "max_tool_calls": 2},
            },
        ],
        "guards": [
            {"id": "source_only", "rule": "Use only supplied source material", "mode": "block"}
        ],
        "hitl_gates": [{"id": "publish", "when": "before_publish", "required": True}],
        "concurrency": {
            "max_parallel": 3,
            "hard_cap": 6,
            "sizing_inputs": {
                "expected_roles": 2,
                "peak_tasks_per_role": {"extractor": 2, "reviewer": 1},
                "operator_note": "Retain this source estimate verbatim.",
            },
        },
    }


class InspectDesignTests(unittest.TestCase):
    def test_design_remains_a_translation_brief(self) -> None:
        source = design_fixture()
        brief = import_cluster.inspect_design(source)
        self.assertEqual(brief["schema"], "forge/legacy-brief/1")
        self.assertEqual(brief["status"], "needs_translation")
        self.assertEqual(brief["source_design"], source)
        self.assertEqual(len(brief["roles"]), len(source["roles"]))
        self.assertTrue(brief["source_hash"].isalnum())
        self.assertEqual(len(brief["source_hash"]), 64)
        self.assertTrue(any("typed artifacts" in item for item in brief["unresolved"]))
        self.assertTrue(any("serial host-driven" in item for item in brief["unresolved"]))
        self.assertTrue(any("has not been validated" in item for item in brief["unresolved"]))

    def test_complete_policy_and_prompt_fields_are_preserved(self) -> None:
        source = design_fixture()
        brief = import_cluster.inspect_design(source)
        for original, imported in zip(source["roles"], brief["roles"]):
            self.assertEqual(
                {key: value for key, value in imported.items() if key != "proposed_node_id"},
                original,
            )
        self.assertEqual(brief["source_design"]["guards"], source["guards"])
        self.assertEqual(brief["source_design"]["hitl_gates"], source["hitl_gates"])
        self.assertEqual(brief["source_design"]["concurrency"]["sizing_inputs"],
                         source["concurrency"]["sizing_inputs"])
        self.assertEqual(brief["source_design"]["concurrency"]["hard_cap"],
                         source["concurrency"]["hard_cap"])
        self.assertTrue(all("prompt" in role and "model_level" in role and "tools" in role
                            and "write_scope" in role and "budget" in role for role in brief["roles"]))
        self.assertNotIn("nodes", brief)
        self.assertNotIn("entry", brief)

    def test_unknown_source_keys_are_retained_and_input_is_not_mutated(self) -> None:
        source = design_fixture()
        source["future_policy_extension"] = {"opaque": [1, "value"]}
        original = copy.deepcopy(source)
        brief = import_cluster.inspect_design(source)
        self.assertEqual(source, original)
        self.assertEqual(brief["source_design"], original)

    def test_duplicate_role_id_rejected(self) -> None:
        source = design_fixture()
        source["roles"].append(copy.deepcopy(source["roles"][0]))
        with self.assertRaisesRegex(import_cluster.ImportDesignError, "Duplicate role ID"):
            import_cluster.inspect_design(source)

    def test_normalized_id_collision_rejected(self) -> None:
        source = design_fixture()
        source["roles"][1]["id"] = "EXTRACTOR"
        with self.assertRaisesRegex(import_cluster.ImportDesignError, "collide after normalization"):
            import_cluster.inspect_design(source)

    def test_source_proposed_node_id_is_rejected_without_mutation(self) -> None:
        source = design_fixture()
        source["roles"][0]["proposed_node_id"] = "source_owned_value"
        original = copy.deepcopy(source)
        with self.assertRaisesRegex(
            import_cluster.ImportDesignError,
            r"roles\[0\]\.proposed_node_id is reserved by the importer",
        ):
            import_cluster.inspect_design(source)
        self.assertEqual(source, original)

    def test_path_traversal_and_invalid_required_structure_rejected(self) -> None:
        source = design_fixture()
        source["roles"][0]["id"] = "../extractor"
        with self.assertRaisesRegex(import_cluster.ImportDesignError, "Unsafe role ID"):
            import_cluster.inspect_design(source)
        for malformed in ({"schema": import_cluster.LEGACY_SCHEMA},
                          {"schema": import_cluster.LEGACY_SCHEMA, "roles": []},
                          {"roles": [{"id": "worker"}]}):
            with self.subTest(malformed=malformed):
                with self.assertRaises(import_cluster.ImportDesignError):
                    import_cluster.inspect_design(malformed)

    def test_non_finite_python_values_rejected(self) -> None:
        source = design_fixture()
        source["unexpected_numeric_extension"] = float("inf")
        with self.assertRaisesRegex(import_cluster.ImportDesignError, "non-finite"):
            import_cluster.inspect_design(source)


class CliTests(unittest.TestCase):
    def run_cli(self, raw: str, out: Path) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.json"
            source.write_text(raw, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(Path(import_cluster.__file__)), str(source), "--out", str(out)],
                text=True, capture_output=True, check=False,
            )

    def test_duplicate_json_keys_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "brief.json"
            result = self.run_cli(
                '{"schema":"cluster-architect/design/1","schema":"cluster-architect/design/1","roles":[]}',
                out,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Duplicate JSON object key", result.stderr)
            self.assertFalse(out.exists())

    def test_malformed_and_nonfinite_json_rejected_without_output(self) -> None:
        for raw, expected in (("{oops", "valid JSON"),
                              ('{"schema":"cluster-architect/design/1","roles":[],"x":NaN}',
                               "Non-finite JSON"),
                              ('{"schema":"cluster-architect/design/1","roles":[],"x":1e999}',
                               "non-finite")):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as temp:
                out = Path(temp) / "brief.json"
                result = self.run_cli(raw, out)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected.lower(), result.stderr.lower())
                self.assertFalse(out.exists())

    def test_existing_output_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "brief.json"
            out.write_text("keep me", encoding="utf-8")
            design = json.dumps({"schema": import_cluster.LEGACY_SCHEMA, "roles": [{"id": "worker"}]})
            result = self.run_cli(design, out)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(out.read_text(encoding="utf-8"), "keep me")


if __name__ == "__main__":
    unittest.main()
