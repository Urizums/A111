#!/usr/bin/env python3
"""GitHub-checkout R24 preflight on the 18 genuine C13/C14-lean Markdown files.

This is a deterministic source/copy/CLI check. It does not launch an Agent,
attest an OS sandbox, establish a skill-read trace, or decide a version winner.
The working checkout and the actual source candidates are read-only.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from paired_experiment_v7_candidate import (
    ARMS, SKILLS, check_frozen, git_blob_identity, md_files, read,
    verify_source_catalog,
)

REPO = Path(__file__).resolve().parents[3]
STUDY = Path(__file__).resolve().parent
CATALOG = STUDY / "REAL-CANDIDATE-SOURCE-CATALOG.json"
TRUSTED_CATALOG_GIT_BLOB = "c8a6b611056a6e9ff68c6de8f91095b9ddcdf5b0"
# Public smoke seeds deliberately cover both arm assignments. Not blind trials.
SMOKES = ((12345, "extract", "C14-lean"), (314159, "reconcile", "C13"))


def insist(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(*args: object) -> dict:
    command = [sys.executable, str(STUDY / "paired_experiment_v7_candidate.py")]
    command.extend(str(arg) for arg in args)
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True,
                            check=False, timeout=90)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "candidate CLI returned non-JSON stdout (last 500 chars): "
            + result.stdout[-500:] + " stderr: " + result.stderr[-500:]
        ) from exc
    return {"exit_code": result.returncode, "output": payload}


def run() -> dict:
    # Pin catalog identity outside the candidate metadata; fail before trials.
    insist(git_blob_identity(CATALOG.read_bytes()) == TRUSTED_CATALOG_GIT_BLOB,
           "trusted source catalog has changed")
    verified = verify_source_catalog(REPO, CATALOG, TRUSTED_CATALOG_GIT_BLOB)
    insist(verified["source_files_checked"] == 18, "expected 18 original Markdown files")
    insist(all(len(md_files(REPO / path)) == 9 for path in SKILLS.values()),
           "expected nine original Markdown files per candidate")
    results = []
    with tempfile.TemporaryDirectory(prefix="r24-genuine-checkout-") as temporary:
        temp = Path(temporary)
        for seed, kind, expected_arm_a in SMOKES:
            trial = temp / f"{kind}-{seed}"
            preparation = invoke(
                "prepare", "--repo", REPO, "--kind", kind, "--seed", seed,
                "--out", trial, "--source-catalog", CATALOG,
                "--trusted-catalog-git-blob", TRUSTED_CATALOG_GIT_BLOB,
            )
            insist(preparation["exit_code"] == 0,
                   f"real-source CLI prepare failed: {kind}: {preparation}")
            insist(preparation["output"]["status"] == "prepared_not_executed",
                   "prepare claimed model execution")
            freeze_path = trial / "reviewer_private/freeze.json"
            freeze = read(freeze_path)
            insist(freeze["schema"] == "forge-r24-paired-trial/5",
                   "trial is not bound to V7 source protocol")
            insist(freeze["source_verification"] == verified,
                   "trial does not preserve trusted source verification")
            assignment = {arm: freeze["arm_snapshots"][arm]["variant"] for arm in ARMS}
            insist(assignment["arm_a"] == expected_arm_a, "expected permutation not exercised")
            insist(set(assignment.values()) == set(SKILLS), "duplicate or missing variant")
            for arm, variant in assignment.items():
                insist(not check_frozen(trial, arm, freeze),
                       f"copied {arm} fails frozen file/entry checks")
                actual = {}
                for original in md_files(trial / "participants" / arm / "skill"):
                    relative = original.relative_to(trial / "participants" / arm / "skill").as_posix()
                    actual[relative] = hashlib.sha256(original.read_bytes()).hexdigest()
                insist(actual == verified["attested_variant_sha256"][variant],
                       "copied Skill bytes differ from trusted original")
                insist(not (trial / "participants" / arm / "submission").exists(),
                       "preparation fabricated a worker submission")
                insist(not (trial / "participants" / arm / "reviewer_private").exists(),
                       "private reviewer material leaked into participant packet")
            frozen_sha256 = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
            insist(frozen_sha256 == preparation["output"]["freeze_sha256_for_external_trusted_log"],
                   "CLI freeze digest does not match actual bytes")
            grade = invoke(
                "grade", "--trial", trial, "--receipt", temp / f"missing-{kind}.json",
                "--trusted-freeze-sha256", frozen_sha256,
            )
            insist(grade["exit_code"] == 2, "empty worker submissions were accepted")
            insist(grade["output"]["artifact_checks_passed"] is False, "missing deliverables passed")
            insist(grade["output"]["winner"] is None, "CLI invented a candidate winner")
            insist(grade["output"]["independent_review"] == "not_run",
                   "CLI claimed independent review")
            results.append({
                "kind": kind, "seed": seed, "arm_assignment": assignment,
                "copied_skill_files_checked": sum(len(v["skill_sha256"])
                                                  for v in freeze["arm_snapshots"].values()),
                "freeze_sha256": frozen_sha256,
                "empty_submission_rejected": True,
            })

        # Negative test uses a disposable copy, never mutates real source files.
        shadow = temp / "disposable-repo"
        for relative in SKILLS.values():
            shutil.copytree(REPO / relative, shadow / relative)
        changed = shadow / SKILLS["C13"] / "SKILL.md"
        changed.write_bytes(changed.read_bytes() + b"\nTAMPERED-FOR-NEGATIVE-TEST\n")
        rejected = False
        try:
            verify_source_catalog(shadow, CATALOG, TRUSTED_CATALOG_GIT_BLOB)
        except ValueError:
            rejected = True
        insist(rejected, "tampered genuine Skill copy passed source attestation")
    return {
        "schema": "forge-r24-genuine-checkout-preflight/1",
        "result": "pass",
        "catalog_git_blob": TRUSTED_CATALOG_GIT_BLOB,
        "genuine_source_markdown_files_checked": verified["source_files_checked"],
        "real_python_prepare_cases": len(results),
        "cases": results,
        "disposable_mutated_original_rejected": True,
        "actor_runs": 0,
        "independent_receiver_runs": 0,
        "comparison_winner": None,
        "boundary": "real checkout and CLI tested; independent Agent and host isolation not tested",
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"result": "fail", "error": type(exc).__name__ + ": " + str(exc)},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from exc
