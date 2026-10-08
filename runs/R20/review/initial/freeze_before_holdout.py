import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]; OUT=ROOT/'runs/R20/review/initial'; DEL=ROOT/'runs/R20/execution/delivery'; OWN=OUT/'rerun'
def entry(p,relative):return {'path':relative,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
identity=json.loads((OUT/'command-identity-check.json').read_text(encoding='utf-8'))
# record_command stores full identity audit stdout as UTF-8 text inside the wrapper record.
identity=json.loads(identity['stdout'])
delivery=[entry(p,p.relative_to(ROOT).as_posix()) for p in sorted(DEL.rglob('*')) if p.is_file()]
rerun=[entry(p,p.relative_to(OWN).as_posix()) for p in sorted(OWN.rglob('*')) if p.is_file()]
locked={'delivery':identity['all_execution_targets_match'],'inputs':identity['all_input_hashes_match'],'design':identity['all_authorized_design_hashes_match'],'acceptance':identity['acceptance_hash_match']}
rec={'schema':'R20-initial-independent-freeze/1','created_before_reading_holdout_truth':True,'holdout_truth_opened':False,'execution_revision':identity['execution_lock_revision'],'execution_frozen_at':identity['execution_frozen_at'],'identity_checks':locked,'source_files_checked':identity['checked_current_execution_files'][:4],'input_files_checked':identity['input_checks'],'authorized_design_files_checked':identity['authorized_design_checks'],'current_delivery_files':delivery,'independent_rerun_files':rerun,'pre_holdout_result_records':[entry(OUT/n,n) for n in ['command-independent-rerun.json','command-independent-recompute-retry.json','command-scenario-recompute-retry2.json','command-production-path-controls.json','command-check-current-delivery.json','command-compare-artifacts.json']]}
(OUT/'pre_holdout_freeze.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'freeze_file':'runs/R20/review/initial/pre_holdout_freeze.json','holdout_truth_opened':False,'all_lock_checks':all(locked.values()),'delivery_files':len(delivery),'rerun_files':len(rerun),'identity_hashes_saved':True},ensure_ascii=False,indent=2))
