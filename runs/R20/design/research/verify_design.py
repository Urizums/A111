"""Author packaging check and fresh CSV numerical recomputation; not independent acceptance."""
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path('runs/R20/design')

def main():
    skill = ROOT/'forge-freshfood-flow'
    assert (ROOT/'research/smoke-invocation-003.py').is_file(), 'historical source archive absent'
    paths = list(skill.rglob('*'))
    assert all(p.suffix == '.md' for p in paths if p.is_file())
    links=[]
    for p in paths:
        if not p.is_file():
            continue
        for dest in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            assert (p.parent/dest).is_file(), (p,dest)
            links.append({'from':p.as_posix(),'to':dest})
    with Path('runs/R20/inputs/raw/items.csv').open(encoding='utf-8',newline='') as f:
        items={r['item_id']:r for r in csv.DictReader(f)}
    with Path('runs/R20/inputs/raw/stores.csv').open(encoding='utf-8',newline='') as f:
        stores={r['store_id'] for r in csv.DictReader(f)}
    with (ROOT/'evidence/smoke-one-day.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    keys=[(r['service_date'],r['store_id'],r['item_id']) for r in rows]
    expected={('2026-10-01',s,k) for s in stores for k in items}
    assert len(keys)==len(set(keys))==96 and set(keys)==expected
    units=0; money=Decimal(0); loss=Decimal(0)
    for r in rows:
        q=Decimal(r['q_units']); d=Decimal(r['demand_point_units']); p=items[r['item_id']]
        assert q.is_finite() and d.is_finite() and d>=0 and q==q.to_integral_value()
        assert 0<=q<=Decimal(p['daily_max_units'])
        units+=int(q); money+=Decimal(p['procurement_yuan'])*q
        loss+=Decimal(p['shortage_yuan'])*max(d-q,0)+Decimal(p['waste_yuan'])*max(q-d,0)
        assert r['last_label_available_at']<='2026-09-30T18:00:00'
    assert units<=1600 and money<=6000
    receipt=json.loads((ROOT/'evidence/smoke-receipt.json').read_text(encoding='utf-8'))
    assert units==receipt['total_q_units'] and money==Decimal(receipt['procurement_yuan'])
    assert loss==Decimal(receipt['loss_at_point_baseline_yuan'])
    records=[]
    for p in sorted((ROOT/'evidence').glob('00[1-4]-*.json')):
        r=json.loads(p.read_text(encoding='utf-8'))
        assert r['state']=='finished' and r['begin'] and r['end']
        records.append({'path':p.as_posix(),'exit_code':r['exit_code'],'begin':r['begin']['utc'],'end':r['end']['utc']})
    assert len(records)==4
    print(json.dumps({'skill_only_markdown':True,'checked_relative_links':links,
                      'csv_recomputed':{'keys':len(keys),'units':units,'procurement_yuan':str(money),'point_loss_yuan':str(loss)},
                      'actual_command_records':records,'independent_acceptance':False},ensure_ascii=False,indent=2))
    if '--manifest' in sys.argv:
        excluded={ROOT/'manifest.json',ROOT/'evidence/008-package-manifest.json'}
        files=[]
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and p not in excluded:
                files.append({'path':p.as_posix(),'size_bytes':p.stat().st_size,
                              'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        manifest={'schema':'r20-workflow-design-manifest/1','created_at':datetime.now(timezone.utc).isoformat(),
                  'scope':'Design plus raw audit and bounded one-day author smoke, not full problem acceptance.',
                  'input_lock':'runs/R20/input-lock.json','source_skill_lock':'runs/R19/final/candidate/C12-lock.json',
                  'exclusions':[p.as_posix() for p in sorted(excluded)],'files':files,
                  'telemetry':{'model':None,'tokens':None,'cost':None},
                  'next_action':{'owner':'root','task_id':'T01','instruction':'Freeze design, then actually dispatch fresh executor with HANDOFF.md and raw inputs.'}}
        (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'manifest':(ROOT/'manifest.json').as_posix(),'files':len(files),'sha256':hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest()},ensure_ascii=False))

if __name__=='__main__':
    main()
