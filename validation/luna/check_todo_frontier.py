#!/usr/bin/env python3
"""Read-only dependency and recovery-frontier check for the exported handoff."""
from __future__ import annotations

import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def graph_report(tasks: list[dict]) -> dict:
    ids = [task.get("id") for task in tasks]
    idset = set(ids)
    missing = []
    graph = {task["id"]: [dep for dep in task.get("depends_on", []) if dep in idset] for task in tasks if task.get("id")}
    for task in tasks:
        for dependency in task.get("depends_on", []) or []:
            if dependency not in idset:
                missing.append({"task_id": task.get("id"), "missing_dependency": dependency})

    state: dict[str, int] = {}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if state.get(node) == 1:
            cycles.append(stack[stack.index(node):] + [node])
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        stack.append(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        stack.pop()
        state[node] = 2

    for node in graph:
        visit(node)
    return {
        "task_count": len(tasks),
        "unique_ids": len(idset) == len(ids),
        "missing_dependencies": missing,
        "cycles": cycles,
        "status_counts": dict(collections.Counter(task.get("status") for task in tasks)),
    }


def main() -> int:
    phase = json.loads((ROOT / "state/phase-todo.json").read_text(encoding="utf-8"))
    project = json.loads((ROOT / "state/project-todo.json").read_text(encoding="utf-8"))
    checkpoint = json.loads((ROOT / "state/checkpoint.json").read_text(encoding="utf-8"))
    audit_plan = json.loads((ROOT / "runs/S01/audit-plan.json").read_text(encoding="utf-8"))
    phase_tasks = {task["id"]: task for task in phase["tasks"]}
    current = phase_tasks[checkpoint["next_task_id"]]
    current_dependencies_ready = all(phase_tasks[dep]["status"] == "done" for dep in current.get("depends_on", []))
    final = phase["tasks"][-1]
    transition = final.get("transition", {})
    missing_inputs = [path for path in audit_plan.get("inputs", []) if not (ROOT / path).exists()]

    result = {
        "schema": "luna-todo-frontier-check/1",
        "phase_graph": graph_report(phase["tasks"]),
        "project_graph": graph_report(project["todo"]),
        "frontier": {
            "checkpoint_active_phase": checkpoint.get("active_phase"),
            "phase_id": phase.get("phase_id"),
            "checkpoint_next_task_id": checkpoint.get("next_task_id"),
            "checkpoint_matches_phase": checkpoint.get("active_phase") == phase.get("phase_id") and checkpoint.get("next_task_id") in phase_tasks,
            "next_task_status": current.get("status"),
            "next_task_dependencies": current.get("depends_on", []),
            "next_task_dependencies_ready": current_dependencies_ready,
            "next_task_write_paths": current.get("write_paths", []),
            "audit_plan_inputs_present": not missing_inputs,
            "missing_audit_plan_inputs": missing_inputs,
            "final_task_id": final.get("id"),
            "final_task_dependencies": final.get("depends_on", []),
            "final_task_dependencies_done_now": all(phase_tasks[dep]["status"] == "done" for dep in final.get("depends_on", [])),
            "final_task_status": final.get("status"),
            "transition_todo_path": transition.get("todo_path"),
            "transition_first_task_id": transition.get("first_task_id"),
            "transition_start_evidence": transition.get("start_evidence", []),
            "transition_metadata_complete": bool(transition.get("todo_path") and transition.get("first_task_id") and transition.get("start_evidence")),
        },
    }
    output = ROOT / "validation/luna/todo-frontier.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output.relative_to(ROOT)),
        "phase_missing_dependencies": len(result["phase_graph"]["missing_dependencies"]),
        "phase_cycles": len(result["phase_graph"]["cycles"]),
        "project_missing_dependencies": len(result["project_graph"]["missing_dependencies"]),
        "project_cycles": len(result["project_graph"]["cycles"]),
        "current_frontier_ready": current_dependencies_ready and not missing_inputs,
        "next_task_id": checkpoint.get("next_task_id"),
        "final_transition_metadata_complete": result["frontier"]["transition_metadata_complete"],
    }, ensure_ascii=False))
    return 0 if not missing_inputs and not result["phase_graph"]["missing_dependencies"] and not result["project_graph"]["missing_dependencies"] and not result["phase_graph"]["cycles"] and not result["project_graph"]["cycles"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
