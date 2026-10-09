"""Compare the explicit clean replay to the independent raw reconstruction."""
from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INITIAL = ROOT / "runs/R22/review/initial"
RECEIPT = INITIAL / "receipts/46-clean-explicit-output-rerun.json"
CLEAN = INITIAL / "clean-rerun-v1"


def main():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    argv = receipt.get("argv", [])
    expected = [
        "py", "-3.12", "-X", "utf8", "-B", "runs/R22/execution/source/v1/run_replay.py",
        "--raw", "runs/R21/inputs/raw", "--config", "runs/R22/execution/source/v1/config.json",
        "--newout", "runs/R22/review/initial/clean-rerun-v1",
    ]
    if receipt.get("state") != "finished" or receipt.get("exit_code") != 0 or argv != expected:
        raise AssertionError("clean replay receipt does not prove the required explicit successful run")
    for stream in ("stdout", "stderr"):
        plain = receipt.get(stream, "").encode("utf-8")
        encoded = base64.b64decode(receipt.get(f"{stream}_base64", ""))
        if plain != encoded:
            raise AssertionError(f"{stream} capture is incomplete or inconsistent")
    run_identity = json.loads((CLEAN / "run_identity.json").read_text(encoding="utf-8"))
    if run_identity.get("argv") != expected[5:]:
        raise AssertionError("clean output identity does not retain exact argv")
    raw_hashes = run_identity.get("raw_hashes", {})
    if len(raw_hashes) != 7:
        raise AssertionError("clean output identity lacks raw file identities")

    # Reuse the frozen row-wise comparator with its production-table root set to the new clean output.
    comparator_path = INITIAL / "source/compare_reconstruction_v2.py"
    spec = importlib.util.spec_from_file_location("comparison_v2", comparator_path)
    comparator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comparator)
    comparison_dir = INITIAL / "clean-comparison"
    comparison_dir.mkdir(parents=True, exist_ok=False)
    comparator.PRODUCTION = CLEAN
    comparator.REPORT = comparison_dir
    comparator.main()
    comparison = json.loads((comparison_dir / "comparison-v2.json").read_text(encoding="utf-8"))
    result = {
        "schema": "r22-clean-rerun-equivalence/1",
        "receipt": {
            "state": receipt["state"], "exit_code": receipt["exit_code"], "argv": argv,
            "begin": receipt.get("begin"), "end": receipt.get("end"),
            "stdout_bytes": len(receipt.get("stdout", "").encode("utf-8")),
            "stderr_bytes": len(receipt.get("stderr", "").encode("utf-8")),
            "full_stream_capture_verified": True,
        },
        "raw_and_config_identity": {"raw_files": raw_hashes, "config_sha256": run_identity.get("config_sha256"), "source_hashes": run_identity.get("source_hashes")},
        "all_table_comparisons_pass": comparison["all_table_comparisons_pass"],
        "all_scenario_comparisons_pass": comparison["all_scenario_comparisons_pass"],
        "comparison_file": (comparison_dir / "comparison-v2.json").relative_to(ROOT).as_posix(),
        "interpretation": "explicit clean replay compared row-by-row to the separately frozen raw reconstruction; replay does not replace independent reconstruction",
        "actual_model": None, "tokens": None, "cost": None,
    }
    out = INITIAL / "clean-rerun-equivalence.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"clean_rerun_finished": True, "tables_pass": result["all_table_comparisons_pass"], "scenarios_pass": result["all_scenario_comparisons_pass"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
