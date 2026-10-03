#!/usr/bin/env python3
"""Read-only extraction of original C1 per-sample records for independent audit."""
import hashlib
import json
from pathlib import Path

ROOT = Path('/workspace/A111')
EVIDENCE = ROOT / 'evidence/c1'
OUT = ROOT / 'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
SAMPLES = {
    'project': ['A1', 'B1', 'B2', 'A2'],
    'package': ['B1', 'A1', 'A2', 'B2'],
}

def record(path):
    raw = path.read_bytes()
    entry = {'path': path.relative_to(ROOT).as_posix(), 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    if path.suffix == '.json':
        try:
            entry['data'] = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            entry['text'] = raw.decode('utf-8', errors='replace')
    elif path.suffix in {'.md', '.txt'}:
        entry['text'] = raw.decode('utf-8', errors='replace')
    elif path.name.endswith('.jsonl'):
        lines = raw.decode('utf-8', errors='replace').splitlines()
        parsed = []
        for number, line in enumerate(lines, 1):
            try:
                parsed.append({'line': number, 'data': json.loads(line)})
            except json.JSONDecodeError:
                parsed.append({'line': number, 'text': line})
        entry['lines'] = parsed
    else:
        entry['text'] = raw.decode('utf-8', errors='replace')
    return entry

result = {'schema': 'c1-raw-extraction/1', 'samples': {}, 'snapshot_manifest_check': None}
for block, sample_ids in SAMPLES.items():
    for sid in sample_ids:
        sample = EVIDENCE / block / sid
        selected = []
        # Explicit folders preserve originals while excluding historical code from execution or import.
        candidates = []
        for name in ['state.json', 'work.json', 'coordinator-decision.json', 'coordinator-decision.draft.json']:
            p = sample / name
            if p.is_file(): candidates.append(p)
        for folder in ['job', 'native', 'logs', 'observations', 'review', 'artifacts']:
            d = sample / folder
            if d.is_dir():
                for p in sorted(d.rglob('*')):
                    if not p.is_file() or p.suffix == '.py': continue
                    if p.suffix not in {'.json', '.jsonl', '.md', '.txt'}: continue
                    # Preserve captures and raw records; leave binary/database files untouched.
                    candidates.append(p)
        for p in sorted(set(candidates)):
            selected.append(record(p))
        result['samples'][f'{block}/{sid}'] = selected

manifest_path = EVIDENCE / 'Snapshot_Manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
checks = []
for entry in manifest.get('entries', []):
    rel = entry['relative_path']
    target = EVIDENCE / rel
    if not target.is_file():
        checks.append({'relative_path': rel, 'status': 'missing', 'expected_sha256': entry.get('sha256')})
        continue
    raw = target.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    checks.append({'relative_path': rel, 'status': 'match' if got == entry.get('sha256') and len(raw) == entry.get('size_bytes') else 'mismatch', 'expected_sha256': entry.get('sha256'), 'actual_sha256': got, 'expected_size_bytes': entry.get('size_bytes'), 'actual_size_bytes': len(raw)})
result['snapshot_manifest_check'] = {'checked': len(checks), 'matches': sum(x['status'] == 'match' for x in checks), 'missing': sum(x['status'] == 'missing' for x in checks), 'mismatches': sum(x['status'] == 'mismatch' for x in checks), 'details': checks}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(OUT), 'sample_count': len(result['samples']), 'per_sample_record_counts': {k: len(v) for k,v in result['samples'].items()}, 'snapshot_manifest_check': {k:v for k,v in result['snapshot_manifest_check'].items() if k != 'details'}}, ensure_ascii=False))
