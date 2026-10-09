import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
report=json.loads((root/'first-result.json').read_text(encoding='utf-8'))
assert report['schema']=='c13-forward-case-independent-first-result/1'
assert all(report['verdicts'][k]['verdict']=='accepted' for k in ('f1','f2','f3'))
cmds=[]
for p in sorted((root/'commands').glob('*.json')):
    r=json.loads(p.read_text(encoding='utf-8'))
    assert r.get('schema')=='forge-command-record/1' and r.get('state')=='finished' and isinstance(r.get('exit_code'),int)
    cmds.append({'path':p.relative_to(root).as_posix(),'state':r['state'],'exit_code':r['exit_code']})
files=[]
for p in sorted(root.rglob('*')):
    if not p.is_file() or p.name=='manifest.json': continue
    b=p.read_bytes()
    files.append({'path':p.relative_to(root).as_posix(),'size_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
manifest={
 'schema':'c13-forward-independent-review-manifest/1',
 'terminal_status':'first_acceptance_complete',
 'case_root':'runs/R20/forward-case',
 'review_root':'runs/R20/forward-case/review/initial',
 'locks':{
  'input':'runs/R20/forward-case/input-lock.json','input_lock_sha256':'8ae32d1eeb05a5eaa3e7aee64aabd7b983a0162fc39c17210d5c4c218b47735a',
  'evaluation':'runs/R20/forward-case/evaluation-lock.json','evaluation_lock_sha256':'38515dd34511217e8f13b9b21f59f48270336ebdc5720fe64f9d704083cb6116',
  'preparation':'runs/R20/forward-case/review/preparation-lock.json','preparation_lock_sha256':'bfc4661b5754f64b7c22a8bd658f9fa3115d6726513e66b267a6cc69ab397924',
  'workflow':'runs/R20/final/candidate/C13-lock.json','workflow_lock_sha256':'860caeec761028fa47723410c99ef2f48db2f61fa16405c8929a0005e158af7a',
  'production':'runs/R20/forward-case/production-lock.json','production_lock_sha256':'8b7edecebe5e5421fe67db7e47e2e4e3885ce4903f32c47b43a85712002e2cf2',
  'production_manifest_sha256':'f0a7523ad9081c56f96eb5147e7adaa326fa9eaefef566ccbd2fa713df63b093'
 },
 'verdicts':{k:report['verdicts'][k]['verdict'] for k in ('f1','f2','f3')},
 'producer_receipt_structural_audit':{'records':11,'all_pass':True,'semantic_stdout_stderr_read_or_emitted':False},
 'command_record_count':len(cmds),
 'commands':cmds,
 'running_processes':0,
 'model_provider_tokens_cost':None,
 'files':files
}
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'terminal_status':manifest['terminal_status'],'f1_f2_f3':manifest['verdicts'],'command_records':len(cmds),'file_count':len(files),'running_processes':0},ensure_ascii=False,indent=2))
