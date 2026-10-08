import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
root=Path('runs/R20/review/initial')
excluded={'manifest.json','checkpoint.json'}
files=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name not in excluded:
  b=p.read_bytes(); files.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
manifest={'schema':'R20-independent-initial-manifest/1','created_utc':datetime.now(timezone.utc).isoformat(),'root':'runs/R20/review/initial','file_count':len(files),'files':files}
mb=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
(root/'manifest.json').write_bytes(mb)
cp={'schema':'R20-independent-initial-checkpoint/1','state':'complete_and_frozen_for_root_review','created_utc':datetime.now(timezone.utc).isoformat(),'manifest':'runs/R20/review/initial/manifest.json','manifest_sha256':hashlib.sha256(mb).hexdigest(),'manifest_file_count':len(files),'first_report_sha256':hashlib.sha256((root/'first-report.md').read_bytes()).hexdigest(),'first_result_sha256':hashlib.sha256((root/'first-result.json').read_bytes()).hexdigest(),'pre_holdout_freeze':'runs/R20/review/initial/pre_holdout_freeze.json','holdout_opened_after_that_freeze':True,'pdf_pages_rendered_and_viewed':11,'all_checked_command_records_terminal':True,'write_scope':'runs/R20/review/initial only','author_feedback_sent':False,'next_action':'Root may freeze/review this first judgment; reviewer stops writing.'}
(root/'checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest_file_count':len(files),'manifest_sha256':hashlib.sha256(mb).hexdigest(),'checkpoint_sha256':hashlib.sha256((root/'checkpoint.json').read_bytes()).hexdigest(),'first_report_sha256':cp['first_report_sha256'],'first_result_sha256':cp['first_result_sha256']},indent=2))
