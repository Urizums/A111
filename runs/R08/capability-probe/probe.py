#!/usr/bin/env python3
"""Read-only local capability evidence; no credentials or external business effects."""
import ctypes
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
lock = json.loads((root / 'runs/R07/candidate/C6-lock.json').read_text())
matched = 0
for entry in lock['files']:
    raw = (root / entry['path']).read_bytes()
    assert len(raw) == entry['size_bytes']
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    matched += 1
state = json.loads((root / 'state/continuation.json').read_text())
assert state['execution']['monitor_enabled'] is False
native = json.loads((root / 'runs/R07/flow-challenge/worker/native/create-receipt.json').read_text())
def command(argv):
    p = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    return {'argv': argv, 'exit_code': p.returncode, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}

print(json.dumps({
    'schema': 'forge-local-capability-probe/1',
    'checkout': str(root),
    'python': sys.version,
    'python_executable': sys.executable,
    'python_3_10_available': shutil.which('python3.10') is not None,
    'platform': platform.platform(),
    'git': command(['git', '--version']),
    'source_head': command(['git', 'rev-parse', 'HEAD']),
    'candidate_files_matching_lock': matched,
    'renameat2_symbol_available': hasattr(ctypes.CDLL(None, use_errno=True), 'renameat2'),
    'actual_native_creation_observed': native['accepted'],
    'native_creation_evidence': 'runs/R07/flow-challenge/worker/native/create-receipt.json',
    'native_completed_evidence': 'runs/R07/flow-challenge/worker/native/terminal-notification.payload.json',
    'timer_enabled': False,
    'provider_preflight': 'not run: this scoped task supplied no authorized provider endpoint or identity',
    'provider_tokens': None,
    'provider_cost': None,
    'limits': ['This host only; next host must re-probe tools and permissions',
               'No independent cold start or global provider resource proof',
               'Raw historical absolute paths remain evidence, not instructions to recreate them'],
}, ensure_ascii=False, indent=2))
