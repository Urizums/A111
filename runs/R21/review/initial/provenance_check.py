"""Structural provenance and permitted production-lock byte verification."""
from __future__ import annotations
import base64
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path("runs/R21")
LOCK_PATH = ROOT / "execution-lock.json"
EXEC = ROOT / "execution"
OUT = ROOT / "review/initial"


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def in_scope(rel):
    rel = rel.replace("\\", "/")
    if rel == "runs/R21/execution/prospective-freeze.json":
        return True
    if rel.startswith("runs/R21/execution/source/v1/"):
        return True
    if rel.startswith("runs/R21/execution/science-v1/"):
        return True
    if rel.startswith("runs/R21/execution/inspection-v1/"):
        return rel.endswith(".csv")
    if rel.startswith("runs/R21/execution/paper-final-v4/"):
        return True
    if rel.startswith("runs/R21/execution/commands/") and rel.endswith(".json"):
        return True
    if rel == "runs/R21/execution/command-index.json":
        return True
    return False


lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
entries = {r["path"].replace("\\", "/"): r for r in lock["files"]}
permitted = sorted(p for p in entries if in_scope(p))
checks = []
for rel in permitted:
    p = Path(rel)
    entry = entries[rel]
    actual_size = p.stat().st_size
    actual_hash = sha(p)
    checks.append({"path": rel, "expected_bytes": entry["size_bytes"], "actual_bytes": actual_size, "expected_sha256": entry["sha256"], "actual_sha256": actual_hash, "matches": actual_size == entry["size_bytes"] and actual_hash == entry["sha256"]})

command_files = sorted((EXEC / "commands").glob("*.json"))
command_structure = []
for p in command_files:
    d = json.loads(p.read_text(encoding="utf-8"))
    raw_out = base64.b64decode(d.get("stdout_base64", ""), validate=True)
    raw_err = base64.b64decode(d.get("stderr_base64", ""), validate=True)
    out_eq = raw_out.decode("utf-8", errors="replace") == d.get("stdout", "")
    err_eq = raw_err.decode("utf-8", errors="replace") == d.get("stderr", "")
    begin = d.get("begin", {})
    end = d.get("end", {})
    time_ok = bool(begin.get("utc") and end.get("utc") and datetime.fromisoformat(begin["utc"]) <= datetime.fromisoformat(end["utc"]))
    shape_ok = isinstance(d.get("argv"), list) and bool(d.get("cwd")) and d.get("state") == "finished" and isinstance(d.get("exit_code"), int) and time_ok
    command_structure.append({"path": str(p).replace("\\", "/"), "schema": d.get("schema"), "argv_is_array": isinstance(d.get("argv"), list), "cwd_present": bool(d.get("cwd")), "state": d.get("state"), "exit_code": d.get("exit_code"), "begin_utc": begin.get("utc"), "end_utc": end.get("utc"), "monotonic_begin": begin.get("monotonic_ns"), "monotonic_end": end.get("monotonic_ns"), "stdout_base64_matches_utf8_replace": out_eq, "stderr_base64_matches_utf8_replace": err_eq, "shape_and_time_valid": shape_ok})

index_path = EXEC / "command-index.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
if isinstance(index, dict):
    top_keys = sorted(str(k) for k in index.keys())
    command_field = next((index[k] for k in index if isinstance(k, str) and "command" in k.lower() and isinstance(index[k], (int, list))), None)
    index_count = len(command_field) if isinstance(command_field, list) else command_field
    index_has_streams = any(k in index for k in ("stdout", "stderr", "stdout_base64", "stderr_base64"))
    index_schema = index.get("schema")
else:
    top_keys = []
    index_count = len(index) if isinstance(index, list) else None
    index_has_streams = False
    index_schema = None
index_structure = {"top_level_type": type(index).__name__, "schema": index_schema, "top_level_keys": top_keys, "command_count_field": index_count, "contains_raw_stream_fields": index_has_streams, "sha256": sha(index_path)}

# Bind the index to record metadata only. Never use command output as a scientific answer.
indexed_records = []
for item in index if isinstance(index, list) else []:
    record_path = EXEC / item.get("path", "")
    d = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else {}
    fields = ("argv", "cwd", "exit_code")
    direct_match = all(item.get(k) == d.get(k) for k in fields)
    for k in ("begin", "end"):
        direct_match = direct_match and item.get(k) == d.get(k)
    out_len = len(base64.b64decode(d.get("stdout_base64", ""), validate=True)) if d else None
    err_len = len(base64.b64decode(d.get("stderr_base64", ""), validate=True)) if d else None
    indexed_records.append({"path": item.get("path"), "record_exists": bool(d), "metadata_matches_record": direct_match,
                            "index_has_only_metadata_and_stream_lengths": set(item) == {"path", "argv", "cwd", "begin", "end", "exit_code", "sha256", "raw_stdout_bytes", "raw_stderr_bytes"},
                            "raw_stream_lengths_match_record_base64": item.get("raw_stdout_bytes") == out_len and item.get("raw_stderr_bytes") == err_len})
