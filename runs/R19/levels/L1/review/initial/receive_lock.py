from pathlib import Path
import hashlib,json
root=Path.cwd();out=root/'runs/R19/levels/L1/review/initial';rows=[]
for lp in ['runs/R19/levels/L1/review/preparation-lock.json','runs/R19/levels/L1/execution-lock.json']:
 lock=json.loads((root/lp).read_text(encoding='utf-8'))
 for r in lock['files']:
  p=root/r['path']; got=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
  rows.append({'lock':lp,'path':r['path'],'size':p.stat().st_size if p.exists() else None,'expected_size':r['size_bytes'],'expected':r['sha256'],'actual':got,'match':got==r['sha256'] and p.stat().st_size==r['size_bytes']})
(out/'received-lock-verification.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('files',len(rows),'all_match',all(x['match'] for x in rows),'mismatches',[x['path'] for x in rows if not x['match']])
print('src',[(p.name,p.stat().st_size) for p in (root/'runs/R19/levels/L1/execution/src').iterdir() if p.is_file()])
for n in ['fixed_T1','fixed_T2','mixed_count','mixed_cost','single_T1_0','single_T1_1','single_T2_0']:
 p=root/f'runs/R19/levels/L1/execution/results/final/{n}.json'; d=json.loads(p.read_text(encoding='utf-8')); print(n, list(d), 'trucks sample',json.dumps(d.get('trucks',[])[:1],ensure_ascii=False)[:1200])
