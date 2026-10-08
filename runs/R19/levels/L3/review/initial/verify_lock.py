import hashlib,json,time,sys
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]
label=sys.argv[1]
t=time.perf_counter(); lock=ROOT/'runs/R19/levels/L3/execution-lock.json'
obj=json.loads(lock.read_text(encoding='utf-8')); items=[]
for row in obj['files']:
    p=ROOT/row['path']; b=p.read_bytes()
    items.append({'path':row['path'],'size':len(b),'matches':hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['size_bytes']})
files={str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'runs/R19/levels/L3/execution').rglob('*') if p.is_file()}
listed={r['path'] for r in obj['files']}
result={'label':label,'utc':datetime.now(timezone.utc).isoformat(),'lock_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),
        'listed_count':len(items),'actual_count':len(files),'all_bytes_match':all(r['matches'] for r in items),
        'unlisted':sorted(files-listed),'missing':sorted(listed-files),'elapsed_seconds':time.perf_counter()-t,
        'mismatches':[x for x in items if not x['matches']]}
(HERE/f'lock-{label}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False)); assert result['all_bytes_match'] and not result['unlisted'] and not result['missing']
