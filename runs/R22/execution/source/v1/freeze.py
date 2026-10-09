from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
repo=Path.cwd();ex=repo/'runs/R22/execution';src=ex/'source/v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
target=src/'reference_policy.py';assert not target.exists();shutil.copyfile(repo/'runs/R21/execution/source/v1/reference_policy.py',target)
paths=[]
for lockpath in ['runs/R21/input-lock.json','runs/R22/protocol-lock.json','runs/R20/final/candidate/C13-lock.json']:
    obj=json.loads((repo/lockpath).read_text('utf-8'))
    for f in obj['files']:
        p=repo/f['path'];assert p.stat().st_size==f['size_bytes'] and sha(p)==f['sha256'];paths.append(f['path'])
paths += ['runs/R21/execution/source/v1/'+n for n in ['config.json','reference_policy.py','run_science.py','freeze.py']]
sc=repo/'runs/R21/execution/science-v1'
paths += [str(p.relative_to(repo)).replace('\\','/') for pattern in ['data/train_*.csv','data/train_features_*.csv','data/predict_features_*.csv','data/promotion_imputation_sources_*.csv','models/coefficients_*.json','uncertainty/residual_coordinates_all.csv'] for p in sc.glob(pattern)]
old=json.loads((repo/'runs/R21/execution-lock.json').read_text('utf-8'));ident={f['path']:f for f in old['files']}
for path in paths:
    if path in ident:assert sha(repo/path)==ident[path]['sha256']
oldfreeze=json.loads((repo/'runs/R21/execution/prospective-freeze.json').read_text('utf-8'))
for n,h in oldfreeze['source_hashes'].items():assert sha(repo/'runs/R21/execution/source/v1'/n)==h
paths += ['runs/R21/input-lock.json','runs/R21/execution-lock.json','runs/R21/execution/prospective-freeze.json','runs/R22/protocol-lock.json','runs/R20/final/candidate/C13-lock.json']
obj={'schema':'r22-prospective-freeze/1','actual_frozen_at_utc':datetime.now(timezone.utc).isoformat(),'authorized_source_identities':[{'path':p,'sha256':sha(repo/p)} for p in sorted(set(paths))],'scientific_source_identities':[{'path':str(p.relative_to(repo)).replace('\\','/'),'sha256':sha(p)} for p in sorted(src.iterdir()) if p.is_file()]+[{'path':'runs/R22/execution/WORKFLOW.md','sha256':sha(ex/'WORKFLOW.md')}],'claim':'actual freeze before first fit, author identity evidence only','model':None,'tokens':None,'cost':None}
with (ex/'prospective-freeze.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print('frozen',obj['actual_frozen_at_utc'],len(paths),'authorized identities')
