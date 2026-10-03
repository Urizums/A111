import csv, hashlib, json, pathlib
RUN = pathlib.Path(__file__).resolve().parents[1]
ROOT = RUN.parent.parent
SOURCE = ROOT / "materials" / "expenses.csv"
SUMMARY = RUN / "artifacts" / "summary.json"
MARKDOWN = RUN / "artifacts" / "summary_zh.md"
REPLY = RUN / "artifacts" / "worker-reply.json"
REQUEST = RUN / "job" / "request.json"
CHECK_REPLY = RUN / "artifacts" / "logs" / "check-reply.json"
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
grouped = {}
with SOURCE.open(encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        fen = __import__("decimal").Decimal(row["amount_yuan"]) * 100
        if fen != fen.to_integral_value():
            raise ValueError("source amount is not an exact integer fen")
        item = grouped.setdefault(row["category"], {"row_count": 0, "total_fen": 0, "ids": []})
        item["row_count"] += 1
        item["total_fen"] += int(fen)
        item["ids"].append(row["id"])
expected = {key: grouped[key] for key in sorted(grouped)}
actual = json.loads(SUMMARY.read_text(encoding="utf-8"))
markdown = MARKDOWN.read_text(encoding="utf-8")
request = json.loads(REQUEST.read_text(encoding="utf-8"))
reply = json.loads(REPLY.read_text(encoding="utf-8"))
captured_check = json.loads(CHECK_REPLY.read_text(encoding="utf-8"))
checks = {
    "json_exactly_matches_raw_csv": actual == expected,
    "category_keys_sorted": list(actual) == sorted(actual),
    "all_ids_and_row_counts_match": all(actual.get(k) == expected[k] for k in expected),
    "markdown_rows_match_raw_csv": all("| {} | {} | {} | {} |".format(k, v["row_count"], v["total_fen"], ", ".join(v["ids"])) in markdown for k, v in expected.items()),
    "markdown_chinese_explanation_present": "费用分类汇总" in markdown and "金额以 Decimal 按 1 元 = 100 分精确换算" in markdown,
    "reply_binds_to_actual_request": reply.get("schema_version") == "forge-host-reply/1" and reply.get("job_id") == request["request"]["job_id"] and reply.get("attempt_id") == request["request"]["attempt_id"] and reply.get("request_hash") == request["request_hash"],
    "reply_result_matches_json": reply.get("result") == actual,
    "reply_artifact_hashes_match": all(pathlib.Path(x["path"]).is_file() and digest(pathlib.Path(x["path"])) == x["sha256"] for x in reply.get("artifacts", [])),
    "captured_check_reply_payload_valid": captured_check.get("exit_code") == 0 and json.loads(captured_check.get("stdout", "{}")).get("status") == "payload_valid",
}
result = {
    "schema_version": "forge-independent-source-check/1",
    "source_sha256": digest(SOURCE),
    "summary_sha256": digest(SUMMARY),
    "markdown_sha256": digest(MARKDOWN),
    "reply_sha256": digest(REPLY),
    "checks": checks,
    "pass": all(checks.values()),
    "source_derived": expected,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
