"""Freeze the selected official input and start the authorized real solution."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl

def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def save(name, obj):
    with (ROOT / name).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

def entry(p):
    raw = p.read_bytes()
    return dict(path=p.relative_to(ROOT).as_posix(), size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

manifest = read("runs/R16/source/source-manifest.json")
base = ROOT / "runs/R16/source"
for item in manifest["files"]:
    raw = (base / item["path"]).read_bytes()
    assert len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], item["path"]
selected = sorted((base / "official_extracted/D_corrected").iterdir())
assert len(selected) == 3 and all(p.is_file() for p in selected)
contract = read("runs/R16/acceptance-draft.json")
contract["status"] = "frozen_before_original_solver"
contract["selected_problem"] = dict(year=2026, contest="MathorCup regular contest", question="D",
    title="多场景、多目标货物运输装箱策略优化", source="runs/R16/source/D_corrected.zip",
    correction_url="https://www.mathorcup.org/detail/2488",
    required_inputs=[p.relative_to(ROOT).as_posix() for p in selected])
save("runs/R16/acceptance.json", contract)
paths = selected + [base / "D_corrected.zip", base / "packet.md", base / "source-manifest.json",
    ROOT / "runs/R16/acceptance.json", ROOT / "runs/R14/candidate/C9-lock.json"]
save("runs/R16/input-lock.json", dict(schema="forge-revision-lock/1", revision="R16-official-D-input",
    files=[entry(p) for p in paths], solution_papers_included=False,
    limits="Official problem/data/version identity; no reference solution, chosen model or expected result"))
save("runs/R16/source-check.json", dict(source_manifest_entries_checked=len(manifest["files"]),
    sha256_matches=True, selected_official_files=3, old_D_not_used=True,
    source_corrections_used=2, source_correction_limit=2,
    source_failures_preserved=manifest["failures_preserved"],
    limits="Retrieval and byte checks only, not a solved problem or CPU feasibility proof"))

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    task = ctl.task_map(state)["R16-01"]
    attempt = task["attempts"][-1]
    task["repairs_used"] = 2
    save("runs/R16/R16-01-result.json", dict(task_id=task["id"], attempt_id=attempt["id"],
        requirements_hash=attempt["requirements_hash"],
        criteria=[dict(id="s1", status="pass", evidence=["runs/R16/source/source-manifest.json", "runs/R16/source-check.json", "runs/R16/input-lock.json"]),
                  dict(id="s2", status="pass", evidence=["runs/R16/source/packet.md", "runs/R16/scope-decision.json"])],
        effect=dict(target="Official historical question without solution-paper contamination",
            hypothesis="Real question/data provide stronger workflow test than synthetic micro-case",
            baseline="R14 self-created eight-week three-station fixture",
            conditions="Official corrected D ZIP and raw PDF/DOCX/XLSX, neutral source packet",
            observations="HTTP200 original ZIPs, raw byte checks and errata identified; source2/2 preserved",
            limits="No solver result, CPU feasibility or competition quality claim",
            metrics=dict(source_corrections_used=2, source_limit=2, tokens=None, cost=None)),
        next_action="Frozen original D solution trial by a fresh actor"))
    ctl.finish(state, ROOT, "R16-01", "runs/R16/R16-01-result.json")
    state["events"].append(dict(at=ctl.stamp(), command="freeze_original_historical_problem",
        result=dict(question="D", corrected_official=True, solution_papers=False, source_budget=2)))
    index = read("state/revision-locks.json")
    for name in ["runs/R14/math-output-lock.json", "runs/R16/input-lock.json"]:
        assert name not in index["locks"]
        index["locks"].append(name)
    ctl.write_json(ROOT / "state/revision-locks.json", index)
    ctl.write_json(ROOT / "state/continuation.json", state)
    phase = ctl.phase_view(read("state/phases/R16.json"), state)
    ctl.write_json(ROOT / "state/phases/R16.json", phase)
    ctl.synchronize(ROOT, state)
print(json.dumps(dict(source_gate="done", frozen_official_files=3, source_budget="2/2", question="D")))
