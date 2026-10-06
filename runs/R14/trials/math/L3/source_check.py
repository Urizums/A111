#!/usr/bin/env python3
"""Check the authorized raw case and the frozen C9 Forge source packet."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TRIAL = Path(__file__).resolve().parent
problem_path = ROOT / "runs/R14/cases/math/problem.json"
lock_path = ROOT / "runs/R14/candidate/C9-lock.json"
problem_bytes = problem_path.read_bytes()
problem = json.loads(problem_bytes.decode("utf-8"))
lock = json.loads(lock_path.read_text(encoding="utf-8"))
assert problem["case_id"] == "offline-demand-allocation-01"
assert len(problem["data"]) == 8 and all(set(("week", "A", "B", "C")) <= set(r) for r in problem["data"])
assert [r["week"] for r in problem["data"]] == list(range(1, 9))
assert problem["units"] == {"demand": "units/week", "allocation": "integer units for week9", "cost": "CNY/unit"}
doc_checks = []
for item in lock["files"]:
    path = ROOT / item["path"]
    data = path.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    doc_checks.append({"path": item["path"], "expected_sha256": item["sha256"], "actual_sha256": got, "matches": got == item["sha256"]})
assert all(item["matches"] for item in doc_checks)
bad = json.loads(problem_bytes.decode("utf-8"))
bad["distribution"]["delivery_cost_per_unit"]["A"] = "two CNY"
bad_path = TRIAL / "malformed_bad_cost.json"
bad_path.write_text(json.dumps(bad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = {
    "case_id": problem["case_id"],
    "problem_path": "runs/R14/cases/math/problem.json",
    "problem_sha256": hashlib.sha256(problem_bytes).hexdigest(),
    "data_rows": len(problem["data"]),
    "stations": ["A", "B", "C"],
    "boundary_material_count": len(problem["boundary_materials"]),
    "c9_lock_repairs_used": lock["repairs_used"],
    "c9_lock_limit": lock["repair_limit"],
    "locked_forge_files": doc_checks,
    "malformed_fixture": str(bad_path.relative_to(ROOT)).replace("\\", "/"),
    "malformed_change": "distribution.delivery_cost_per_unit.A = 'two CNY'",
}
(TRIAL / "source_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"raw_data_rows": len(problem["data"]), "locked_docs_verified": len(doc_checks), "malformed_fixture": report["malformed_fixture"]}, ensure_ascii=False))
