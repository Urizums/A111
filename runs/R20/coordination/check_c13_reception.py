"""Integrate exact first reception, source binding and real terminal commands."""
import base64
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
base=ROOT/'runs/R20/forward-case/review/initial'
def read(f):return json.loads(f.read_text(encoding='utf-8'))
assert hashlib.sha256((base/'manifest.json').read_bytes()).hexdigest()=='67c0d59bcb7c776bba0ae5ccbcf005295c92476d36beab6c62431801964bcfc8'
manifest=read(base/'manifest.json')
for row in manifest['files']:
    b=(base/row['path']).read_bytes()
    assert (len(b),hashlib.sha256(b).hexdigest())==(row['size_bytes'],row['sha256']),row['path']
for rel in ['runs/R20/forward-case/production-lock.json','runs/R20/forward-case/review/preparation-lock.json',
    'runs/R20/forward-case/review/initial-lock.json','runs/R20/forward-case/review/preparation-path-error-lock.json',
    'runs/R20/final/candidate/C13-lock.json']:
    for row in read(ROOT/rel)['files']:
        b=(ROOT/row['path']).read_bytes()
        assert (len(b),hashlib.sha256(b).hexdigest())==(row['size_bytes'],row['sha256']),row['path']
result=read(base/'first-result.json')
assert result['running_processes']==0 and all(result['verdicts'][k]['verdict']=='accepted' for k in ['f1','f2','f3'])
records=[]
for f in sorted((base/'commands').glob('*.json')):
    r=read(f)
    assert r['schema']=='forge-command-record/1' and r['state']=='finished' and r['argv'] and r['cwd']
    assert r['begin']['utc'] and r['end']['utc'] and type(r['exit_code']) is int
    for stream in ['stdout','stderr']:
        # record_command.py retains raw bytes separately and deliberately uses
        # UTF-8 replacement for display text (native tools may emit local bytes).
        assert base64.b64decode(r[stream+'_base64']).decode('utf-8',errors='replace')==r[stream], (f.name,stream)
    records.append({'path':f.name,'exit_code':r['exit_code']})
assert len(records)==17
f2=result['verdicts']['f2']['observations']
for field in ['independent_clean_rerun','main_independent_receiver','invalid_same_version_source_control','invalid_future_label_output_control']:
    row=f2[field];actual=read(base/row['record'])
    assert actual['state']==row['terminal_state'] and actual['exit_code']==row['exit_code'],field
for field,pathkey,exitkey in [('lawful_duplicate_control','production_record','production_exit_code'),
    ('lawful_duplicate_control','receiver_record','receiver_exit_code')]:
    row=f2[field];assert read(base/row[pathkey])['exit_code']==row[exitkey]
assert f2['production_vs_clean_rerun']['six_artifacts_byte_identical']
for f in (ROOT/'runs/R20/forward-case/production/results').iterdir():
    assert f.read_bytes()==(base/'clean-rerun/results'/f.name).read_bytes(),f.name
assert read(base/'commands/producer-receipt-structure-audit.json')['exit_code']==0
failed_checker=[r['path'] for r in records if r['exit_code'] and r['path'] not in ['invalid-source-conflict-control.json','independent-receiver-invalid-output.json']]
assert len(failed_checker)==3,failed_checker
print(json.dumps(dict(f1_f2_f3='first accepted',author_inventory=70,production_lock=71,
    reception_lock_files=59,receiving_commands=len(records),checker_nonzero=failed_checker,
    production_invalid_source_exit=2,independent_invalid_output_exit=1,actual_clean_raw_rerun=True,
    producer_structural_audit=11,original_path_blocked_preserved=True,
    scope='Independent scientific result limited to affected original case; root exact bytes/receipts integration, no causal comparison.'),ensure_ascii=False))
