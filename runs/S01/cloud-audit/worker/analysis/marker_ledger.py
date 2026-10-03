#!/usr/bin/env python3
"""Write a boot-aware concise ledger of every frozen sample marker/wait/status return."""
import json
from pathlib import Path
ROOT=Path('/workspace/A111')
SRC=ROOT/'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
OUT=ROOT/'runs/S01/cloud-audit/worker/analysis/marker_ledger.txt'
src=json.loads(SRC.read_text(encoding='utf-8'))
lines=[]
def add(s=''):lines.append(str(s))
for sample,entries in src['samples'].items():
    markers=[];native=[]
    for e in entries:
        p=e['path'];d=e.get('data')
        if isinstance(d,dict) and d.get('schema')=='forge-comparison-marker/1':markers.append((p,d))
        if '/native/' in p and isinstance(d,dict):native.append((p,d))
    add('\n## '+sample)
    boot_groups={}
    for p,d in markers:boot_groups.setdefault(d.get('boot_id'),[]).append((p,d))
    for boot,rows in boot_groups.items():
        rows.sort(key=lambda x:(x[1].get('monotonic_ns') or -1,x[0]))
        add('BOOT '+str(boot))
        for p,d in rows:add(json.dumps({'mono':d.get('monotonic_ns'),'actor':d.get('actor'),'stage':d.get('stage'),'event':d.get('event'),'utc':d.get('utc'),'path':p},ensure_ascii=False,separators=(',',':')))
    add('WAIT RECORDS')
    for p,d in sorted(native):
        if any(s in Path(p).name.lower() for s in ['wait','notification']):add(json.dumps({'path':p,'data':d},ensure_ascii=False,separators=(',',':')))
    add('STATUS RAW RETURNS')
    for p,d in sorted(native):
        name=Path(p).name.lower()
        if 'return' in name and 'observer' not in name and ('status' in name or 'query' in name):
            add(json.dumps({'path':p,'data':d},ensure_ascii=False,separators=(',',':')))
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT),'bytes':OUT.stat().st_size,'lines':len(lines)},ensure_ascii=False))
