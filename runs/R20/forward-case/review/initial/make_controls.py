#!/usr/bin/env python3
"""Create isolated lawful and invalid controls from frozen raw input."""
import argparse, csv, shutil
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--inputs',type=Path,required=True); p.add_argument('--root',type=Path,required=True); a=p.parse_args()
if a.root.exists(): raise SystemExit('control root must be absent')
a.root.mkdir(parents=True)
# Lawful: exact duplicate retransmission of a locked source row.
lawful=a.root/'lawful'; shutil.copytree(a.inputs,lawful/'inputs')
with (lawful/'inputs/raw/labels.csv').open(encoding='utf-8',newline='') as f: first=next(csv.DictReader(f))
with (lawful/'inputs/raw/labels.csv').open('a',encoding='utf-8',newline='') as f:
    f.write(','.join(first[k] for k in ['target_date','series_id','revision','available_at','actual_units'])+'\n')
# Invalid: conflicting contents under an existing label version identity.
invalid=a.root/'invalid-source-conflict'; shutil.copytree(a.inputs,invalid/'inputs')
with (invalid/'inputs/raw/labels.csv').open(encoding='utf-8',newline='') as f: first=next(csv.DictReader(f))
try: changed=str(int(first['actual_units'])+100)
except ValueError: changed=first['actual_units']+'-conflict'
with (invalid/'inputs/raw/labels.csv').open('a',encoding='utf-8',newline='') as f:
    f.write(','.join([first['target_date'],first['series_id'],first['revision'],first['available_at'],changed])+'\n')
print(f'lawful_input={lawful / "inputs"}')
print(f'invalid_source_conflict_input={invalid / "inputs"}')
