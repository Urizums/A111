"""Inventory immutable C1 records using only repository paths; no old replay."""
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = datetime.now(timezone.utc).isoformat()
schemas, errors, cli = Counter(), [], []
for p in sorted((ROOT/'evidence/c1').rglob('*')):
    if not p.is_file() or p.suffix not in {'.json','.jsonl'}:
        continue
    try:
        value = json.loads(p.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError):
        continue
    if not isinstance(value, dict):
        continue
    schema = value.get('schema')
    if schema:
        schemas[schema] += 1
    if schema != 'forge-comparison-cli/1':
        continue
    rel = p.relative_to(ROOT).as_posix()
    row = {'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
           'actor':value.get('actor'),'exit_code':value.get('exit_code')}
    problems = []
    for stream in ['stdout','stderr']:
        try:
            raw = base64.b64decode(value[stream+'_base64'],validate=True)
            if raw.decode('utf-8',errors='replace') != value[stream]:
                problems.append(stream+' decoded text mismatch')
        except (ValueError, KeyError, TypeError) as exc:
            problems.append(stream+': '+str(exc))
    begin, end = value.get('begin',{}), value.get('end',{})
    row['same_boot'] = bool(begin.get('boot_id')) and begin.get('boot_id') == end.get('boot_id')
    if row['same_boot']:
        try:
            elapsed = (end['monotonic_ns']-begin['monotonic_ns']) / 1e9
            if elapsed < 0 or abs(elapsed-value['elapsed_seconds']) > 1e-9:
                problems.append('elapsed mismatch')
        except (KeyError, TypeError):
            problems.append('missing/invalid monotonic elapsed')
    row['record_integrity_errors'] = problems
    cli.append(row)
    errors.extend({'path':rel,'error':e} for e in problems)
result = {'schema':'forge-audit-inventory/1','started_at':START,
          'finished_at':datetime.now(timezone.utc).isoformat(),
          'actual_operation':'Read repository C1 JSON/JSONL; identify schema; independently decode raw CLI streams and compare same-boot elapsed fields.',
          'schema_counts':dict(sorted(schemas.items())),'cli_records':cli,'errors':errors,
          'exit_code':int(bool(errors)), 'old_native_calls':0,
          'limits':'Top-level record inventory only. Invalid/non-object JSON is skipped and is not graded. Does not complete receipt/semantic/correction/marker/wait acceptance or prove every command was recorded.'}
dest=ROOT/'runs/S01/record-inventory.json'
dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':dest.relative_to(ROOT).as_posix(),'cli_records':len(cli),'errors':errors,'old_native_calls':0}))
raise SystemExit(result['exit_code'])
