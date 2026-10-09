"""Administrative last write: hash terminal artifacts, excluding only the manifest itself."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--production', type=Path, required=True)
parser.add_argument('--repo', type=Path, required=True)
args = parser.parse_args()
base = args.production.resolve()
manifest_path = base / 'manifest.json'
assert not manifest_path.exists(), 'No replacement of already frozen manifest.'
receipts = []
for path in sorted((base / 'evidence').glob('*.json')):
    payload = json.loads(path.read_text(encoding='utf-8'))
    assert payload['state'] == 'finished', path
    receipts.append({'path': path.relative_to(base).as_posix(), 'exit_code': payload['exit_code'],
                     'begin': payload['begin'], 'end': payload['end']})
assert len(receipts) == 11
files = []
for path in sorted(base.rglob('*')):
    if path.is_file() and path != manifest_path:
        body = path.read_bytes()
        files.append({'path': path.relative_to(base).as_posix(), 'size_bytes': len(body),
                      'sha256': hashlib.sha256(body).hexdigest()})
source_locks = {}
for name in ['runs/R20/forward-case/input-lock.json', 'runs/R20/final/candidate/C13-lock.json']:
    source_locks[name] = hashlib.sha256((args.repo / name).read_bytes()).hexdigest()
manifest = {'schema': 'forward-production-manifest/1', 'task_id': 'R20-C13-forward-calibration-production',
            'frozen_at': datetime.now(timezone.utc).isoformat(), 'state': 'author_complete_writes_stopped',
            'absolute_production_root': str(base), 'readme_entry': 'README.md',
            'workflow_entry': 'calibration-flow/SKILL.md', 'authoritative_result': 'results/results.json',
            'scientific_consumer': 'results/说明.md', 'source_lock_sha256': source_locks,
            'inventory': files, 'terminal_scientific_receipts': receipts,
            'excluded': [{'path': 'manifest.json', 'reason': 'Self-hash excluded; actual manifest hash returned to coordinator as administrative tool output.'}],
            'reproduction_and_challenge_not_authoritative': ['clean-rerun/', 'script-reproduction/', 'fixtures/'],
            'pending_processes': [], 'pending_host_calls': [], 'independent_acceptance': 'not claimed',
            'model': None, 'tokens': None, 'cost': None,
            'finalization': 'Administrative inventory/hash write only, after all recorded scientific commands finished. No producer writes after this invocation.'}
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'entry': str(base / 'README.md'), 'workflow_entry': str(base / 'calibration-flow/SKILL.md'),
                  'manifest': str(manifest_path), 'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                  'inventory_file_count': len(files), 'terminal_command_count': len(receipts), 'writes_stopped': True}, ensure_ascii=False))
