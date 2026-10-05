#!/usr/bin/env python3
"""Local, source-bound equipment allocation advice. No approval or notification effects."""
import argparse, csv, hashlib, json, re, sys
from pathlib import Path

def digest(path):
    raw=path.read_bytes()
    return {"file":path.name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def read_csv(path, required):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or any(k not in reader.fieldnames for k in required):
            raise ValueError(f"{path.name} missing required columns")
        return [(line, row) for line,row in enumerate(reader,start=2)]

def allocate(equipment_path, requests_path, rules_path):
    equipment_rows=read_csv(equipment_path,["equipment_id","name","available_units"])
    requests=read_csv(requests_path,["request_id","equipment_id","units","date","priority","submitted_at","room"])
    rules=json.loads(rules_path.read_text(encoding="utf-8"))
    priorities=rules.get("priority_order")
    if not isinstance(priorities,list) or not priorities or any(not isinstance(x,str) for x in priorities):
        raise ValueError("rules.priority_order must be a non-empty string array")
    ready_clause=rules.get("complete_statuses",{}).get("ready")
    conflict_clause=rules.get("complete_statuses",{}).get("conflict")
    incomplete_clause=rules.get("incomplete")
    if not all(isinstance(x,str) and x for x in (ready_clause,conflict_clause,incomplete_clause)):
        raise ValueError("rules must define incomplete and both complete_statuses")
    inventory={}
    for line,row in equipment_rows:
        key=row.get("equipment_id","")
        try: count=int(row.get("available_units",""))
        except (TypeError,ValueError): raise ValueError(f"equipment row {line}: available_units must be an integer")
        if not key or count < 0: raise ValueError(f"equipment row {line}: invalid id or available_units")
        inventory[key]=count
    prepared=[]
    for line,row in requests:
        reasons=[]
        equipment_id=row.get("equipment_id","")
        if equipment_id not in inventory: reasons.append(f"unknown equipment_id {equipment_id}")
        if not row.get("room","").strip(): reasons.append("missing room")
        raw_units=row.get("units","")
        if not re.fullmatch(r"[0-9]+",raw_units or "") or int(raw_units or "0") <= 0:
            reasons.append("units is not a positive integer")
        for field in ("date","priority","submitted_at"):
            if not row.get(field,"").strip(): reasons.append(f"missing {field}")
        if row.get("priority") not in priorities: reasons.append("priority is not in priority_order")
        prepared.append({"line":line,"record":row,"reasons":reasons,"units":int(raw_units) if re.fullmatch(r"[0-9]+",raw_units or "") and int(raw_units or "0")>0 else None})
    complete=[p for p in prepared if not p["reasons"]]
    complete.sort(key=lambda p:(priorities.index(p["record"]["priority"]),p["record"]["submitted_at"],p["record"]["request_id"]))
    order=[]; decisions={}; balances={}; initial={}
    for rank,p in enumerate(complete,start=1):
        r=p["record"]; key=(r["equipment_id"],r["date"])
        if key not in balances:
            balances[key]=inventory[r["equipment_id"]]; initial[key]=inventory[r["equipment_id"]]
        remaining=balances[key]; order.append(r["request_id"])
        if p["units"] <= remaining:
            balances[key]-=p["units"]
            decisions[p["line"]]={"status":"ready","allocation_order":rank,"advice":f"建议调配{p['units']}件（本地建议）","reason":f"请求{p['units']}件，处理前库存{remaining}件，库存足够。","rule_basis":ready_clause}
        else:
            decisions[p["line"]]={"status":"conflict","allocation_order":rank,"advice":"库存不足，暂不建议调配","reason":f"请求{p['units']}件，处理时剩余库存{remaining}件，库存不足。","rule_basis":conflict_clause}
    out=[]
    for p in prepared:
        if p["line"] in decisions:
            d=decisions[p["line"]]
        else:
            d={"status":"needs_info","allocation_order":None,"advice":"需补齐资料或核实器材清单后再给建议","reason":"；".join(p["reasons"])+"；未占用库存。","rule_basis":incomplete_clause}
        out.append({"source_row":p["line"],"request_id":p["record"].get("request_id",""),"priority":p["record"].get("priority",""),"record":p["record"],**d})
    inv=[{"equipment_id":e,"date":d,"initial_units":initial[(e,d)],"remaining_units":balances[(e,d)]} for e,d in sorted(balances)]
    counts={s:sum(1 for x in out if x["status"]==s) for s in ("ready","conflict","needs_info")}
    return {"schema":"local-equipment-advice/1","scope":rules.get("scope","本地建议；不代表实际审批或发送通知"),"source_files":[digest(equipment_path),digest(requests_path),digest(rules_path)],"processing_order":order,"inventory_after":inv,"summary":counts,"requests":out}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--equipment",type=Path,required=True);p.add_argument("--requests",type=Path,required=True);p.add_argument("--rules",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        result=allocate(a.equipment,a.requests,a.rules)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        a.out.write_text(raw,encoding="utf-8")
        sys.stdout.write(raw)
        return 0
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as e:
        sys.stderr.write(json.dumps({"error":str(e)},ensure_ascii=False)+"\n");return 2
if __name__=="__main__":raise SystemExit(main())
