#!/usr/bin/env python3
"""Root source checks only; protocol, authority and capture are separate grades."""
import csv,json,hashlib
from decimal import Decimal
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((BASE/'materials/expenses.csv').open()))
expected={}
for r in rows:
 value=Decimal(r['amount_yuan'])*100
 assert value==value.to_integral_value()
 entry=expected.setdefault(r['category'],{'rows':0,'fen':0,'ids':[]})
 entry['rows']+=1;entry['fen']+=int(value);entry['ids'].append(r['id'])
notes=(BASE/'materials/notes.txt').read_text()
# Literal original commitments, not inferred owners or normalized relative dates.
actions=[{'task':'更新部署文档','owner':'赵宁','due':'周五','source_quote':'赵宁负责更新部署文档，截止周五。'}, {'task':'补充回归用例','owner':'许静','due':'2026-10-09','source_quote':'许静负责补充回归用例，截止2026-10-09。'}, {'task':'补充日志告警','owner':None,'due':None,'source_quote':'决定补充日志告警。'}]
checks=[]
for block,order in [('project',['A1','B1','B2','A2']),('package',['B1','A1','A2','B2'])]:
 for name in order:
  run=(BASE/'coordinator/cutoff-snapshot'/block/name) if block=='project' and (BASE/'coordinator/cutoff-snapshot/Snapshot_Manifest.json').exists() else BASE/block/name
  path=run/'artifacts'/('summary.json' if block=='project' else 'actions.json')
  item={'block':block,'sample':name,'status':'pending','protocol_grade':'separate','scope_grade':'separate','original_acceptance_grade':'separate'}
  if path.exists():
   try:
    data=json.loads(path.read_text())
    if block=='project':
     categories=data.get('categories',data)
     normalized={k:{'rows':v['row_count'],'fen':v.get('total_amount_fen',v.get('total_fen')),'ids':v.get('source_ids',v.get('ids'))} for k,v in categories.items()}
     equal=normalized==expected
    else:
     actual=data if isinstance(data,list) else data.get('artifacts',{}).get('actions',data.get('actions'))
     # Exact task spelling is an executable convenience; equivalent wording gets human review.
     equal=isinstance(actual,list) and len(actual)==len(actions) and sorted(actual,key=lambda x:x['source_quote'])==sorted(actions,key=lambda x:x['source_quote']) and all(x['source_quote'] in notes for x in actual)
    item.update(status='source_fields_match' if equal else 'needs_human_review',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),path=str(path),actual=data)
   except (ValueError,KeyError,TypeError) as e:item.update(status='needs_human_review',reason=str(e))
  checks.append(item)
result={'reviewer':'Root','expected_csv_independently_recomputed':expected,'notes_commitments_read_from_original':actions,'samples':checks,'Chinese_explanation':'independent human inspection, recorded in Root_Source_Review.md','scope':'Business fields only; no automatic aggregate pass or speed claim'}
(BASE/'coordinator/Root_Source_Computation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'block':x['block'],'sample':x['sample'],'status':x['status']} for x in checks],ensure_ascii=False))
