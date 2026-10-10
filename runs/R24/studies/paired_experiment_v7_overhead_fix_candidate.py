#!/usr/bin/env python3
"""Prepare and score a paired C13/C14-lean study without invoking model agents.

The runtime MUST mount only the selected participant directory for each worker,
withhold private/, and isolate contexts, tools, histories and receipts. Merely
creating subdirectories is NOT a security boundary or an independent AI trial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import random
import subprocess
import shutil
import stat
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = {"arm_a": "C13", "arm_b": "C14-lean"}
SKILLS = {
    "C13": "runs/R20/final/candidate/C13/forge-agent-flow",
    "C14-lean": "runs/R24/candidate/C14-lean/forge-agent-flow",
}
MAX_FILE = 2 * 1024 * 1024


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read(path: Path) -> dict:
    def no_duplicate(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field: " + key)
            result[key] = value
        return result
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object: " + str(path))
    return data


def safe_bytes(path: Path, base: Path) -> bytes:
    if path.is_symlink() or base.is_symlink() or not path.is_relative_to(base) or not path.resolve().is_relative_to(base.resolve()):
        raise ValueError("symlink/out-of-root source: " + str(path))
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
        raise ValueError("unbounded or non-regular file: " + str(path))
    return path.read_bytes()


def md_files(directory: Path) -> list[Path]:
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("missing Skill directory: " + str(directory))
    files = sorted(directory.rglob("*.md"))
    if not files or not (directory / "SKILL.md").is_file():
        raise ValueError("Skill must provide SKILL.md")
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError("symbolic Skill entry: " + str(path))
    for path in files:
        safe_bytes(path, directory)
    return files


def copy_skill(src: Path, destination: Path) -> dict:
    files = md_files(src)
    copied = {}
    for f in files:
        relative = f.relative_to(src)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = safe_bytes(f, src)
        data.decode("utf-8", errors="strict")
        target.write_bytes(data)
        copied[relative.as_posix()] = sha(target)
    return copied


def git_blob_identity(data: bytes) -> str:
    """Match `git hash-object` without needing Git or network access."""
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def verify_source_catalog(repo: Path, catalog_path: Path,
                          trusted_catalog_blob: str) -> dict:
    """Fail before trial creation unless 18 real Skill blobs match a pinned catalog.

    The expected catalog blob must come from a trusted location OUTSIDE
    the participant and the mutable trial workspace.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", trusted_catalog_blob):
        raise ValueError("trusted catalog Git Blob identity must be 40 hex characters")
    data = safe_bytes(catalog_path, catalog_path.parent)
    if git_blob_identity(data) != trusted_catalog_blob:
        raise ValueError("candidate catalog differs from externally trusted Git Blob")
    catalog = read(catalog_path)
    if catalog.get("schema") != "forge-r24-real-candidate-source-catalog/1":
        raise ValueError("unknown or invalid candidate source catalog")
    if catalog.get("source_repo") != "Urizums/A111":
        raise ValueError("wrong candidate source repository")
    if not re.fullmatch(r"[0-9a-f]{40}", str(catalog.get("source_commit", ""))):
        raise ValueError("source commit is not a pinned Git SHA")
    variants = catalog.get("candidates")
    if not isinstance(variants, dict) or set(variants) != set(SKILLS):
        raise ValueError("candidate catalog missing or unexpected variants")
    compared = 0
    attested_variant_sha256 = {}
    for variant, dirname in SKILLS.items():
        entry = variants[variant]
        if not isinstance(entry, dict) or entry.get("root") != dirname:
            raise ValueError("candidate root differs from source catalog: " + variant)
        expected = entry.get("file_blobs")
        if not isinstance(expected, dict) or not expected or not all(
            isinstance(k, str) and isinstance(v, str) and re.fullmatch(r"[0-9a-f]{40}", v)
            for k, v in expected.items()
        ):
            raise ValueError("invalid source file blob map: " + variant)
        source = repo / dirname
        files = md_files(source)
        found = {f.relative_to(source).as_posix(): f for f in files}
        if set(found) != set(expected) or entry.get("file_count") != len(found):
            raise ValueError("candidate file coverage differs from audited source: " + variant)
        attested_variant_sha256[variant] = {}
        for rel, file in found.items():
            raw = safe_bytes(file, source)
            if git_blob_identity(raw) != expected[rel]:
                raise ValueError("candidate source blob mismatch: " + variant + "/" + rel)
            attested_variant_sha256[variant][rel] = hashlib.sha256(raw).hexdigest()
        compared += len(found)
    return {"catalog_git_blob": trusted_catalog_blob,
            "catalog_source_commit": catalog["source_commit"],
            "source_files_checked": compared,
            "attested_variant_sha256": attested_variant_sha256,
            "source_code_checks": "actual Git Blob bytes; host permissions and independent reading not attested"}


