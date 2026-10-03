"""Read-only independent C1 source recomputation; no old effects."""
import csv,hashlib,json
from decimal import Decimal
from pathlib import Path
root=Path(__file__).resolve().parents[2];source=root/'evidence/c1/materials/expenses.csv';groups={}
for row in csv.DictReader(source.open()):
 g=groups.setdefault(row['category'],{'row_count':0,'total_fen':0,'ids':[]})
 g['row_count']+=1;g['total_fen']+=int(Decimal(row['amount_yuan'])*100);g['ids'].append(row['id'])
checks=[]
for sample in ['A1','B1','B2','A2']:
 path=root/f'evidence/c1/project/{sample}/artifacts/summary.json'
 obj=json.loads(path.read_text());obj=obj.get('categories',obj)
 normalized={k:{'row_count':v['row_count'],'total_fen':v.get('total_fen',v.get('total_amount_fen')),'ids':v.get('ids',v.get('source_ids'))} for k,v in obj.items()}
 checks.append({'sample':sample,'path':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'matches':normalized==groups})
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'expected':groups,'samples':checks,'scope':'A2 is cutoff output only, never lifecycle completion; zero old native or controller calls.'}
print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(not all(c['matches'] for c in checks))
