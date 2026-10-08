"""Seal only this reviewer preparation. Root performs authoritative freeze."""
import ast, hashlib, json, time
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
start=time.perf_counter()
scripts=[]
for path in sorted(HERE.glob('*.py')):
    ast.parse(path.read_text(encoding='utf-8'),filename=path.name)
    scripts.append(path.name)
json_checks=[]
def reject_constant(value): raise ValueError('Nonstandard JSON constant: '+value)
for path in sorted(HERE.glob('*.json')):
    if path.name in {'preparation-manifest.json','preparation-final-check.json'}: continue
    try:
        json.loads(path.read_text(encoding='utf-8'),parse_constant=reject_constant)
        status='strict_json_valid'
    except ValueError as exc:
        if path.name!='method-controls-input.attempt1.json': raise
        status='retained_known_attempt1_nonstandard_NaN; current file repaired'
    json_checks.append({'file':path.name,'status':status})
result=json.loads((HERE/'result.json').read_text(encoding='utf-8'))
controls=json.loads((HERE/'method-controls-result.json').read_text(encoding='utf-8'))
assert result['phase']=='preparation_only' and result['own_processes_terminal'] and not result['pending_calls']
assert controls['all_method_controls_pass'] and not controls['production_acceptance_run']
assert len(controls['actual_controls'])==21
assert sum(c['expected']=='valid' for c in controls['actual_controls'])==6
check={'status':'preparation_internal_consistency_checked', 'utc':datetime.now(timezone.utc).isoformat(),
       'script_syntax':scripts,'json_checks':json_checks,'scope':'own preparation only',
       'actual_source_lock_match':True,'method_controls':21,'producer_verdict_created':False,
       'pending_calls':[],'background_processes_created':[],'synchronous_check_terminal_on_exit':True,
       'elapsed_seconds':time.perf_counter()-start}
(HERE/'preparation-final-check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
files=[]
for path in sorted(HERE.rglob('*')):
    if not path.is_file() or path.name=='preparation-manifest.json': continue
    blob=path.read_bytes()
    files.append({'path':str(path.relative_to(HERE)).replace('\\','/'),
                  'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
manifest={'schema':'independent-review-preparation-manifest/1','utc':datetime.now(timezone.utc).isoformat(),
          'role':'/root/r19_l3_reviewer','phase':'preparation_only','root_freeze_requested':True,
          'scope':'runs/R19/levels/L3/review/preparation/', 'files':files,
          'terminal':'all scripts synchronous finished; no background/pending calls; this finalization process exits synchronously',
          'production_acceptance':'not run; no verdict', 'model':None,'token_usage':None,'cost':None}
(HERE/'preparation-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'prepared_files':len(files),'internal_consistency':'pass',
                  'manifest_sha256':hashlib.sha256((HERE/'preparation-manifest.json').read_bytes()).hexdigest(),
                  'production_acceptance_run':False},ensure_ascii=False))
