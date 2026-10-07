"""Bind actual saved run receipts to input/config/code/source identities.

This is post-run audit metadata, not fabricated solver timestamps.
"""
from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rawlock=json.loads((R.parents[2]/'inputs/raw-lock.json').read_text(encoding='utf8'));rawid=[{'path':a['path'],'sha256':a['sha256']} for a in rawlock['files']];assumptions=digest(R/'assumptions.md');time=datetime.datetime.now(datetime.timezone.utc).isoformat();count=0
for p in R.rglob('run.json'):
 if 'algorithm_replay' in p.parts:continue
 x=json.loads(p.read_text(encoding='utf8'));rel=p.relative_to(R);summary=None;root=None
 for candidate in ['results/main','results/improved','results/final','results/reproduction']:
  folder=R/candidate
  if folder in p.parents:root=folder;summary=json.loads((folder/'summary.json').read_text(encoding='utf8'));break
 itemfile=R/'data/items.csv'
 if 'experiments' in rel.parts:itemfile=p.parent/'items.csv'
 elif 'smoke' in rel.parts:itemfile=R/'checks/smoke_items.csv'
 config=x.get('config',{});vs=p.parent/'vehicles.json'
 x['audit_identity']={'raw_source':rawid,'items_sha256':digest(itemfile),'vehicles_sha256':digest(vs),'config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True,ensure_ascii=False).encode('utf8')).hexdigest(),'executed_main_sha256':summary.get('code_sha256') if summary else None,'code_identity_limit':None if summary else 'Not captured at this invocation start; no retrospective inference of code bytes. Actual inputs/config/results retained.','assumptions_sha256':assumptions,'seed':config.get('seed'),'pipeline_utc_start':summary.get('utc_start') if summary else None,'pipeline_utc_finish':summary.get('utc_finish') if summary else None,'individual_run_utc_start':None,'individual_run_utc_finish':None,'timing_limit':'Individual run timestamps were not recorded; actual pipeline and MILP seconds remain in summary/solver receipts.','metadata_enriched_utc':time,'metadata_operation':'post-run identity binding, not original solver receipt timing','model':None,'tokens':None,'cost':None}
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8');count+=1
print(json.dumps({'receipts_enriched':count,'individual_timestamps_fabricated':False,'unknown_old_experiment_code_identity':True},ensure_ascii=False))