def make_simple(seed: int, case: Path) -> None:
    rng = random.Random(seed)
    cities = ["杭州", "苏州", "武汉", "厦门", "青岛", "成都"]
    public, private = case / "producer", case / "private"
    public.mkdir(parents=True)
    private.mkdir()
    data = {"ticket": f"T-{rng.randrange(10000, 99999)}", "city": rng.choice(cities),
            "deadline": f"2027-{rng.randrange(1,13):02}-{rng.randrange(1,29):02}",
            "remarks": "Only city and deadline are requested."}
    dump(public / "source.json", data)
    (public / "task.md").write_text(
        "请根据 source.json 给出该工单的城市和截止日期。输出 answer.json，"
        "字段为 city 与 deadline。请核对原件并直接交付结果。\n", encoding="utf-8")
    dump(private / "expected.json", {"city": data["city"], "deadline": data["deadline"]})


def make_reconcile(seed: int, case: Path) -> None:
    sys.path.insert(0, str(HERE / "reconciliation"))
    from rehearsal import generate
    generate(seed, case)


def prepare(repo: Path, kind: str, seed: int, out: Path, source_verification: dict | None = None) -> dict:
    if out.exists() or out.is_symlink():
        raise FileExistsError("trial root already exists, cannot overwrite")
    if kind not in ("extract", "reconcile"):
        raise ValueError("unsupported task kind")
    source_dirs = {variant: repo / relative for variant, relative in SKILLS.items()}
    # Verify candidates completely before creating case or trial directories.
    for directory in source_dirs.values():
        md_files(directory)
    # Preflight is a claim about specific bytes, not permission to later copy
    # whatever happens to occupy the same filenames.
    expected_attested = (source_verification or {}).get("attested_variant_sha256")
    if not isinstance(expected_attested, dict) or set(expected_attested) != set(SKILLS):
        raise ValueError("prepare requires bound attested per-variant bytes")
    for variant, directory in source_dirs.items():
        actual = {p.relative_to(directory).as_posix():
                  hashlib.sha256(safe_bytes(p, directory)).hexdigest()
                  for p in md_files(directory)}
        if actual != expected_attested[variant]:
            raise ValueError("candidate bytes changed after catalog preflight: " + variant)
    out.mkdir(parents=True)
    case = out / "reviewer_private" / "case"
    if kind == "extract":
        make_simple(seed, case)
    else:
        make_reconcile(seed, case)
    originals = case / "producer"
    source_hashes = {f.name: sha(f) for f in originals.iterdir() if f.is_file()}
    private_files = case / "private"
    expected_oracle = {"expected.json"} if kind == "extract" else {"oracle.json"}
    if {f.name for f in private_files.iterdir()} != expected_oracle:
        raise ValueError("private oracle contents are not the expected minimal set")
    oracle_hashes = {f.name: sha(f) for f in private_files.iterdir() if f.is_file()}
    # Freeze source identities by *variant*, independently of randomized arm labels.
    # The previous implementation copied by arm, which silently mislabelled swapped trials.
    variant_sources = {
        variant: {p.relative_to(directory).as_posix(): sha(p)
                  for p in md_files(directory)}
        for variant, directory in source_dirs.items()
    }
    if variant_sources != expected_attested:
        raise ValueError("candidate sources changed during trial preparation")
    variants = list(SKILLS)
    random.Random(seed ^ 0xF06E).shuffle(variants)
    assignment = dict(zip(ARMS, variants))
    arms = {}
    for arm, version in assignment.items():
        dst = out / "participants" / arm
        src = dst / "task"
        src.mkdir(parents=True)
        for name in sorted(source_hashes):
            f = originals / name
            dst_file = src / name
            dst_file.write_bytes(safe_bytes(f, originals))
        skills = copy_skill(source_dirs[version], dst / "skill")
        if skills != variant_sources[version]:
            raise ValueError("copied Skill differs from declared variant source: " + version)
        (dst / "START_HERE.md").write_text(
            "执行前请完整阅读 skill/SKILL.md；其 references/ 文件按本任务实际需要选读，"
            "不要求机械执行其中每一个示例。请完成 task/ 中用户要求的真实交付，"
            "只在 submission/ 中写成果；不要访问其他参与者或评分材料。"
            "用实际材料核对结果。阅读是否发生必须由执行宿主轨迹另行证实；"
            "此说明本身不是已阅读或独立性证明。\n", encoding="utf-8")
        arms[arm] = {"variant": version, "skill_sha256": skills,
                     "start_sha256": sha(dst / "START_HERE.md")}
    manifest = {
        "schema": "forge-r24-paired-trial/5", "status": "prepared_not_executed",
        "protocol": "skill_entry_read_required/1",
        "source_verification": source_verification,
        "task_kind": kind, "seed": seed, "source_sha256": source_hashes,
        "oracle_sha256": oracle_hashes,
        "variant_source_sha256": variant_sources,
        "arm_snapshots": arms,
        "note": "Only an actual host can hide reviewer_private and opposite participant roots."
    }
    freeze_path = out / "reviewer_private" / "freeze.json"
    dump(freeze_path, manifest)
    return {"status": "prepared_not_executed", "arms": list(arms), "kind": kind,
            "freeze_sha256_for_external_trusted_log": sha(freeze_path),
            "private_oracle": "reviewer_private must never be mounted in a worker context",
            "source_catalog_verified": source_verification is not None,
            "worker_input_dirs": [str(out / "participants" / arm) for arm in ARMS]}


