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
import random
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


def prepare(repo: Path, kind: str, seed: int, out: Path) -> dict:
    if out.exists() or out.is_symlink():
        raise FileExistsError("trial root already exists, cannot overwrite")
    if kind not in ("extract", "reconcile"):
        raise ValueError("unsupported task kind")
    source_dirs = {variant: repo / relative for variant, relative in SKILLS.items()}
    # Verify candidates completely before creating case or trial directories.
    for directory in source_dirs.values():
        md_files(directory)
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
            "请完成 task/ 中用户要求的真实交付，按需参考 skill/SKILL.md。"
            "只在 submission/ 中写成果；不要访问其他参与者或评分材料。"
            "用实际材料核对结果。此说明不是独立性或权限证明。\n", encoding="utf-8")
        arms[arm] = {"variant": version, "skill_sha256": skills,
                     "start_sha256": sha(dst / "START_HERE.md")}
    manifest = {
        "schema": "forge-r24-paired-trial/2", "status": "prepared_not_executed",
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
            "worker_input_dirs": [str(out / "participants" / arm) for arm in ARMS]}


def check_frozen(out: Path, arm: str, freeze: dict) -> list[str]:
    worker = out / "participants" / arm
    errors = []
    expected_task = freeze["source_sha256"]
    expected_skill = freeze["arm_snapshots"][arm]["skill_sha256"]
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


def grade(out: Path, receipt: Path, trusted_freeze_sha256: str | None = None) -> dict:
    if receipt.exists() or receipt.is_symlink():
        raise FileExistsError("refusing to overwrite an earlier grading receipt")
    if trusted_freeze_sha256 is not None and sha(out / "reviewer_private" / "freeze.json") != trusted_freeze_sha256:
        raise ValueError("frozen study manifest differs from externally retained digest")
    freeze = read(out / "reviewer_private" / "freeze.json")
    if freeze.get("schema") != "forge-r24-paired-trial/2":
        raise ValueError("legacy or unknown trial schema; v1 randomized arm labels are unreliable")
    if freeze.get("status") != "prepared_not_executed":
        raise ValueError("unrecognized frozen trial status")
    # Check attribution independently of the participant's artifact contents.
    variant_sources = freeze.get("variant_source_sha256")
    snapshots = freeze.get("arm_snapshots")
    if not isinstance(variant_sources, dict) or set(variant_sources) != set(SKILLS):
        raise ValueError("missing version-labelled Skill source hashes")
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
    for arm in ARMS:
        worker = out / "participants" / arm
        problems = check_frozen(out, arm, freeze)
        sub = worker / "submission"
        if not sub.is_dir() or sub.is_symlink():
            problems.append("missing or invalid submission folder")
        score = {"passed": False, "details": None}
        if not problems:
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
        if problems:
            score["passed"] = False
        expected_names = {"answer.json"} if kind == "extract" else {"ledger.csv", "suppliers.csv", "workflow.md"}
        if sub.is_dir():
            extra = sorted(p.name for p in sub.iterdir() if p.is_file() and p.name not in expected_names)
        else:
            extra = []
        results[arm] = {"variant": freeze["arm_snapshots"][arm]["variant"],
                        "artifact_passed": score["passed"], "score_details": score,
                        "frozen_input_issues": problems, "nonrequired_artifacts": extra,
                        "independent_actor_verified": False}
    response = {"schema": "forge-r24-paired-grade/1", "task_kind": kind,
                "cases_scored": len(results), "arms": results,
                "comparison_result": "not_established_no_independent_actor_receipts",
                "independent_review": "not_run", "winner": None,
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
        trial = root / "trial"
        prepare(fake_repo, "extract", 207, trial)
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
            prepare(fake_repo, "extract", seed, candidate)
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
               freeze.get("schema") == "forge-r24-paired-trial/2" and
               freeze["arm_snapshots"]["arm_a"]["skill_sha256"] ==
               freeze["variant_source_sha256"][freeze["arm_snapshots"]["arm_a"]["variant"]])
        record("private oracle hash frozen", bool(freeze["oracle_sha256"]))
        digest = sha(trial / "reviewer_private/freeze.json")
        record("external freeze token available", len(digest) == 64)
        record("both arms have identical original task bytes", all(
            sha(trial / "participants" / arm / "task/source.json") == freeze["source_sha256"]["source.json"] for arm in ARMS))
        record("private oracle absent from worker packet", all(
            not list((trial / "participants" / arm).rglob("expected.json")) for arm in ARMS))
        for arm in ARMS:
            output = trial / "participants" / arm / "submission"
            output.mkdir()
            source = read(trial / "participants" / arm / "task/source.json")
            dump(output / "answer.json", {"city": source["city"], "deadline": source["deadline"]})
        r = grade(trial, root / "first.json", digest)
        record("equal correct results accept both without naming a winner", all(v["artifact_passed"] for v in r["arms"].values()) and r["winner"] is None and r["externally_frozen_manifest_checked"])
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
        # Explicitly refuse old v1 trials; v1 could attribute swapped versions wrongly.
        old_format = read(trial / "reviewer_private/freeze.json")
        old_format["schema"] = "forge-r24-paired-trial/1"
        dump(trial / "reviewer_private/freeze.json", old_format)
        try:
            grade(trial, root / "v1.json")
            record("legacy v1 ambiguous trial is never accepted", False)
        except ValueError:
            record("legacy v1 ambiguous trial is never accepted", True)
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
            prepare(fake_repo, "extract", 207, trial)
            record("trial root cannot overwrite", False)
        except FileExistsError:
            record("trial root cannot overwrite", True)
        second = root / "secondtrial"
        prepare(fake_repo, "reconcile", 671, second)
        record("reconciliation task includes all real source documents", len(list((second / "participants/arm_a/task").iterdir())) == 5)
        r = grade(second, root / "fourth.json")
        record("missing submissions do not become passes", all(not x["artifact_passed"] for x in r["arms"].values()))
        sys.path.insert(0, str(HERE / "reconciliation"))
        from public_producer import execute as produce_public
        for arm in ARMS:
            participant = second / "participants" / arm
            produce_public(participant / "task", participant / "submission")
        r = grade(second, root / "fifth.json")
        record("raw-input-only implementation passes both neutral task arms",
               all(x["artifact_passed"] for x in r["arms"].values()))
        extra = second / "participants/arm_a/submission/unused_summary.txt"
        extra.write_text("extra developer artifact", encoding="utf-8")
        r = grade(second, root / "sixth.json")
        record("unnecessary output is counted without retroactive rejection",
               r["arms"]["arm_a"]["artifact_passed"] and r["arms"]["arm_a"]["nonrequired_artifacts"] == ["unused_summary.txt"])
        csv_file = second / "participants/arm_b/submission/suppliers.csv"
        csv_file.write_bytes(csv_file.read_bytes().replace(b"Cedar,0", b"Cedar,1"))
        r = grade(second, root / "seventh.json")
        record("reconciliation result corruption fails affected arm", not r["arms"]["arm_b"]["artifact_passed"])
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
    g = actions.add_parser("grade")
    g.add_argument("--trial", type=Path, required=True)
    g.add_argument("--receipt", type=Path, required=True)
    g.add_argument("--trusted-freeze-sha256", default=None)
    actions.add_parser("selftest")
    args = p.parse_args(argv)
    try:
        result = selftest() if args.cmd == "selftest" else prepare(args.repo, args.kind, args.seed, args.out) if args.cmd == "prepare" else grade(args.trial, args.receipt, args.trusted_freeze_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("passed") is not False else 2
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": type(exc).__name__ + ": " + str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
