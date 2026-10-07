from pathlib import Path
import json,hashlib,difflib,shutil,datetime
ROOT=Path.cwd();OUT=ROOT/'runs/R19/levels/L1/review/recheck-1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for name in ['review/preparation-lock.json','execution-lock.json','execution-v2-lock.json']:
    lp=ROOT/'runs/R19/levels/L1'/name
    for x in json.loads(lp.read_text(encoding='utf-8'))['files']:
        p=ROOT/x['path'];ok=p.is_file()
        rows.append({'lock':name,'path':x['path'],'expected':x['sha256'],'actual':digest(p) if ok else None,'match':ok and p.stat().st_size==x['size_bytes'] and digest(p)==x['sha256']})
(OUT/'received-lock-verification.json').write_text(json.dumps({'files':rows,'all_match':all(x['match'] for x in rows),'count':len(rows)},ensure_ascii=False,indent=2),encoding='utf-8')
assert all(x['match'] for x in rows)
old=ROOT/'runs/R19/levels/L1/execution';new=ROOT/'runs/R19/levels/L1/execution-v2'
srcs=[];diff=[]
for name in sorted(set(p.name for p in (old/'src').glob('*.py'))|set(p.name for p in (new/'src').glob('*.py'))):
    a=old/'src'/name;b=new/'src'/name
    sa=a.read_text(encoding='utf-8') if a.exists() else '';sb=b.read_text(encoding='utf-8') if b.exists() else ''
    srcs.append({'file':name,'old_sha256':digest(a) if a.exists() else None,'new_sha256':digest(b) if b.exists() else None,'changed':sa!=sb})
    diff.extend(difflib.unified_diff(sa.splitlines(True),sb.splitlines(True),fromfile='execution/src/'+name,tofile='execution-v2/src/'+name))
for name in ['README.md','paper/paper.md']:
    a=old/name;b=new/name
    diff.extend(difflib.unified_diff(a.read_text(encoding='utf-8').splitlines(True),b.read_text(encoding='utf-8').splitlines(True),fromfile='execution/'+name,tofile='execution-v2/'+name))
(OUT/'source-differences.diff').write_text(''.join(diff),encoding='utf-8')
(OUT/'source-difference-inventory.json').write_text(json.dumps(srcs,ensure_ascii=False,indent=2),encoding='utf-8')
adapt=[]
initial=OUT.parent/'initial'
for name in ['independent_audit.py','audit_experiments.py','paper_crosscheck.py','run_receipt.py']:
    p=initial/name;s=p.read_text(encoding='utf-8');r=s
    if name=='independent_audit.py':r=r.replace("EXEC=ROOT/'runs/R19/levels/L1/execution'","EXEC=ROOT/'runs/R19/levels/L1/execution-v2'")
    if name=='run_receipt.py':r=r.replace('runs/R19/levels/L1/execution','runs/R19/levels/L1/execution-v2')
    (OUT/name).write_text(r,encoding='utf-8')
    adapt.append({'file':name,'frozen_initial_sha256':digest(p),'copy_sha256':digest(OUT/name),'adaptation':'execution-root path only' if s!=r else 'identical own method; output root naturally current file parent'})
(OUT/'method-adaptations.json').write_text(json.dumps(adapt,ensure_ascii=False,indent=2),encoding='utf-8')
unchanged=[]
for rel in ['configs/base.json','configs/experiments.json']+[p.relative_to(old).as_posix() for p in (old/'results/final').glob('*') if p.is_file()]+[p.relative_to(old).as_posix() for p in (old/'results/sensitivity').glob('*.json')]:
    a=old/rel;b=new/rel;unchanged.append({'relative':rel,'old_sha256':digest(a),'new_sha256':digest(b) if b.exists() else None,'identical':b.exists() and digest(a)==digest(b)})
(OUT/'numerical-version-comparison.json').write_text(json.dumps(unchanged,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'locks_match':True,'count':len(rows),'changed_source_files':[s['file'] for s in srcs if s['changed']],'numerical_records_compared':len(unchanged),'numerical_records_all_identical':all(x['identical'] for x in unchanged)},ensure_ascii=False))
