#!/usr/bin/env python3
"""Independently recompute frozen project expense totals with Decimal/integer fen."""
import csv, hashlib, json
from decimal import Decimal
from pathlib import Path
ROOT=Path('/workspace/A111')
source=ROOT/'evidence/c1/materials/expenses.csv'
rows=list(csv.DictReader(source.open(encoding='utf-8-sig', newline='')))
by={}
for row in rows:
    amount=Decimal(row['amount_yuan'])
    fen=amount*100
    if fen != fen.to_integral_value():
        raise SystemExit(f'non-integral fen amount for {row["id"]}')
    cat=row['category']
    by.setdefault(cat, {'category':cat,'count':0,'total_fen':0,'ids':[]})
    by[cat]['count']+=1
    by[cat]['total_fen']+=int(fen)
    by[cat]['ids'].append(row['id'])
expected={
    'schema':'independent-project-expected/1',
    'basis':{'source':'evidence/c1/materials/expenses.csv','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rule':'Sort categories lexicographically; integer fen; source row order within each ID list.'},
    'row_count':len(rows),
    'categories':[by[k] for k in sorted(by)],
}
out=ROOT/'runs/S01/cloud-audit/worker/analysis/expected_project_summary.json'
out.write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(out),'row_count':len(rows),'category_count':len(by),'source_sha256':expected['basis']['source_sha256']},ensure_ascii=False))
