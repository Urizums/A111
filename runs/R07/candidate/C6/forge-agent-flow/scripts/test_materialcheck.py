#!/usr/bin/env python3
"""Fixture tests for the conservative material identity gate."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import materialcheck


SCRIPT = Path(__file__).with_name("materialcheck.py")


def write_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def artifact(path, role, digest, *, identity="org.example.demo", stack="flutter", platform="android"):
    result = {
        "path": path,
        "sha256": digest,
        "role": role,
        "identity": identity,
        "stack": stack,
        "platform": platform,
    }
    if role == "target_source":
        result["fingerprint_scope"] = "complete_source_snapshot"
    return result


def source_only_manifest(source):
    return {
        "schema": "forge-materials/1",
        "intent": "source_only",
        "source": source,
        "binary": None,
        "references": [],
        "provenance": None,
    }


class MaterialCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_manifest(self, data, name="manifest.json"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def make_binary_source(self, directory=None, *, source_identity="org.example.demo",
                           binary_identity="org.example.demo", provenance=True):
        directory = directory or self.root
        source_hash = write_file(directory / "source-snapshot.zip", b"fixed source snapshot bytes")
        binary_hash = write_file(directory / "app.apk", b"binary package bytes")
        evidence_ref = None
        if provenance:
            record = {
                "schema": "forge-provenance/1",
                "kind": "build_provenance",
                "source_sha256": source_hash,
                "binary_sha256": binary_hash,
                "issuer": "fixture-build-system",
            }
            evidence_bytes = json.dumps(record, sort_keys=True).encode()
            evidence_hash = write_file(directory / "provenance.json", evidence_bytes)
            evidence_ref = {"path": "provenance.json", "sha256": evidence_hash}
        manifest = {
            "schema": "forge-materials/1",
            "intent": "binary_source",
            "source": artifact("source-snapshot.zip", "target_source", source_hash, identity=source_identity),
            "binary": artifact("app.apk", "target_binary", binary_hash, identity=binary_identity),
            "references": [],
            "provenance": evidence_ref,
        }
        return manifest

    def test_explicit_source_only_allows_modify_without_binary_or_sdk(self):
        digest = write_file(self.root / "source-snapshot.zip", b"source only")
        path = self.make_manifest(source_only_manifest(artifact("source-snapshot.zip", "target_source", digest)))
        result = materialcheck.assess(path)
        self.assertTrue(result["valid"])
        self.assertEqual(result["allowed_operations"], ["inspect", "design", "modify"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(materialcheck.require_valid(path)["intent"], "source_only")

    def test_same_application_identity_does_not_prove_build_relationship(self):
        path = self.make_manifest(self.make_binary_source(provenance=False))
        result = materialcheck.assess(path)
        self.assertTrue(result["valid"])
        self.assertEqual(result["allowed_operations"], ["inspect", "design"])
        self.assertTrue(any("provenance" in reason for reason in result["blockers"]))

    def test_bound_provenance_and_matching_identity_allow_modify(self):
        path = self.make_manifest(self.make_binary_source())
        result = materialcheck.assess(path)
        self.assertTrue(result["valid"])
        self.assertEqual(result["allowed_operations"], ["inspect", "design", "modify"])

    def test_conflicting_identity_blocks_modify_but_allows_design(self):
        path = self.make_manifest(self.make_binary_source(binary_identity="org.example.other"))
        result = materialcheck.assess(path)
        self.assertTrue(result["valid"])
        self.assertEqual(result["allowed_operations"], ["inspect", "design"])
        self.assertTrue(any("conflict" in reason for reason in result["blockers"]))

    def test_unknown_identity_blocks_modify_but_allows_design(self):
        path = self.make_manifest(self.make_binary_source(source_identity="unknown"))
        result = materialcheck.assess(path)
        self.assertTrue(result["valid"])
        self.assertEqual(result["allowed_operations"], ["inspect", "design"])
        self.assertTrue(any("unknown" in reason for reason in result["blockers"]))
        self.assertEqual(materialcheck.require_valid(path)["intent"], "binary_source")

    def test_actual_file_hash_mismatch_blocks_every_operation(self):
        digest = write_file(self.root / "source-snapshot.zip", b"original")
        data = source_only_manifest(artifact("source-snapshot.zip", "target_source", digest))
        path = self.make_manifest(data)
        write_file(self.root / "source-snapshot.zip", b"changed")
        result = materialcheck.assess(path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["allowed_operations"], [])
        with self.assertRaises(materialcheck.MaterialError):
            materialcheck.require_valid(path)

    def test_single_configuration_file_cannot_stand_for_source_tree(self):
        digest = write_file(self.root / "pubspec.yaml", b"name: app")
        data = source_only_manifest(artifact("pubspec.yaml", "target_source", digest))
        path = self.make_manifest(data)
        result = materialcheck.assess(path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["allowed_operations"], [])
        self.assertTrue(any("archive file" in reason for reason in result["blockers"]))

    def test_reference_role_cannot_be_selected_as_target_source(self):
        digest = write_file(self.root / "source-snapshot.zip", b"source")
        data = source_only_manifest(artifact("source-snapshot.zip", "reference_source", digest))
        path = self.make_manifest(data)
        result = materialcheck.assess(path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["allowed_operations"], [])

    def test_provenance_must_bind_both_actual_fingerprints(self):
        data = self.make_binary_source()
        record = {
            "schema": "forge-provenance/1",
            "kind": "authoritative_record",
            "source_sha256": "0" * 64,
            "binary_sha256": data["binary"]["sha256"],
            "issuer": "fixture-authority",
        }
        evidence = json.dumps(record, sort_keys=True).encode()
        evidence_hash = write_file(self.root / "provenance.json", evidence)
        data["provenance"] = {"path": "provenance.json", "sha256": evidence_hash}
        result = materialcheck.assess(self.make_manifest(data))
        self.assertEqual(result["allowed_operations"], ["inspect", "design"])
        self.assertTrue(any("does not bind" in reason for reason in result["blockers"]))

    def test_cli_exit_status_distinguishes_modify_from_blocked(self):
        allowed_dir = self.root / "allowed"
        blocked_dir = self.root / "blocked"
        allowed = self.make_manifest(self.make_binary_source(allowed_dir), "allowed/manifest.json")
        blocked = self.make_manifest(
            self.make_binary_source(blocked_dir, provenance=False), "blocked/manifest.json"
        )
        allowed_run = subprocess.run([sys.executable, str(SCRIPT), str(allowed)], capture_output=True, text=True)
        blocked_run = subprocess.run([sys.executable, str(SCRIPT), str(blocked)], capture_output=True, text=True)
        self.assertEqual(allowed_run.returncode, 0, allowed_run.stdout + allowed_run.stderr)
        self.assertEqual(blocked_run.returncode, 2)
        self.assertEqual(json.loads(blocked_run.stdout)["status"], "blocked")

    def test_malformed_manifest_fails_closed(self):
        path = self.root / "malformed.json"
        path.write_text('{"schema":"forge-materials/1","schema":"forge-materials/1"}', encoding="utf-8")
        result = materialcheck.assess(path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["allowed_operations"], [])
        cli = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
        self.assertEqual(cli.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO fixtures require POSIX")
    def test_fifo_manifest_is_rejected_without_blocking(self):
        path = self.root / "manifest.fifo"
        os.mkfifo(path)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True, timeout=2
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["allowed_operations"], [])


if __name__ == "__main__":
    unittest.main()
