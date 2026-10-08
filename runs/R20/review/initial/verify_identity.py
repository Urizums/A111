import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
with (ROOT/'runs/R20/execution-lock.json').open(encoding='utf-8') as f:el=json.load(f)
entries={e['path']:e for e in el['files']}
with (ROOT/'runs/R20/input-lock.json').open(encoding='utf-8') as f:il=json.load(f)
with (ROOT/'runs/R20/evaluation-lock.json').open(encoding='utf-8') as f:vl=json.load(f)
with (ROOT/'runs/R20/design-lock.json').open(encoding='utf-8') as f:dl=json.load(f)
with (ROOT/'runs/R20/evaluation/ACCEPTANCE.md').open(encoding='utf-8') as f: acceptance=f.read()
# Only inspect permitted execution files plus every file in current delivery, by bytes.
exact=['runs/R20/execution/README.md','runs/R20/execution/code/run.py','runs/R20/execution/code/report.py','runs/R20/execution/config/experiment.json']+[f'runs/R20/execution/evidence/{n}' for n in ['013-final-interval-consistency.json','014-clean-rerun-current.json','016-render-delivery-pages.json','018-final-package.json']]
actual_paths=set(exact)
for p in (ROOT/'runs/R20/execution/delivery').rglob('*'):
    if p.is_file(): actual_paths.add(p.relative_to(ROOT).as_posix())
def check(path, ent):
    p=ROOT/path; h=sha(p); size=p.stat().st_size
    return {'path':path,'expected_sha256':ent['sha256'],'actual_sha256':h,'expected_bytes':ent['size_bytes'],'actual_bytes':size,'match':h==ent['sha256'] and size==ent['size_bytes']}
results=[]
for path in sorted(actual_paths):
    if path not in entries: results.append({'path':path,'error':'not present in execution lock'}); continue
    results.append(check(path,entries[path]))
input_checks=[check(e['path'],e) for e in il['files']]
allowed_design=['runs/R20/design/HANDOFF.md','runs/R20/design/forge-freshfood-flow/SKILL.md','runs/R20/design/forge-freshfood-flow/references/acceptance.md','runs/R20/design/forge-freshfood-flow/references/contracts.md','runs/R20/design/forge-freshfood-flow/references/paper-delivery.md','runs/R20/design/forge-freshfood-flow/references/research-decisions.md']
design_entries={e['path']:e for e in dl['files']}
design_checks=[check(p,design_entries[p]) for p in allowed_design]
accept_entry=next(e for e in vl['files'] if e['path']=='runs/R20/evaluation/ACCEPTANCE.md')
accept_actual=sha(ROOT/accept_entry['path'])
hold_entry=next(e for e in vl['files'] if e['path']=='runs/R20/evaluation/holdout_truth.csv')
out={'schema':'independent-source-identity/1','execution_lock_revision':el['revision'],'execution_frozen_at':el['frozen_at'],'checked_current_execution_files':results,'all_execution_targets_match':bool(results) and all(x.get('match',False) for x in results),'current_delivery_file_count':sum(p.startswith('runs/R20/execution/delivery/') for p in actual_paths),'input_checks':input_checks,'all_input_hashes_match':all(x['match'] for x in input_checks),'authorized_design_checks':design_checks,'all_authorized_design_hashes_match':all(x['match'] for x in design_checks),'acceptance_hash_match':accept_actual==accept_entry['sha256'],'acceptance_expected_sha256':accept_entry['sha256'],'acceptance_actual_sha256':accept_actual,'holdout_expected_sha256':hold_entry['sha256'],'holdout_opened':False,'other_design_lock_or_execution_lock_entries_consumed_as_results':False}
print(json.dumps(out,ensure_ascii=False,indent=2))
