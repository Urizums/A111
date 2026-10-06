"""Integrate actual source publication receipts while coordinator lease is held."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl
def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))
commit = read("runs/R16/publication/source-commit-command.json")
push = read("runs/R16/publication/source-push-command.json")
remote = read("runs/R16/publication/source-remote-command.json")
ci_record = read("runs/R16/publication/source-ci-discovery-command.json")
for receipt in [commit, push, remote, ci_record]:
    assert receipt["state"] == "finished" and receipt["exit_code"] == 0
sha = remote["stdout"].split()[0]
ci = next(item for item in json.loads(ci_record["stdout"]) if item["headSha"] == sha)
result = dict(schema="forge-development-publication/1", source_commit=sha,
    repository="Urizums/A111", branch="main", source_push_observed=True,
    remote_head_at_observation=sha, evidence=[
        "runs/R16/publication/source-commit-command.json",
        "runs/R16/publication/source-push-command.json",
        "runs/R16/publication/source-remote-command.json",
        "runs/R16/publication/source-ci-discovery-command.json"],
    source_ci_at_discovery=ci, current_actor_pending=[],
    source_scope="C9 document candidate; R14 diagnostic artifacts; R16 official raw material and stopped unexecuted draft",
    R14_diagnostic=dict(pass_count=38, fail_count=2),
    R16_full_paper_delivered=False, R16_original_case_budget=dict(used=2, limit=2),
    full_acceptance_passed=False,
    local_checks=dict(handoff="pass91_source_375_cutoff_1062_release_690_revisions",
        queue="pass46_tasks", original_tasks="38_hashes_unchanged",
        staged_whitespace="exit1: warnings in frozen/source records retained without byte normalization",
        whitespace_evidence="runs/R16/staged-whitespace-check-command.json"),
    limits="Development source publication and integrity do not supersede failed semantic cases or prove CI success while queued.",
    receipt_commit="Prepared after the identified source push; its future hash is not claimed here.")
ctl.write_json(ROOT / "runs/R16/publication/source-receipt.json", result)
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    baseline = read("runs/R14/baseline.json")["historical_task_hashes"]
    for tid, digest in baseline.items():
        assert ctl.identity(ctl.task_map(state)[tid]) == digest, tid
    state["execution"].update(R14_R16_publication_source_commit=sha,
        R14_R16_publication_receipt="runs/R16/publication/source-receipt.json",
        R14_R16_source_ci_at_discovery=ci, publication_source_commit=sha,
        publication_receipt="runs/R16/publication/source-receipt.json",
        coordinator_release_evidence="runs/R16/publication/lease-release-observation.json")
    state["events"].append(dict(at=ctl.stamp(), command="record_actual_R14_R16_source_push",
        result=dict(source_commit=sha, remote_head_at_observation=sha, source_ci_status=ci["status"],
            full_acceptance_passed=False, old_tasks_preserved=True)))
    ctl.write_json(ROOT / "state/continuation.json", state)
    ctl.synchronize(ROOT, state)
    checkpoint = read("state/checkpoint.json")
    checkpoint.update(publication_source_commit=sha,
        publication_evidence="runs/R16/publication/source-receipt.json",
        R14_R16_source_ci_at_discovery=ci, unpublished_work=False,
        publication_note="Development source uploaded; this checkpoint and its receipts are being committed separately. CI result at discovery is queued, not pass.",
        root_entries_rollback_scope="R13 historical protocol rollback remains preserved; current entries expose R14/R16 observations without adopting that protocol.")
    ctl.write_json(ROOT / "state/checkpoint.json", checkpoint)
print(json.dumps(dict(source_commit=sha, source_ci_status=ci["status"], old_tasks_preserved=len(baseline),
    full_paper=False, full_acceptance=False, final_receipt_commit_not_claimed=True)))
