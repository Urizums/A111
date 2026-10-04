"""Read only the assigned immutable request and bound public study input."""
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);envelope=json.loads(p.read_text());r=envelope['request'];work=r['work']
for ref in work['input_files']:
 assert hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest()==ref['sha256'],ref['path']
print(json.dumps({'identity':{k:r[k] for k in ['job_id','attempt_id','invocation_id','kind']},'request_hash':envelope['request_hash'],'dispatch':r['dispatch'],'work':work['inputs'],'reply_path':work['reply_path'],'write_paths':work['write_paths']},ensure_ascii=False,indent=2))
print(Path(work['inputs']['protocol']).read_text())
print(Path(work['inputs']['material']).read_text())
