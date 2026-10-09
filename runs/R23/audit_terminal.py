"""Audit actual actor lock bytes and command records without judging their claims."""
import hashlib
import json
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R23'
p=argparse.ArgumentParser();p.add_argument('--out',default='runs/R23/terminal-audit.json');p.add_argument('--locks',nargs='+',default=['design-lock.json','reception-preparation-lock.json','execution-lock.json']);args=p.parse_args()
rows=[]
for rel in args.locks:
    lock=json.loads((BASE/rel).read_text(encoding='utf-8'));commands=[];invalid=[]
    for entry in lock['files']:
        p=ROOT/entry['path'];b=p.read_bytes()
        assert len(b)==entry['size_bytes'] and hashlib.sha256(b).hexdigest()==entry['sha256'],entry['path']
        if p.suffix not in {'.json','.txt'}:continue
        try:j=json.loads(b)
        except (ValueError,UnicodeDecodeError):
            assert not {'receipts','records'}.intersection(p.parts),entry['path']
            if p.suffix=='.json':invalid.append(entry['path'])
            continue
        if isinstance(j,dict) and j.get('schema')=='forge-command-record/1':
            assert j['state']=='finished' and isinstance(j['exit_code'],int) and j.get('end'),entry['path']
            commands.append(dict(path=entry['path'],exit_code=j['exit_code'],begin=j['begin'],end=j['end']))
    rows.append(dict(lock='runs/R23/'+rel,files=len(lock['files']),commands=len(commands),nonzero=sum(c['exit_code']!=0 for c in commands),historical_invalid_json=invalid,records=commands))
out=ROOT/args.out
with out.open('x',encoding='utf-8') as f:json.dump(dict(schema='r23-terminal-byte-audit/1',scopes=rows,claim='Byte identities and command terminal states only; no substantive or independence verdict.'),f,ensure_ascii=False,indent=2)
print(json.dumps([dict(lock=r['lock'],files=r['files'],commands=r['commands'],nonzero=r['nonzero'],invalid_json=len(r['historical_invalid_json'])) for r in rows]))
