"""Read freeze metadata only; deliberately does not open holdout truth bytes."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

R = Path("runs/R21")
OUT = R / "review/holdout"
OUT.mkdir(parents=True, exist_ok=True)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lock_info(p):
    d = json.loads(p.read_text(encoding="utf-8"))
    return {"path": str(p).replace("\\", "/"), "sha256": sha(p), "schema": d.get("schema"),
            "revision": d.get("revision"), "frozen_at": d.get("frozen_at"),
            "file_count": len(d.get("files", [])), "files": d.get("files", [])}

initial = lock_info(R / "review/initial-lock.json")
execution = lock_info(R / "execution-lock.json")
evaluation = lock_info(R / "evaluation-lock.json")
freeze_receipt = json.loads((R / "receiver-initial-freeze-command.json").read_text(encoding="utf-8"))
initial_files = {x["path"].replace("\\", "/"): x for x in initial["files"]}
needed_initial = ["runs/R21/review/initial/result.json", "runs/R21/review/initial/pre-holdout-ready.json"]
initial_checks = []
for rel in needed_initial:
    entry = initial_files.get(rel)
    p = Path(rel)
    initial_checks.append({"path": rel, "listed": entry is not None,
                          "matches": bool(entry and p.is_file() and p.stat().st_size == entry.get("size_bytes") and sha(p) == entry.get("sha256"))})
exec_files = {x["path"].replace("\\", "/"): x for x in execution["files"]}
eval_files = {x["path"].replace("\\", "/"): x for x in evaluation["files"]}
truth_path = "runs/R21/evaluation/holdout_truth.csv"
report = {
    "schema": "r21-holdout-freeze-binding/1",
    "initial_lock": {k: initial[k] for k in ("path", "sha256", "schema", "revision", "frozen_at", "file_count")},
    "execution_lock": {k: execution[k] for k in ("path", "sha256", "schema", "revision", "frozen_at", "file_count")},
    "evaluation_lock": {k: evaluation[k] for k in ("path", "sha256", "schema", "revision", "frozen_at", "file_count")},
    "initial_freeze_command_structure_only": {"schema": freeze_receipt.get("schema"), "state": freeze_receipt.get("state"),
        "exit_code": freeze_receipt.get("exit_code"), "argv": freeze_receipt.get("argv"), "cwd": freeze_receipt.get("cwd"),
        "begin_utc": freeze_receipt.get("begin", {}).get("utc"), "end_utc": freeze_receipt.get("end", {}).get("utc")},
    "initial_result_identity_checks": initial_checks,
    "holdout_truth_lock_identity_only": {"path": truth_path, "listed": truth_path in eval_files,
        "expected_bytes": eval_files.get(truth_path, {}).get("size_bytes"),
        "expected_sha256": eval_files.get(truth_path, {}).get("sha256"),
        "truth_bytes_opened_by_this_command": False},
    "production_execution_lock_has_required_route_outputs": all(p in exec_files for p in (
        "runs/R21/execution/science-v1/future/shared_ridge10/predictions.csv",
        "runs/R21/execution/science-v1/future/shared_ridge10/replenishment.csv",
        "runs/R21/execution/science-v1/future/weekly_mean56/predictions.csv",
        "runs/R21/execution/science-v1/future/weekly_mean56/replenishment.csv")),
}
report["binding_valid"] = (
    all(x["matches"] for x in initial_checks)
    and report["holdout_truth_lock_identity_only"]["listed"]
    and freeze_receipt.get("state") == "finished" and freeze_receipt.get("exit_code") == 0
    and report["production_execution_lock_has_required_route_outputs"]
    and len(execution["files"]) == 301
)
(OUT / "freeze-bindings.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "initial_lock" and k != "execution_lock" and k != "evaluation_lock"}, ensure_ascii=False, indent=2))
print(json.dumps({"initial_lock": report["initial_lock"], "execution_lock": report["execution_lock"], "evaluation_lock": report["evaluation_lock"]}, ensure_ascii=False, indent=2))