def check_frozen(out: Path, arm: str, freeze: dict) -> list[str]:
    worker = out / "participants" / arm
    errors = []
    # The participant root and frozen directories must be real directories,
    # not symlinks to reviewer-side material or another participant.
    for directory in (worker, worker / "task", worker / "skill"):
        if directory.is_symlink() or not directory.is_dir():
            return ["missing or unsafe frozen input directory: " + directory.name]
    expected_task = freeze["source_sha256"]
    expected_skill = freeze["arm_snapshots"][arm]["skill_sha256"]
    # A frozen file list is not enough: hidden extra directories and directory
    # symlinks can expose reviewer-private materials without changing the
    # names/hashes of the expected files. Check all input paths, including dirs.
    for entry in worker.iterdir():
        if entry.name not in {"task", "skill", "START_HERE.md", "submission"}:
            errors.append("unfrozen participant-root entry: " + entry.name)
    for label, expected_files in (("task", expected_task), ("skill", expected_skill)):
        root = worker / label
        expected_dirs = set()
        for relative in expected_files:
            parts = Path(relative).parts
            for i in range(1, len(parts)):
                expected_dirs.add(Path(*parts[:i]).as_posix())
        for entry in root.rglob("*"):
            relative = entry.relative_to(root).as_posix()
            if entry.is_symlink():
                errors.append("symbolic frozen input: " + label + "/" + relative)
            elif entry.is_dir():
                if relative not in expected_dirs:
                    errors.append("unfrozen input directory: " + label + "/" + relative)
            elif entry.is_file():
                if relative not in expected_files:
                    errors.append("unfrozen input file: " + label + "/" + relative)
            else:
                errors.append("nonregular frozen input: " + label + "/" + relative)
    task_files = {f.name for f in (worker / "task").iterdir() if f.is_file()}
    skill_files = {f.relative_to(worker / "skill").as_posix()
                   for f in (worker / "skill").rglob("*") if f.is_file()}
    if task_files != set(expected_task):
        errors.append("task file coverage changed")
    if skill_files != set(expected_skill):
        errors.append("Skill file coverage changed")
    checks = [(worker / "task" / n, d) for n, d in expected_task.items()]
    checks += [(worker / "skill" / n, d) for n, d in expected_skill.items()]
    checks += [(worker / "START_HERE.md", freeze["arm_snapshots"][arm]["start_sha256"])]
    for f, expected in checks:
        try:
            if f.is_symlink() or not f.is_file() or sha(f) != expected:
                errors.append("frozen input mismatch: " + f.name)
        except OSError:
            errors.append("frozen file unreadable: " + f.name)
    return errors




def check_submission(sub: Path, required_names: set[str]) -> list[str]:
    """Reject unsafe output aliases, not ordinary extra reports.

    The host still must hide private inputs; this local guard is not isolation.
    """
    if sub.is_symlink() or not sub.is_dir():
        return ["missing or invalid submission directory"]
    errors = []
    # A symlink anywhere under submission is unacceptable, even if optional.
    # This includes symlinked directories pointing outside the participant.
    for item in sub.rglob("*"):
        if item.is_symlink():
            errors.append("submission contains symbolic link: " + item.relative_to(sub).as_posix())
        elif item.is_file():
            try:
                info = item.stat()
                if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
                    errors.append("submission has oversized/nonregular file: " + item.relative_to(sub).as_posix())
            except OSError:
                errors.append("submission file unreadable: " + item.relative_to(sub).as_posix())
    for name in required_names:
        item = sub / name
        if item.is_symlink() or not item.is_file():
            errors.append("missing or unsafe required output: " + name)
    return errors

