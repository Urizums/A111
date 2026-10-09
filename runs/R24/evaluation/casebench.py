#!/usr/bin/env python3
"""R24: small deterministic task generator and artifact checker.

Not an agent runner, an independence sandbox, or a behavioral skill evaluation.
Python 3.10+, standard library only. Private oracles must be access-controlled
outside the producer's actual visible workspace by the execution host.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import random
import sys
import tempfile
from pathlib import Path


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def make_case(kind: str, seed: int, root: Path) -> dict:
    if root.exists():
        raise FileExistsError(f"Case already exists; refusing overwrite: {root}")
    rng = random.Random(seed)
    producer, private = root / "producer", root / "private"
    producer.mkdir(parents=True)
    private.mkdir()
    if kind == "extract":
        cities = ["苏州", "厦门", "成都", "青岛", "杭州"]
        source = {
            "ticket": f"R-{rng.randint(1000,9999)}",
            "city": rng.choice(cities),
            "deadline": f"2027-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "notes": "This note is not one of the requested output fields.",
        }
        expected = {"kind":kind, "answer": {"city":source["city"], "deadline":source["deadline"]}}
        task = ("Read input.json. Produce answer.json containing the city and deadline "
                "from the source. Do not create extra project artifacts unless necessary. "
                "Check your two values against the original input.\n")
    elif kind == "two_methods":
        orders = [{"order_id":f"O{i+1}","demand":rng.randint(1,30)} for i in range(rng.randint(3,5))]
        source = {"orders":orders, "methods":["alpha","beta"], "units":"items"}
        # Deliberately both methods must be delivered, even when one is recommended.
        rows=[]
        for method in source["methods"]:
            for order in orders:
                n=order["demand"]
                units=(n+1)//2+4 if method=="alpha" else n+1
                rows.append({"method":method,"order_id":order["order_id"],"units":units})
        totals={m:sum(row["units"] for row in rows if row["method"]==m) for m in source["methods"]}
        winner=min(totals, key=lambda m:(totals[m],m))
        expected={"kind":kind,"rows":rows,"recommendation":{"method":winner}}
        task=("Read input.json. Create proposals.csv with columns method,order_id,units, "
              "including a row for EVERY order under EACH of two methods: "
              "alpha units = ceil(demand/2)+4, beta units = demand+1. "
              "Then create recommendation.json with the method having the lower "
              "sum of units (alphabetical tie-break). Selecting a method DOES NOT "
              "remove the duty to deliver the other method's rows.\n")
    else:
        raise ValueError(f"Unknown case kind: {kind}")
    (producer / "task.md").write_text(task, encoding="utf-8")
    write_json(producer / "input.json", source)
    write_json(private / "expected.json", expected)
    return {"kind":kind,"seed":seed,"producer":str(producer),"private_oracle":str(private / "expected.json")}


def _int_field(value: str) -> int:
    # bool, float, negative and noncanonical string variants should not silently pass.
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ValueError(f"units must be an unsigned integer string: {value!r}")
    return int(value)


def grade(case_root: Path, submission: Path) -> dict:
    oracle=read_json(case_root / "private" / "expected.json")
    kind=oracle["kind"]
    errors=[]
    warnings=[]
    required={"answer.json"} if kind=="extract" else {"proposals.csv","recommendation.json"}
    actual={p.name for p in submission.iterdir() if p.is_file()} if submission.is_dir() else set()
    for name in sorted(required - actual):
        errors.append(f"missing required artifact: {name}")
    extra=sorted(actual-required)
    if extra:
        warnings.append("nonrequired artifacts present; review whether they helped: " + ", ".join(extra))
    if kind=="extract" and "answer.json" in actual:
        try:
            answer=read_json(submission/"answer.json")
            for key,value in oracle["answer"].items():
                if answer.get(key)!=value:
                    errors.append(f"wrong {key}: expected original source value")
            if set(answer)-set(oracle["answer"]):
                warnings.append("answer.json includes nonrequested fields")
        except (OSError, ValueError, json.JSONDecodeError) as e:
            errors.append(f"invalid answer.json: {e}")
    if kind=="two_methods":
        if "proposals.csv" in actual:
            try:
                with (submission/"proposals.csv").open(encoding="utf-8-sig", newline="") as f:
                    reader=csv.DictReader(f)
                    if reader.fieldnames != ["method","order_id","units"]:
                        raise ValueError("CSV columns must be method,order_id,units")
                    rows=list(reader)
                observed={}
                for row in rows:
                    key=(row["method"],row["order_id"])
                    if key in observed:
                        errors.append(f"duplicate row: {key}")
                    observed[key]=_int_field(row["units"])
                expected={(r["method"],r["order_id"]):r["units"] for r in oracle["rows"]}
                for key in sorted(expected.keys()-observed.keys()):
                    errors.append(f"missing method/order output: {key}")
                for key in sorted(observed.keys()-expected.keys()):
                    errors.append(f"unexpected method/order output: {key}")
                for key in sorted(expected.keys() & observed.keys()):
                    if expected[key]!=observed[key]:
                        errors.append(f"wrong units for: {key}")
            except (OSError, UnicodeError, ValueError, csv.Error) as e:
                errors.append(f"invalid proposals.csv: {e}")
        if "recommendation.json" in actual:
            try:
                reco=read_json(submission/"recommendation.json")
                if reco.get("method")!=oracle["recommendation"]["method"]:
                    errors.append("wrong recommended method by original total-units objective")
            except (OSError, ValueError, json.JSONDecodeError) as e:
                errors.append(f"invalid recommendation.json: {e}")
    return {"schema":"forge-r24-check/1","kind":kind,"passed":not errors,
            "errors":errors,"warnings":warnings,
            "scope":"artifact correctness against frozen oracle only; not independence, efficiency, or agent capability"}


def _write_valid(case_root: Path, sub: Path) -> None:
    oracle=read_json(case_root/"private"/"expected.json")
    sub.mkdir()
    if oracle["kind"]=="extract":
        write_json(sub/"answer.json",oracle["answer"])
    else:
        with (sub/"proposals.csv").open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=["method","order_id","units"])
            writer.writeheader();writer.writerows(oracle["rows"])
        write_json(sub/"recommendation.json",oracle["recommendation"])


def selftest() -> dict:
    checks=[]
    def record(name: str, ok: bool):
        checks.append({"name":name,"passed":bool(ok)})
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        c=root/"extract"; make_case("extract",11,c)
        sub=root/"sub1";_write_valid(c,sub)
        record("direct extraction valid",grade(c,sub)["passed"])
        (sub/"README.md").write_text("unnecessary doc",encoding="utf-8")
        extra=grade(c,sub)
        record("extra process artifact warned but not failed",extra["passed"] and bool(extra["warnings"]))
        write_json(sub/"answer.json",{"city":"wrong","deadline":"bad"})
        record("incorrect extraction rejected",not grade(c,sub)["passed"])
        d=root/"both"; make_case("two_methods",22,d)
        sd=root/"sub2";_write_valid(d,sd)
        record("all requested method outputs valid",grade(d,sd)["passed"])
        csvpath=sd/"proposals.csv"
        with csvpath.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
        with csvpath.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["method","order_id","units"]);w.writeheader();w.writerows([r for r in rows if r["method"]=="alpha"])
        record("selected-only method missing other rejected",not grade(d,sd)["passed"])
        with csvpath.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["method","order_id","units"]);w.writeheader();w.writerows(rows)
        rows[0]["units"]=str(int(rows[0]["units"])+1)
        with csvpath.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["method","order_id","units"]);w.writeheader();w.writerows(rows)
        record("incorrect quantity rejected",not grade(d,sd)["passed"])
        _write_valid(d,root/"tmp_valid")
        write_json(root/"tmp_valid"/"recommendation.json",{"method":"invalid"})
        record("wrong objective recommendation rejected",not grade(d,root/"tmp_valid")["passed"])
        try:make_case("extract",11,c);record("cannot overwrite frozen case",False)
        except FileExistsError:record("cannot overwrite frozen case",True)
    return {"schema":"forge-r24-selftest/1","passed":all(x["passed"] for x in checks),"checks":checks,
            "note":"Local deterministic checker tests only; no C13/C14 agent comparison"}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sp=parser.add_subparsers(dest="action",required=True)
    generate=sp.add_parser("generate");generate.add_argument("--kind",choices=["extract","two_methods"],required=True);generate.add_argument("--seed",type=int,required=True);generate.add_argument("--out",type=Path,required=True)
    check=sp.add_parser("grade");check.add_argument("--case",type=Path,required=True);check.add_argument("--submission",type=Path,required=True)
    sp.add_parser("selftest")
    args=parser.parse_args(argv)
    try:
        if args.action=="generate":out=make_case(args.kind,args.seed,args.out)
        elif args.action=="grade":out=grade(args.case,args.submission)
        else:out=selftest()
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        out={"passed":False,"errors":[f"{type(e).__name__}: {e}"]}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out.get("passed",args.action=="generate") else 1

if __name__=="__main__":
    sys.exit(main())