index_structure["record_metadata_bindings"] = indexed_records
index_structure["all_records_bound"] = len(indexed_records) == index_count and all(x["record_exists"] and x["metadata_matches_record"] and x["index_has_only_metadata_and_stream_lengths"] and x["raw_stream_lengths_match_record_base64"] for x in indexed_records)

identity_path = ROOT / "execution/science-v1/run_identity.json"
identity = json.loads(identity_path.read_text(encoding="utf-8"))
input_lock = json.loads((ROOT / "input-lock.json").read_text(encoding="utf-8"))
protocol_lock = json.loads((ROOT / "protocol-lock.json").read_text(encoding="utf-8"))
clarification_lock = json.loads((ROOT / "clarification-lock.json").read_text(encoding="utf-8"))
prospective = json.loads((EXEC / "prospective-freeze.json").read_text(encoding="utf-8"))
raw_expected = {Path(x["path"]).name: x["sha256"] for x in input_lock["files"] if "/inputs/raw/" in x["path"].replace("\\", "/")}
identity_binding = {
    "identity_argv_binds_frozen_source_and_inputs": identity.get("argv") == ["runs/R21/execution/source/v1/run_science.py", "--raw", "runs/R21/inputs/raw", "--config", "runs/R21/execution/source/v1/config.json", "--newout", "runs/R21/execution/science-v1"],
    "raw_hashes_match_canonical_input_lock": identity.get("raw_hashes") == raw_expected,
    "config_hash_matches_prospective_freeze": identity.get("config_sha256") == prospective["source_hashes"].get("config.json"),
    "source_hashes_match_prospective_freeze": identity.get("source_hashes") == {k: prospective["source_hashes"][k] for k in identity.get("source_hashes", {})},
    "input_lock_sha256": sha(ROOT / "input-lock.json"),
    "protocol_lock_sha256": sha(ROOT / "protocol-lock.json"),
    "clarification_lock_sha256": sha(ROOT / "clarification-lock.json"),
    "input_lock_entry_count": len(input_lock["files"]),
    "protocol_lock_entry_count": len(protocol_lock["files"]),
    "clarification_lock_entry_count": len(clarification_lock["files"]),
}
identity_binding["all_identity_bindings_match"] = all(identity_binding[k] for k in ("identity_argv_binds_frozen_source_and_inputs", "raw_hashes_match_canonical_input_lock", "config_hash_matches_prospective_freeze", "source_hashes_match_prospective_freeze"))

root_freeze_path = ROOT / "production-freeze-command.json"
root_freeze = json.loads(root_freeze_path.read_text(encoding="utf-8"))
root_begin = root_freeze.get("begin", {})
root_end = root_freeze.get("end", {})
root_freeze_structure = {"schema": root_freeze.get("schema"), "argv": root_freeze.get("argv"), "cwd": root_freeze.get("cwd"), "state": root_freeze.get("state"), "exit_code": root_freeze.get("exit_code"), "begin_utc": root_begin.get("utc"), "end_utc": root_end.get("utc"), "stdout_base64_matches_utf8_replace": base64.b64decode(root_freeze.get("stdout_base64", ""), validate=True).decode("utf-8", errors="replace") == root_freeze.get("stdout", ""), "stderr_base64_matches_utf8_replace": base64.b64decode(root_freeze.get("stderr_base64", ""), validate=True).decode("utf-8", errors="replace") == root_freeze.get("stderr", "")}

report = {"schema": "r21-structural-provenance/2", "execution_lock_sha256": sha(LOCK_PATH), "lock_entry_count": len(entries), "permitted_lock_entry_count": len(permitted), "permitted_entries": checks, "all_permitted_lock_entries_match": all(x["matches"] for x in checks), "command_index_structure": index_structure, "command_records_structure": command_structure, "all_command_records_structurally_valid": all(x["shape_and_time_valid"] and x["stdout_base64_matches_utf8_replace"] and x["stderr_base64_matches_utf8_replace"] for x in command_structure), "identity_source_bindings": identity_binding, "production_freeze_receipt_structure_only": root_freeze_structure}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "provenance-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"execution_lock_sha256": report["execution_lock_sha256"], "lock_entries": report["lock_entry_count"], "permitted_entries_checked": len(checks), "all_permitted_lock_entries_match": report["all_permitted_lock_entries_match"], "command_records_checked_structurally": len(command_structure), "all_command_records_structurally_valid": report["all_command_records_structurally_valid"], "command_index_records_bound": index_structure["all_records_bound"], "identity_source_bindings_match": identity_binding["all_identity_bindings_match"], "root_freeze_receipt_structural_state": root_freeze_structure["state"]}, ensure_ascii=False, indent=2))
