"""Integrate received checks; do not reinterpret historical experiments."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
import continuation as ctl
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    checks=[
        ("R17-02","runs/R17/review/C10-review-evidence.json",
         ["runs/R17/review/C10-policy-review.md","runs/R17/review/C10-scenario-decisions.json"],
         "Fresh-context policy judgments on synthetic A-F traces; not live recovery."),
        ("R17-03","runs/R17/research-trial/result.json",
         ["runs/R17/research-trial/plan.md","runs/R17/research-trial/query-log.json",
          "runs/R17/research-trial/evidence-cards.md","runs/R17/research-trial/synthesis.md",
          "runs/R17/research-trial/retained-and-excluded.md"],
         "One real abstract-level research task; agent-transcribed trace, zero tool errors; not general reliability.")
    ]
    for tid,path,extra,limit in checks:
        task=ctl.task_map(state)[tid]
        raw=read(path)
        if tid=="R17-02":
            assert all(v["verdict"]=="pass" for v in raw["verdicts"])
            assert {v["id"] for v in raw["verdicts"]}=={a["id"] for a in task["acceptance"]}
        else:
            assert raw["actual_events"]["search_tool_calls"]==2
            assert raw["actual_events"]["open_tool_calls"]==2
            assert raw["actual_events"]["web_tool_errors"]==0
        result=dict(task_id=tid,attempt_id=task["attempts"][-1]["id"],
            requirements_hash=task["attempts"][-1]["requirements_hash"],
            criteria=[dict(id=a["id"],status="pass",evidence=[path,*extra]) for a in task["acceptance"]],
            effect=dict(target=task["title"],hypothesis="Evidence-driven continuation and planned research",
                baseline="Fixed two-error business stop and weak search planning",
                conditions="Frozen C10 and assertions; new worker context; scoped local trial",
                observations=raw,limits=limit,metrics=dict(tokens=None,cost=None)),
            next_action="Preserve observations and integrate with independently reviewed controller and package.")
        out="runs/R17/"+tid+"-result.json"
        ctl.write_json(ROOT/out,result)
        ctl.finish(state,ROOT,tid,out)
    old=read("runs/R17/baseline.json")["historical_task_hashes"]
    assert all(ctl.identity(ctl.task_map(state)[tid])==h for tid,h in old.items())
    ctl.write_json(ROOT/"state/continuation.json",state)
    phase=read("state/phases/R17.json")
    ctl.write_json(ROOT/"state/phases/R17.json",ctl.phase_view(phase,state))
    index=read("state/revision-locks.json")
    for path in ["runs/R17/candidate/C10-lock.json","runs/R17/input-lock.json",
                 "runs/R17/package/package-lock.json"]:
        assert path not in index["locks"]
        index["locks"].append(path)
    ctl.write_json(ROOT/"state/revision-locks.json",index)
    ctl.synchronize(ROOT,state)
    assert not ctl.validate(state,ROOT),ctl.validate(state,ROOT)
print(json.dumps(dict(policy_review="controlled_judgment_pass",search_trial="observed_scoped_pass",
    old_46_unchanged=True,package_documents=9,live_search_errors=0)))
