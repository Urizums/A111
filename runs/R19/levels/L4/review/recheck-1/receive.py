from pathlib import Path
import json,hashlib,zipfile,shutil
ROOT=Path(__file__).resolve().parents[6];OUT=Path(__file__).parent;OLD=ROOT/'runs/R19/levels/L4/execution';NEW=ROOT/'runs/R19/levels/L4/execution-v2'
def ident(p):return {'path':p.relative_to(ROOT).as_posix(),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    records=[]
    for loc in ['runs/R19/levels/L4/execution-v2-lock.json','runs/R19/levels/L4/review/initial-lock.json','runs/R19/levels/L4/review/recheck-preparation-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/evaluation-lock.json','runs/R19/levels/L4/design-lock.json']:
        lock=json.loads((ROOT/loc).read_text(encoding='utf-8-sig'));checks=[]
        for f in lock['files']:
            actual=ident(ROOT/f['path']);checks.append({'expected':f,'actual':actual,'match':all(actual[k]==v for k,v in f.items())})
        assert all(c['match'] for c in checks)
        records.append({'lock':loc,'count':len(checks),'all_match':True,'checks':checks})
    (OUT/'receiving-identities.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    reused=[];changed=[]
    for p in sorted(OLD.rglob('*')):
        if p.is_file():
            q=NEW/p.relative_to(OLD)
            equal=q.exists() and ident(p)['sha256']==ident(q)['sha256']
            record={'old':ident(p),'new':ident(q) if q.exists() else None,'same_bytes':equal}
            (reused if equal else changed).append(record)
    (OUT/'old-new-identities.json').write_text(json.dumps({'same_files':reused,'changed_or_missing':changed},ensure_ascii=False,indent=2),encoding='utf-8')
    consumer=OUT/'consumer';consumer.mkdir()
    with zipfile.ZipFile(NEW/'program_attachment.zip') as z:
        for name in z.namelist():
            if not (consumer/name).resolve().is_relative_to(consumer.resolve()):raise ValueError('archive traversal')
        z.extractall(consumer);names=z.namelist()
    codecompare=[]
    for p in (consumer/'code').glob('*.py'):
        q=NEW/'code'/p.name;codecompare.append({'archive':ident(p),'production':ident(q),'equal':ident(p)['sha256']==ident(q)['sha256']})
    assert all(c['equal'] for c in codecompare)
    for name in ['source_audit.py','source_contract.py','independent_checks.py']:
        shutil.copyfile(ROOT/'runs/R19/levels/L4/review/preparation'/name,OUT/name)
    shutil.copyfile(ROOT/'runs/R19/levels/L4/review/initial/consumer/data/raw_rebuilt.json',consumer/'data/raw_rebuilt.json')
    (OUT/'archive-reception.json').write_text(json.dumps({'members':names,'codecompare':codecompare},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'locks':[(r['lock'],r['count'],r['all_match']) for r in records],'same_old_files':len(reused),'changed':[(r['old']['path'],r['new']['path'] if r['new'] else None) for r in changed],'archive_code_match':True},ensure_ascii=False))
if __name__=='__main__':main()
