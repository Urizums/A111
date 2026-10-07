from pathlib import Path
import json, re, hashlib
root=Path.cwd(); out=root/'runs/R19/levels/L1/review/preparation'
data=json.loads((out/'official-source-extraction.json').read_text(encoding='utf-8'))
doc=next(s for s in data['sources'] if s['path'].endswith('.docx'))
table=next(e for e in doc['body'] if e['kind']=='table')
items=[]
for row in table['rows'][1:]:
 cells={c['col']:c['text'] for c in row['cells']}
 dims=[int(x) for x in re.findall(r'\d+',cells[3])]
 w=int(cells[4]); q=int(cells[5]); v=dims[0]*dims[1]*dims[2]
 items.append({'type_id':cells[1],'category':cells[2],'dimensions_cm':dims,'unit_weight_kg':w,'quantity':q,'unit_volume_cm3':v,'total_volume_cm3':v*q,'total_weight_kg':w*q,'source':f'附件1.docx body[22] table row {row["row"]} columns 1..5'})
ledger={'status':'source_review_prepared_artifacts_pending','classification':'raw_data_arithmetic_controls_not_solution','items':items,'total_quantity':sum(e['quantity'] for e in items),'total_weight_kg':sum(e['total_weight_kg'] for e in items),'total_volume_cm3':sum(e['total_volume_cm3'] for e in items),'total_volume_m3':sum(e['total_volume_cm3'] for e in items)/1e6,'formula':'unit_volume_cm3=L*W*H; total=sum(quantity*unit_value); 1 m3=1000000 cm3','claim_limit':'原件批次守恒校核量，不是车型数/费用/装载率答案或优化界。'}
(out/'raw-inventory-controls.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
checks=[]
for lock_name in ['runs/R19/evaluation-lock.json','runs/R19/levels/L1/design-lock.json']:
 lock=json.loads((root/lock_name).read_text(encoding='utf-8'))
 for e in lock['files']:
  p=root/e['path']; got=hashlib.sha256(p.read_bytes()).hexdigest()
  checks.append({'lock':lock_name,'path':e['path'],'expected':e['sha256'],'actual':got,'matches':got==e['sha256'],'actual_bytes':p.stat().st_size})
(out/'input-lock-verification.json').write_text(json.dumps({'status':'source_review_prepared_artifacts_pending','checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'inventory_controls':{k:ledger[k] for k in ['total_quantity','total_weight_kg','total_volume_cm3','total_volume_m3']},'lock_checks':len(checks),'all_locked_bytes_match':all(c['matches'] for c in checks)},ensure_ascii=False))
