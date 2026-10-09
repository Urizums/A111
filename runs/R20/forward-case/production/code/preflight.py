import argparse
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
locks = ['runs/R20/forward-case/input-lock.json', 'runs/R20/final/candidate/C13-lock.json']
observations = []
for name in locks:
    lock = json.loads((args.repo / name).read_text(encoding='utf-8'))
    for entry in lock['files']:
        path = args.repo / entry['path']
        body = path.read_bytes()
        actual = hashlib.sha256(body).hexdigest()
        assert actual == entry['sha256'], f"hash mismatch: {entry['path']}"
        assert len(body) == entry['size_bytes'], f"size mismatch: {entry['path']}"
        observations.append({'path': entry['path'], 'sha256': actual, 'size_bytes': len(body)})
report = {'scope': 'author preflight, identity only', 'status': 'pass', 'runtime': sys.version,
          'locks': locks, 'verified_files': observations, 'model': None, 'tokens': None, 'cost': None}
args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'PASS identity preflight: {len(observations)} exact files; Python {sys.version.split()[0]}')