def grade(out: Path, receipt: Path, trusted_freeze_sha256: str | None = None) -> dict:
    if receipt.exists() or receipt.is_symlink():
        raise FileExistsError("refusing to overwrite an earlier grading receipt")
    if trusted_freeze_sha256 is not None and sha(out / "reviewer_private" / "freeze.json") != trusted_freeze_sha256:
        raise ValueError("frozen study manifest differs from externally retained digest")
    freeze = read(out / "reviewer_private" / "freeze.json")
    if freeze.get("schema") != "forge-r24-paired-trial/5":
        raise ValueError("unpinned or unknown trial protocol; previous formats cannot attest real candidate source identity")
    if freeze.get("protocol") != "skill_entry_read_required/1":
        raise ValueError("required Skill exposure protocol is not frozen")
    if freeze.get("status") != "prepared_not_executed":
        raise ValueError("unrecognized frozen trial status")
    evidence = freeze.get("source_verification")
    if not isinstance(evidence, dict) or not re.fullmatch(r"[0-9a-f]{40}",
                            str(evidence.get("catalog_git_blob", ""))):
        raise ValueError("paired trial missing externally attested source catalog")
    if not isinstance(evidence.get("source_files_checked"), int) or evidence["source_files_checked"] < 2:
        raise ValueError("source catalog evidence is incomplete")
    if not isinstance(evidence.get("attested_variant_sha256"), dict):
        raise ValueError("source attestation does not bind future copied bytes")
    # Check attribution independently of the participant's artifact contents.
    variant_sources = freeze.get("variant_source_sha256")
    snapshots = freeze.get("arm_snapshots")
    if not isinstance(variant_sources, dict) or set(variant_sources) != set(SKILLS):
        raise ValueError("missing version-labelled Skill source hashes")
    if variant_sources != evidence["attested_variant_sha256"]:
        raise ValueError("copied candidate files are not the attested source identities")
    if not isinstance(snapshots, dict) or set(snapshots) != set(ARMS):
        raise ValueError("incorrect number of study arms")
    declared_versions = [snapshots[arm]["variant"] for arm in ARMS]
    if set(declared_versions) != set(SKILLS):
        raise ValueError("both distinct candidates must be represented")
    for arm in ARMS:
        snapshot = snapshots[arm]
        if snapshot["skill_sha256"] != variant_sources[snapshot["variant"]]:
            raise ValueError("arm Skill hashes do not match its declared candidate: " + arm)
    kind = freeze["task_kind"]
    source_case = out / "reviewer_private/case/producer"
    private_case = out / "reviewer_private/case/private"
    for name, digest in freeze["source_sha256"].items():
        if sha(source_case / name) != digest:
            raise ValueError("reviewer-side task source modified since freeze: " + name)
    for name, digest in freeze["oracle_sha256"].items():
        if sha(private_case / name) != digest:
            raise ValueError("reviewer-side private oracle modified since freeze: " + name)
    results = {}
    expected_names = {"answer.json"} if kind == "extract" else {"ledger.csv", "suppliers.csv", "workflow.md"}
    for arm in ARMS:
        worker = out / "participants" / arm
        problems = check_frozen(out, arm, freeze)
        sub = worker / "submission"
        submission_issues = check_submission(sub, expected_names)
        score = {"passed": False, "details": None}
        if not problems and not submission_issues:
            if kind == "extract":
                try:
                    actual = read(sub / "answer.json")
                    expected = read(out / "reviewer_private/case/private/expected.json")
                    score = {"passed": set(actual) == set(expected) and actual == expected,
                             "details": "two source-derived fields checked"}
                except (OSError, ValueError, json.JSONDecodeError):
                    score = {"passed": False, "details": "answer.json unreadable or ambiguous"}
            else:
                sys.path.insert(0, str(HERE / "reconciliation"))
                from rehearsal import grade as grade_reconcile
                check = grade_reconcile(out / "reviewer_private/case", sub)
                score = {"passed": check["data_artifacts_passed"] and check["workflow_present"],
                         "data_passed": check["data_artifacts_passed"],
                         "workflow_semantic_usability": check["workflow_usability"],
                         "errors": check["errors"]}
        if problems or submission_issues:
            score["passed"] = False
        if sub.is_dir() and not sub.is_symlink():
            # Compare the entire extra output burden, not only the submission
            # root. Nested reports and empty folders must not evade overhead
            # reporting simply because required deliverables are correct.
            extra = sorted(
                rel + ("/" if item.is_dir() else "")
                for item in sub.rglob("*")
                for rel in [item.relative_to(sub).as_posix()]
                if (item.is_file() and rel not in expected_names)
                or (item.is_dir() and not any(item.iterdir()))
            )
        else:
            extra = []
        results[arm] = {"variant": freeze["arm_snapshots"][arm]["variant"],
                        "artifact_passed": score["passed"], "score_details": score,
                        "frozen_input_issues": problems, "submission_issues": submission_issues,
                        "nonrequired_artifacts": extra,
                        "independent_actor_verified": False}
    artifact_checks_passed = all(item["artifact_passed"] for item in results.values())
    response = {"schema": "forge-r24-paired-grade/5", "trial_schema": freeze["schema"], "task_kind": kind,
                "artifact_checks_passed": artifact_checks_passed,
                "cli_success_requires_external_freeze_and_all_artifacts": True,
                "cases_scored": len(results), "arms": results,
                "comparison_result": "not_established_no_independent_actor_receipts",
                "independent_review": "not_run", "winner": None,
                "skill_read_observed_in_independent_host_trace": False,
                "candidate_source_catalog_attested": True,
                "externally_frozen_manifest_checked": trusted_freeze_sha256 is not None,
                "note": "Self-scores do not establish C13/C14-lean causal effects, cost or semantic handoff."}
    dump(receipt, response)
    return response


