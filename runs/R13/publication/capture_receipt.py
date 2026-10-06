"""Capture exact Git publication state, without inferring CI acceptance."""
from pathlib import Path
from datetime import datetime,timezone
import json
import subprocess

ROOT=Path(__file__).resolve().parents[3]
local=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
assert local==remote
path=ROOT/'runs/R13/publication/source-receipt.json'
with path.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(dict(observed_at=datetime.now(timezone.utc).isoformat(),repository='Urizums/A111',branch='main',
          local_commit=local,remote_commit=remote,development_source_pushed=True,
          R12='independent_prospective_design_pass',R13='failed_and_rolled_back_at2_over2',
          old_gates_and_budgets='preserved',ci_conclusion=None,
          limits='Exact remote Git publication only; CI and adoption acceptance are separate'),f,ensure_ascii=False,indent=2)
    f.write('\n')
print(json.dumps(dict(local_commit=local,remote_commit=remote,source_pushed=True)))
