"""Individually certify the saved main mode library with the separate validator."""
from pathlib import Path
import json,csv,time
from validate import validate
R=Path(__file__).resolve().parents[1]
with (R/'data/items.csv').open(encoding='utf-8-sig') as f:items=list(csv.DictReader(f))
vs=json.loads((R/'data/vehicles.json').read_text(encoding='utf8'));patterns=json.loads((R/'results/final/pattern_library.json').read_text(encoding='utf8'));ids={t:[r['item_id'] for r in items if r['cargo_type']==t] for t in ['G1','G2','G3','G4','G5']};records=[];start=time.perf_counter()
for i,p in enumerate(patterns):
 used={t:0 for t in ids};rows=[]
 for a in p['placements']:
  t=a['cargo_type'];rows.append({'vehicle_id':'T1','vehicle_type':p['vehicle_type'],'item_id':ids[t][used[t]],**a});used[t]+=1
 z=validate(rows,items,[v for v in vs if v['type_id']==p['vehicle_type']],full=False)
 records.append({'pattern':i,'vehicle_type':p['vehicle_type'],'counts':p['counts'],'valid':z['valid'],'errors':z['errors'],'checked_items':z['checked_items'],'counts_recomputed_match':[used[t] for t in ids]==p['counts']})
out={'pattern_count':len(patterns),'valid_patterns':sum(a['valid'] and a['counts_recomputed_match'] for a in records),'records':records,'seconds':time.perf_counter()-start,'claim':'every final main candidate mode was recomputed; author-run separate implementation, not fresh-agent acceptance'};(R/'checks/pattern_library_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');assert out['valid_patterns']==out['pattern_count'];print(json.dumps({k:v for k,v in out.items() if k!='records'},ensure_ascii=False))
