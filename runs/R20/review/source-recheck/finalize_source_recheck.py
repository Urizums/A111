from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
root=Path('runs/R20/review/source-recheck')
excluded={'manifest.json','checkpoint.json'}
files=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name not in excluded:
  b=p.read_bytes(); files.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
m={'schema':'R20-source-recheck-manifest/1','created_utc':datetime.now(timezone.utc).isoformat(),'root':'runs/R20/review/source-recheck','file_count':len(files),'files':files}
mb=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
(root/'manifest.json').write_bytes(mb)
sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
cp={'schema':'R20-source-recheck-checkpoint/1','state':'complete_and_frozen_for_root_review','created_utc':datetime.now(timezone.utc).isoformat(),'manifest':'runs/R20/review/source-recheck/manifest.json','manifest_sha256':hashlib.sha256(mb).hexdigest(),'manifest_file_count':len(files),'source_recheck_report_sha256':sha('source-recheck-report.md'),'source_recheck_result_sha256':sha('source-recheck-result.json'),'freeze_correction_sha256':sha('freeze-reference-correction.json'),'command_final_status':'runs/R20/review/source-recheck/command-final-status.json','commands_terminal':True,'initial_directory_modified':False,'future_truth_read_or_used_in_addendum':False,'prior_holdout_read_in_initial_review':True,'write_scope':'runs/R20/review/source-recheck only','author_feedback_sent':False,'next_action':'Root may freeze and review this informed source recheck; reviewer stops writing.'}
(root/'checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'file_count':len(files),'manifest_sha256':cp['manifest_sha256'],'checkpoint_sha256':sha('checkpoint.json'),'report_sha256':cp['source_recheck_report_sha256'],'result_sha256':cp['source_recheck_result_sha256']},indent=2))
