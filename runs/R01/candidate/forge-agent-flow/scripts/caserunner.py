#!/usr/bin/env python3
"""Run frozen program-mode cases against an explicitly supplied local command.

The command receives {case_id, inputs} on stdin and emits {status, output} as
one JSON object. This runner grades exact JSON values and process outcomes;
it cannot judge human criteria, authenticate producers, or discover undeclared
dependencies. Run only an authorized command. Each run uses a new directory.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

import evalplan
import projectctl as p

SCHEMA = "forge-case-run/1"
MAX_OUTPUT = 8 * 1024 * 1024


def require_plan(plan):
    result = evalplan.validate(plan)
    if not result["valid"]:
        raise p.ProjectError("Invalid case plan: " + "; ".join(result["errors"]))


def ref(path):
    return {"path": str(Path(path).resolve()), "sha256": p.file_sha256(path)}


def parse_output(path):
    if Path(path).stat().st_size > MAX_OUTPUT:
        raise p.ProjectError("Output exceeds 8 MiB")
    value = p.load_json(path)
    p._exact_keys(value, {"status", "output"}, "adapter output")
    if value["status"] not in {"completed", "failed", "blocked"}:
        raise p.ProjectError("Invalid product status")
    if not isinstance(value["output"], dict):
        raise p.ProjectError("Product output must be an object")
    return value


def grade(plan, report):
    """Recompute from checked raw outputs, never trust a stored pass label."""
    require_plan(plan)
    p._exact_keys(report, {"schema", "plan_hash", "candidate", "command", "cwd",
                          "timeout_seconds", "cases"}, "case report")
    if report["schema"] != SCHEMA or report["plan_hash"] != p.digest(plan):
        raise p.ProjectError("Case report does not match the complete frozen plan")
    p._string_list(report["command"], "command", allow_empty=False)
    p._string(report["cwd"], "cwd")
    timeout = report["timeout_seconds"]
    if type(timeout) not in {int, float} or not math.isfinite(timeout) or timeout <= 0:
        raise p.ProjectError("Invalid timeout_seconds")
    candidate = report["candidate"]
    p._exact_keys(candidate, {"files", "hash"}, "candidate")
    if not isinstance(candidate["files"], list) or not candidate["files"]:
        raise p.ProjectError("Candidate requires nonempty source references")
    checked = [p.check_evidence(item, "candidate source") for item in candidate["files"]]
    if len({item["path"] for item in checked}) != len(checked):
        raise p.ProjectError("Duplicate candidate source")
    if candidate["hash"] != p.digest(checked):
        raise p.ProjectError("Candidate manifest hash mismatch")
    if not isinstance(report["cases"], list):
        raise p.ProjectError("cases must be a list")
    actual = {}
    for row in report["cases"]:
        p._exact_keys(row, {"id", "input", "stdout", "stderr", "returncode",
                           "timed_out", "elapsed_seconds", "launch_error"}, "case record")
        if row["id"] in actual:
            raise p.ProjectError("Duplicate case record")
        actual[row["id"]] = row
    if set(actual) != {case["id"] for case in plan["cases"]}:
        raise p.ProjectError("Case records must cover exactly the full frozen plan")
    criteria = {item["id"]: item for item in plan["criteria"]}
    results = []
    for case in plan["cases"]:
        row = actual[case["id"]]
        for name in ("input", "stdout", "stderr"):
            p.check_evidence(row[name], f"{case['id']}.{name}")
        if p.canonical(p.load_json(row["input"]["path"])) != p.canonical(
                {"case_id": case["id"], "inputs": case["inputs"]}):
            raise p.ProjectError("Adapter input differs from frozen case")
        if type(row["timed_out"]) is not bool:
            raise p.ProjectError("timed_out must be boolean")
        if row["returncode"] is not None and type(row["returncode"]) is not int:
            raise p.ProjectError("returncode must be an integer or null")
        elapsed = row["elapsed_seconds"]
        if type(elapsed) not in {int, float} or not math.isfinite(elapsed) or elapsed < 0:
            raise p.ProjectError("Invalid elapsed_seconds")
        if row["launch_error"] is not None:
            p._string(row["launch_error"], "launch_error")
        if row["timed_out"] or row["launch_error"] or row["returncode"] != 0:
            verdict, reason = "fail", "Process failed, timed out, or could not start"
        else:
            try:
                output = parse_output(row["stdout"]["path"])
                matches = (output["status"] == case["expected_status"] and
                           p.canonical(output["output"]) == p.canonical(case["expected"]))
                if not matches:
                    verdict, reason = "fail", "Product status or full output differs"
                elif any(criteria[cid]["kind"] == "human" for cid in case["criteria"]):
                    verdict, reason = "needs_review", "Matching values cannot judge human criteria"
                else:
                    verdict, reason = "pass", "Process and full JSON expectations match"
            except (p.ProjectError, OSError, TypeError) as exc:
                verdict, reason = "fail", f"Invalid adapter output: {exc}"
        results.append({"id": case["id"], "required": case["required"],
                        "status": verdict, "reason": reason,
                        "criteria": case["criteria"], "elapsed_seconds": elapsed})
    required = [row for row in results if row["required"]]
    verdict = ("fail" if any(row["status"] == "fail" for row in required) else
               "needs_review" if any(row["status"] == "needs_review" for row in required)
               else "pass")
    return {"status": verdict, "required_passed": sum(row["status"] == "pass" for row in required),
            "required_total": len(required), "cases": results,
            "candidate_hash": candidate["hash"], "plan_hash": report["plan_hash"],
            "limits": ["Exact JSON grading only; no human or UI judgement",
                       "Source manifest covers declared files only; environment/dependencies are not attested",
                       "Hashes detect drift; they do not authenticate producer or process receipts"]}


def run(plan, command, cwd, candidate_paths, output_dir, timeout=30):
    require_plan(plan)
    p._string_list(command, "command", allow_empty=False)
    if type(timeout) not in {int, float} or not math.isfinite(timeout) or timeout <= 0:
        raise p.ProjectError("timeout must be positive and finite")
    cwd = str(Path(cwd).resolve(strict=True))
    if not Path(cwd).is_dir():
        raise p.ProjectError("cwd must be a directory")
    sources = sorted({str(Path(path).resolve(strict=True)) for path in candidate_paths})
    if not sources:
        raise p.ProjectError("Supply candidate source files, including the adapter")
    candidate = [ref(path) for path in sources]
    directory = Path(output_dir).resolve()
    if any(Path(path).is_relative_to(directory) for path in sources):
        raise p.ProjectError("Run output must be separate from candidate sources")
    directory.mkdir(parents=True, exist_ok=False)
    snapshot_dir = directory / "source-snapshot"
    snapshot_dir.mkdir()
    snapshot = []
    for index, source in enumerate(candidate):
        target = snapshot_dir / f"{index:04d}-{Path(source['path']).name}"
        shutil.copyfile(source["path"], target)
        copied = ref(target)
        if copied["sha256"] != source["sha256"]:
            raise p.ProjectError("Candidate changed while capturing source snapshot; no cases executed")
        snapshot.append({"original": source, "snapshot": copied})
    p.save(snapshot_dir / "manifest.json", {"candidate_hash": p.digest(candidate), "files": snapshot})
    report = {"schema": SCHEMA, "plan_hash": p.digest(plan),
              "candidate": {"files": candidate, "hash": p.digest(candidate)},
              "command": command, "cwd": cwd, "timeout_seconds": timeout, "cases": []}
    for case in plan["cases"]:
        case_dir = directory / case["id"]
        case_dir.mkdir()
        request = {"case_id": case["id"], "inputs": case["inputs"]}
        input_path, stdout, stderr = [case_dir / name for name in ("input.json", "stdout.txt", "stderr.txt")]
        p.save(input_path, request)
        started = time.monotonic()
        timed_out, launch_error, returncode = False, None, None
        with stdout.open("wb") as out, stderr.open("wb") as err:
            try:
                process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                                           stdout=out, stderr=err, start_new_session=(os.name == "posix"))
                try:
                    process.communicate(p.canonical(request).encode("utf-8"), timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    if os.name == "posix":
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        process.kill()
                    process.communicate()
                returncode = process.returncode
            except OSError as exc:
                launch_error = str(exc)
        report["cases"].append({"id": case["id"], "input": ref(input_path),
                                "stdout": ref(stdout), "stderr": ref(stderr),
                                "returncode": returncode, "timed_out": timed_out,
                                "launch_error": launch_error,
                                "elapsed_seconds": round(time.monotonic() - started, 6)})
    p.save(directory / "report.json", report)
    # Preserve raw report even when candidate drift prevents regrading.
    try:
        assessment = grade(plan, report)
    except (p.ProjectError, OSError) as exc:
        assessment = {"status": "unverified", "reason": str(exc)}
    p.save(directory / "assessment.json", assessment)
    return {"report": str(directory / "report.json"), "assessment": assessment}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("plan")
    execute.add_argument("--cwd", required=True)
    execute.add_argument("--candidate-file", action="append", required=True)
    execute.add_argument("--output-dir", required=True)
    execute.add_argument("--timeout", type=float, default=30)
    execute.add_argument("--command", nargs=argparse.REMAINDER, required=True)
    assess = sub.add_parser("assess")
    assess.add_argument("plan")
    assess.add_argument("report")
    args = parser.parse_args(argv)
    try:
        plan = p.load_json(args.plan)
        result = (run(plan, args.command, args.cwd, args.candidate_file, args.output_dir, args.timeout)
                  if args.action == "run" else grade(plan, p.load_json(args.report)))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("assessment", result)["status"] == "pass" else 2
    except (p.ProjectError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
