#!/usr/bin/env python3
"""Exercise the preserved installer and CLI smoke on this scoped checkout."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = root / 'runs/R07/validation/local-smoke'
with tempfile.TemporaryDirectory(prefix='forge-r07-install-') as tmp:
    prefix = Path(tmp) / 'installed'
    for argv in [
        [sys.executable, 'scripts/deploy_cloud.py', '--prefix', str(prefix)],
        [sys.executable, 'scripts/smoke_cloud.py', '--prefix', str(prefix), '--out', str(out)],
    ]:
        subprocess.run(argv, cwd=root, check=True)
    report = json.loads((out / 'report.json').read_text())
    print(json.dumps({'report': 'runs/R07/validation/local-smoke/report.json',
                      'scope': 'Fresh local install and existing CLI smoke; Python 3.12 only',
                      'result': report}, ensure_ascii=False))
