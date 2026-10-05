#!/usr/bin/env python3
"""Start a local-only successor review record for retained manual decisions."""
import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rules = load(args.rules)
    if rules.get("scope") != "Local follow-up on actual retained manual outcomes only; no real assignments":
        raise ValueError("unexpected successor scope")
    db_uri = f"file:{args.database.resolve()}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT a.ticket_id, a.reason, a.policy_version, a.request_id, "
            "a.new_version, a.decision FROM audit a ORDER BY a.id"
        ).fetchall()
    items = []
    for row in rows:
        if row["decision"] != "manual":
            continue
        reason = row["reason"]
        if reason not in rules["rules"]:
            raise ValueError(f"no successor material rule for {reason}")
        items.append({
            "ticket_id": row["ticket_id"],
            "reason": reason,
            "needed_material": rules["rules"][reason],
            "source_request_id": row["request_id"],
            "source_version": row["new_version"],
            "policy_version": row["policy_version"],
        })
    if not items:
        raise ValueError("no retained manual outcomes to review")
    if rules.get("preserve_source_order") is not True:
        raise ValueError("successor source-order rule is not enabled")
    missing = [
        {"ticket_id": item["ticket_id"], "reason": item["reason"], "needed_material": item["needed_material"]}
        for item in items
    ]
    source_digest = hashlib.sha256(canonical(items).encode("utf-8")).hexdigest()
    task = {
        "schema": "local-demo-manual-review-task/1",
        "task_id": f"manual-review-{source_digest[:16]}",
        "status": "started",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scope": rules["scope"],
        "fictional_local_only": True,
        "external_effects": False,
        "notifications_sent": False,
        "real_assignment": None,
        "source": {
            "database": str(args.database.resolve()),
            "selection": "actual audit rows where decision=manual, ordered by audit id",
            "entry_count": len(items),
        },
        "items": items,
        "missing_materials": missing,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        prior = load(args.out)
        for key in ("schema", "task_id", "status", "scope", "items", "missing_materials"):
            if prior.get(key) != task.get(key):
                raise ValueError("existing successor record differs; refusing overwrite")
        print(json.dumps({"task_id": prior["task_id"], "status": prior["status"], "reused_existing": True}, ensure_ascii=False))
        return
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(task, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    print(json.dumps({"task_id": task["task_id"], "status": task["status"], "reused_existing": False, "entry_count": len(items)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