def selftest() -> dict:
    checks = []
    def record(name, ok):
        checks.append({"name": name, "passed": bool(ok)})
    with tempfile.TemporaryDirectory(prefix="forge-r24-pair-") as tmp:
        root = Path(tmp)
        fake_repo = root / "repo"
        for name, skillpath in SKILLS.items():
            p = fake_repo / skillpath
            (p / "references").mkdir(parents=True)
            (p / "SKILL.md").write_text(f"---\nname: forge-agent-flow\ndescription: {name} trial\n---\n", encoding="utf-8")
            (p / "references" / "method.md").write_text("# Method\n", encoding="utf-8")
        catalog_path = root / "source-catalog.json"
        fixture_catalog = {"schema": "forge-r24-real-candidate-source-catalog/1",
                           "source_repo": "Urizums/A111", "source_commit": "0" * 40,
                           "candidates": {
                               version: {"root": dirname, "file_count": len(md_files(fake_repo / dirname)),
                                         "file_blobs": {str(f.relative_to(fake_repo / dirname)).replace("\\", "/"):
                                                        git_blob_identity(f.read_bytes()) for f in md_files(fake_repo / dirname)}}
                               for version, dirname in SKILLS.items()}}
        dump(catalog_path, fixture_catalog)
        catalog_git_sha = git_blob_identity(catalog_path.read_bytes())
        verified_sources = verify_source_catalog(fake_repo, catalog_path, catalog_git_sha)
        record("fixture candidate source catalog checked by exact Git Blob bytes",
               verified_sources["source_files_checked"] == 4)
        trial = root / "trial"
        prepare(fake_repo, "extract", 207, trial, verified_sources)
        freeze = read(trial / "reviewer_private/freeze.json")
        record("both candidates copied with distinct source identities", len(freeze["arm_snapshots"]) == 2 and
               {v["variant"] for v in freeze["arm_snapshots"].values()} == set(SKILLS))
        # Regression for the actual v1 bug: it permuted the *label* but always
        # copied fixed A=C13, B=C14-lean Skill files.  Both permutations are
        # required to prove this experiment cannot attribute results backwards.
        reversed_trials = 0
        direct_trials = 0
        for seed in range(20):
            candidate = root / ("permutation-" + str(seed))
            prepare(fake_repo, "extract", seed, candidate, verified_sources)
            frozen = read(candidate / "reviewer_private/freeze.json")
            assignment = {arm: frozen["arm_snapshots"][arm]["variant"] for arm in ARMS}
            if assignment["arm_a"] != "C13":
                reversed_trials += 1
            else:
                direct_trials += 1
            for arm, version in assignment.items():
                copied = candidate / "participants" / arm / "skill/SKILL.md"
                assert f"description: {version} trial" in copied.read_text(encoding="utf-8")
                assert frozen["arm_snapshots"][arm]["skill_sha256"] == frozen["variant_source_sha256"][version]
        record("both randomized assignments exercised and actual Skill contents match declared variant",
               reversed_trials > 0 and direct_trials > 0)
        record("new frozen trial format records actual source-by-variant identity",
               freeze.get("schema") == "forge-r24-paired-trial/5" and
               freeze["arm_snapshots"]["arm_a"]["skill_sha256"] ==
               freeze["variant_source_sha256"][freeze["arm_snapshots"]["arm_a"]["variant"]])
        record("required entry exposure protocol frozen",
               freeze.get("protocol") == "skill_entry_read_required/1")
        record("both arms receive identical read-SKILL-first instructions", all(
               "执行前请完整阅读 skill/SKILL.md" in (trial / "participants" / arm / "START_HERE.md").read_text(encoding="utf-8")
               and "references/ 文件按本任务实际需要选读" in (trial / "participants" / arm / "START_HERE.md").read_text(encoding="utf-8")
               for arm in ARMS))
        record("frozen experiment captures source catalog reference",
               freeze.get("source_verification") == verified_sources)
        record("source attestation includes all candidate byte SHA256 identities",
               verified_sources.get("attested_variant_sha256") == freeze.get("variant_source_sha256"))
        mutation_source = fake_repo / SKILLS["C13"] / "SKILL.md"
        changed_bytes = mutation_source.read_bytes()
        mutation_source.write_bytes(changed_bytes + b"\n")
        try:
            prepare(fake_repo, "extract", 9109, root / "preflight-stale-case", verified_sources)
            record("source edits between catalog preflight and trial preparation rejected", False)
        except ValueError:
            record("source edits between catalog preflight and trial preparation rejected",
                   not (root / "preflight-stale-case").exists())
        mutation_source.write_bytes(changed_bytes)
        expected_skill = fake_repo / SKILLS["C13"] / "SKILL.md"
        old_skill = expected_skill.read_bytes()
        expected_skill.write_bytes(old_skill + b" ")
        try:
            verify_source_catalog(fake_repo, catalog_path, catalog_git_sha)
            record("modified candidate source is rejected before new trial", False)
        except ValueError:
            record("modified candidate source is rejected before new trial", True)
        expected_skill.write_bytes(old_skill)
        try:
            verify_source_catalog(fake_repo, catalog_path, "f" * 40)
            record("untrusted catalog is refused", False)
        except ValueError:
            record("untrusted catalog is refused", True)
        extra = fake_repo / SKILLS["C14-lean"] / "references/unexpected.md"
        extra.write_text("# Extra", encoding="utf-8")
        try:
            verify_source_catalog(fake_repo, catalog_path, catalog_git_sha)
            record("extra candidate file is refused before trial", False)
        except ValueError:
            record("extra candidate file is refused before trial", True)
        extra.unlink()
        record("restored candidate sources re-attest", verify_source_catalog(fake_repo, catalog_path, catalog_git_sha) == verified_sources)
        record("private oracle hash frozen", bool(freeze["oracle_sha256"]))
        digest = sha(trial / "reviewer_private/freeze.json")
        record("external freeze token available", len(digest) == 64)
        record("both arms have identical original task bytes", all(
            sha(trial / "participants" / arm / "task/source.json") == freeze["source_sha256"]["source.json"] for arm in ARMS))
        record("private oracle absent from worker packet", all(
            not list((trial / "participants" / arm).rglob("expected.json")) for arm in ARMS))
        # The exact frozen file hashes alone would previously miss additional
        # directories, invisible directory links and root-level leaked notes.
        packet = trial / "participants" / "arm_a"
        record("clean complete frozen participant tree is accepted",
               not check_frozen(trial, "arm_a", freeze))
        hidden = packet / "task" / "hidden_context"
        hidden.mkdir()
        (hidden / "oracle.txt").write_text("private", encoding="utf-8")
        record("unlisted task subtree is rejected",
               any("unfrozen input" in issue for issue in check_frozen(trial, "arm_a", freeze)))
        (hidden / "oracle.txt").unlink()
        hidden.rmdir()
        link = packet / "skill" / "hidden_reviewer"
        try:
            link.symlink_to(trial / "reviewer_private", target_is_directory=True)
            record("directory symlink to reviewer material is rejected",
                   any("symbolic frozen input" in issue for issue in check_frozen(trial, "arm_a", freeze)))
            link.unlink()
        except (OSError, NotImplementedError):
            record("directory symlink to reviewer material is rejected", False)
        extra_root = packet / "author_note.md"
        extra_root.write_text("secret", encoding="utf-8")
        record("unfrozen participant root material is rejected",
               any("unfrozen participant-root" in issue for issue in check_frozen(trial, "arm_a", freeze)))
        extra_root.unlink()
        for arm in ARMS:
            output = trial / "participants" / arm / "submission"
            output.mkdir()
            source = read(trial / "participants" / arm / "task/source.json")
            dump(output / "answer.json", {"city": source["city"], "deadline": source["deadline"]})
        # A root-only overhead count used to miss nested bonus reports and
        # empty folders, biasing a C13/C14-lean workflow-cost comparison.
        extra_sub = trial / "participants/arm_a/submission"
        nested_extra = extra_sub / "unused-reports/appendix/long-notes.md"
        nested_extra.parent.mkdir(parents=True)
        nested_extra.write_text("Unnecessary process document", encoding="utf-8")
        empty_extra = extra_sub / "unused-empty-folder"
        empty_extra.mkdir()
        r = grade(trial, root / "first.json", digest)
        record("nested unnecessary deliverables counted without failing valid data",
               r["arms"]["arm_a"]["artifact_passed"] and
               "unused-reports/appendix/long-notes.md" in r["arms"]["arm_a"]["nonrequired_artifacts"] and
               "unused-empty-folder/" in r["arms"]["arm_a"]["nonrequired_artifacts"] and
               not r["arms"]["arm_b"]["nonrequired_artifacts"])
        nested_extra.unlink()
        nested_extra.parent.rmdir()
        (extra_sub / "unused-reports").rmdir()
        empty_extra.rmdir()
        record("equal correct results accept both without naming a winner", all(v["artifact_passed"] for v in r["arms"].values()) and r["winner"] is None and r["externally_frozen_manifest_checked"])
        # A symlink to the private answer used to pass: this must now be refused.
        answer = trial / "participants/arm_a/submission/answer.json"
        original_answer = answer.read_bytes()
        answer.unlink()
        answer.symlink_to(trial / "reviewer_private/case/private/expected.json")
        alias = grade(trial, root / "alias.json", digest)
        record("a submission symlink to private truth cannot pass", not alias["arms"]["arm_a"]["artifact_passed"]
               and bool(alias["arms"]["arm_a"]["submission_issues"]))
        answer.unlink()
        answer.write_bytes(original_answer)
        # Re-label a frozen arm without changing the actual source file hashes.
        # Even without a separate externally trusted digest, the grader must
        # refuse a self-contradictory source/label assignment.
        raw = (trial / "reviewer_private/freeze.json").read_bytes()
        forged = read(trial / "reviewer_private/freeze.json")
        forged["arm_snapshots"]["arm_a"]["variant"] = (
            "C14-lean" if forged["arm_snapshots"]["arm_a"]["variant"] == "C13" else "C13")
        dump(trial / "reviewer_private/freeze.json", forged)
        try:
            grade(trial, root / "misattributed.json")
            record("mislabelled arm cannot pass scoring", False)
        except ValueError:
            record("mislabelled arm cannot pass scoring", True)
        (trial / "reviewer_private/freeze.json").write_bytes(raw)
        # Explicitly refuse v1's swapped attribution and v2's optional Skill entry.
        for old_schema in ("forge-r24-paired-trial/1", "forge-r24-paired-trial/2", "forge-r24-paired-trial/3", "forge-r24-paired-trial/4"):
            old_format = read(trial / "reviewer_private/freeze.json")
            old_format["schema"] = old_schema
            dump(trial / "reviewer_private/freeze.json", old_format)
            try:
                grade(trial, root / (old_schema[-1] + "-obsolete.json"))
                record("legacy " + old_schema + " trial is rejected", False)
            except ValueError:
                record("legacy " + old_schema + " trial is rejected", True)
            (trial / "reviewer_private/freeze.json").write_bytes(raw)
        bad_protocol = read(trial / "reviewer_private/freeze.json")
        bad_protocol["protocol"] = "entry_optional"
        dump(trial / "reviewer_private/freeze.json", bad_protocol)
        try:
            grade(trial, root / "bad-protocol.json")
            record("forged skill exposure protocol is rejected", False)
        except ValueError:
            record("forged skill exposure protocol is rejected", True)
        (trial / "reviewer_private/freeze.json").write_bytes(raw)
        try:
            grade(trial, root / "first.json")
            record("grade receipt cannot overwrite", False)
        except FileExistsError:
            record("grade receipt cannot overwrite", True)
        p = trial / "participants/arm_a/task/source.json"
        p.write_bytes(p.read_bytes() + b" ")
        r = grade(trial, root / "second.json")
        record("tampered public input rejected", not r["arms"]["arm_a"]["artifact_passed"] and bool(r["arms"]["arm_a"]["frozen_input_issues"]))
        p = trial / "participants/arm_b/skill/SKILL.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        r = grade(trial, root / "third.json")
        record("changed Skill version rejected", bool(r["arms"]["arm_b"]["frozen_input_issues"]))
        frozen_path = trial / "reviewer_private/freeze.json"
        freeze_raw = frozen_path.read_bytes()
        frozen_path.write_bytes(freeze_raw + b" ")
        try:
            grade(trial, root / "forged_freeze.json", digest)
            record("externally sealed freeze digest rejects modified manifest", False)
        except ValueError:
            record("externally sealed freeze digest rejects modified manifest", True)
        frozen_path.write_bytes(freeze_raw)
        oracle = trial / "reviewer_private/case/private/expected.json"
        oracle.write_bytes(oracle.read_bytes() + b" ")
        try:
            grade(trial, root / "tampered_judge.json")
            record("altered private scoring truth blocks grading", False)
        except ValueError:
            record("altered private scoring truth blocks grading", True)
        try:
            prepare(fake_repo, "extract", 207, trial, verified_sources)
            record("trial root cannot overwrite", False)
        except FileExistsError:
            record("trial root cannot overwrite", True)
        second = root / "secondtrial"
        prepare(fake_repo, "reconcile", 671, second, verified_sources)
        record("reconciliation task includes all real source documents", len(list((second / "participants/arm_a/task").iterdir())) == 5)
        r = grade(second, root / "fourth.json")
        record("missing submissions do not become passes", all(not x["artifact_passed"] for x in r["arms"].values()))
        command = [sys.executable, str(Path(__file__).resolve()), "grade", "--trial", str(second)]
        frozen_second = sha(second / "reviewer_private/freeze.json")
        failed_cli = subprocess.run(command + ["--receipt", str(root / "cli_missing.json"),
                                     "--trusted-freeze-sha256", frozen_second],
                                    capture_output=True, text=True, check=False)
        record("CLI returns nonzero when both submissions are absent", failed_cli.returncode == 2
               and not read(root / "cli_missing.json")["artifact_checks_passed"])
        sys.path.insert(0, str(HERE / "reconciliation"))
        from public_producer import execute as produce_public
        for arm in ARMS:
            participant = second / "participants" / arm
            produce_public(participant / "task", participant / "submission")
        r = grade(second, root / "fifth.json")
        record("raw-input-only implementation passes both neutral task arms",
               all(x["artifact_passed"] for x in r["arms"].values()))
        good_cli = subprocess.run(command + ["--receipt", str(root / "cli_complete.json"),
                                   "--trusted-freeze-sha256", frozen_second],
                                  capture_output=True, text=True, check=False)
        record("CLI exits zero only for fully correct sealed artifact check", good_cli.returncode == 0
               and read(root / "cli_complete.json")["artifact_checks_passed"])
        unsealed_cli = subprocess.run(command + ["--receipt", str(root / "cli_unsealed.json")],
                                      capture_output=True, text=True, check=False)
        record("unsealed diagnostic grading cannot signal success to CI", unsealed_cli.returncode == 2
               and not read(root / "cli_unsealed.json")["externally_frozen_manifest_checked"])
        extra = second / "participants/arm_a/submission/unused_summary.txt"
        extra.write_text("extra developer artifact", encoding="utf-8")
        r = grade(second, root / "sixth.json")
        record("unnecessary output is counted without retroactive rejection",
               r["arms"]["arm_a"]["artifact_passed"] and r["arms"]["arm_a"]["nonrequired_artifacts"] == ["unused_summary.txt"])
        csv_file = second / "participants/arm_b/submission/suppliers.csv"
        csv_file.write_bytes(csv_file.read_bytes().replace(b"Cedar,0", b"Cedar,1"))
        r = grade(second, root / "seventh.json")
        record("reconciliation result corruption fails affected arm", not r["arms"]["arm_b"]["artifact_passed"])
        # Reject a frozen directory replaced by an external alias even if
        # its contents could otherwise have the expected SHA map.
        arm_skill = second / "participants/arm_a/skill"
        shutil.rmtree(arm_skill)
        arm_version = read(second / "reviewer_private/freeze.json")["arm_snapshots"]["arm_a"]["variant"]
        arm_skill.symlink_to(fake_repo / SKILLS[arm_version], target_is_directory=True)
        malicious = grade(second, root / "aliased_skill.json")
        record("frozen skill directory symlink is refused", bool(malicious["arms"]["arm_a"]["frozen_input_issues"]))
        record("no independent Agent is ever claimed", r["winner"] is None and r["independent_review"] == "not_run")
    return {"passed": all(c["passed"] for c in checks), "checks": checks,
            "scope": "author-local fixture integrity, not independent agent or comparative performance"}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    actions = p.add_subparsers(dest="cmd", required=True)
    a = actions.add_parser("prepare")
    a.add_argument("--repo", type=Path, required=True)
    a.add_argument("--kind", choices=["extract", "reconcile"], required=True)
    a.add_argument("--seed", type=int, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--source-catalog", type=Path, required=True,
                   help="trusted real candidate file identity catalog")
    a.add_argument("--trusted-catalog-git-blob", required=True,
                   help="Git Blob SHA of catalog from external trusted source")
    g = actions.add_parser("grade")
    g.add_argument("--trial", type=Path, required=True)
    g.add_argument("--receipt", type=Path, required=True)
    g.add_argument("--trusted-freeze-sha256", default=None)
    actions.add_parser("selftest")
    args = p.parse_args(argv)
    try:
        if args.cmd == "selftest":
            result = selftest()
        elif args.cmd == "prepare":
            # Explicit source attestation must finish before any trial path exists.
            evidence = verify_source_catalog(args.repo, args.source_catalog, args.trusted_catalog_git_blob)
            result = prepare(args.repo, args.kind, args.seed, args.out, evidence)
        else:
            result = grade(args.trial, args.receipt, args.trusted_freeze_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # Never return process success when either arm has missing/incorrect
        # artifacts or when the freeze manifest lacks a trusted external seal.
        # Exit 0 STILL does not mean either Agent was independent or won.
        if args.cmd == "grade":
            return 0 if (result["artifact_checks_passed"] and
                         result["externally_frozen_manifest_checked"]) else 2
        return 0 if result.get("passed") is not False else 2
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": type(exc).__name__ + ": " + str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
