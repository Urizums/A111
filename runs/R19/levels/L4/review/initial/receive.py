from pathlib import Path
import json, hashlib, zipfile
ROOT=Path(__file__).resolve().parents[6]
OUT=Path(__file__).parent
E=ROOT/'runs/R19/levels/L4/execution'
def main():
    records=[]
    for loc in ['runs/R19/levels/L4/execution-lock.json','runs/R19/levels/L4/review/preparation-lock.json']:
        lock=json.loads((ROOT/loc).read_text(encoding='utf-8-sig')); checks=[]
        for f in lock['files']:
            p=ROOT/f['path']; actual={'path':f['path'],'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            checks.append({'expected':f,'actual':actual,'match':all(actual[k]==v for k,v in f.items())})
        records.append({'lock':loc,'count':len(checks),'all_match':all(c['match'] for c in checks),'checks':checks})
    assert all(r['all_match'] for r in records)
    (OUT/'receiving-identities.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    consumer=OUT/'consumer';consumer.mkdir(exist_ok=True)
    with zipfile.ZipFile(E/'program_attachment.zip') as z:
        for name in z.namelist():
            target=(consumer/name).resolve()
            if not target.is_relative_to(consumer.resolve()):raise ValueError('archive traversal')
        z.extractall(consumer)
        inventory=z.namelist()
    c=json.loads((OUT/'source-contract.json').read_text(encoding='utf-8'))
    original=json.loads((consumer/'data/instance.json').read_text(encoding='utf-8'))
    rebuilt=json.loads(json.dumps(original))
    for v,raw in zip(rebuilt['vehicles'],c['vehicles']):
        for key,value in [('dims',raw['dims_cm']),('capacity',raw['capacity_kg']),('cost',raw['cost_per_trip_yuan'])]:
            assert v[key]==value
            v[key]=value
    names={'标准件':'standard','易碎件':'fragile','定向件':'oriented'}
    for g,raw in zip(rebuilt['cargo'],c['cargo']):
        for key,value in [('id',raw['type_id']),('class',names[raw['class']]),('dims',raw['dims_cm']),('mass',raw['mass_kg']),('quantity',raw['quantity'])]:
            assert g[key]==value
            g[key]=value
    (consumer/'data/raw_rebuilt.json').write_text(json.dumps(rebuilt,ensure_ascii=False,indent=2),encoding='utf-8')
    receipt={'locks':[{'lock':r['lock'],'count':r['count'],'all_match':r['all_match']} for r in records],
             'archive_members':inventory,'source_fields_exact_match':True,'rerun_data':'consumer/data/raw_rebuilt.json',
             'copied_code_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (consumer/'code').glob('*.py')}}
    (OUT/'receiving-summary.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='archive_members'},ensure_ascii=False))
if __name__=='__main__':main()
