import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]

def entry(path):
    return dict(path=path.relative_to(ROOT).as_posix(),size_bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def save(name,content):
    (HERE/name).write_text(json.dumps(content,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

method_paths=['runs/R19/final/forward/review-preparation/method.md',
              'runs/R19/final/forward/review-preparation/independent_check.py',
              'runs/R19/final/forward/acceptance.json']
save('method-lock.json',dict(schema='C12-independent-reception-method/1',
    frozen_at=datetime.now(timezone.utc).isoformat(),
    stage='before reading production content',
    method='Apply frozen preparation methodology and b1-b5; no new mandatory gates',
    files=[entry(ROOT/p) for p in method_paths],
    scope='Actual frozen production workflow/raw execution, source-bound independent physical/objective/paper checks, paired real receiver paths, full PDF render inspection'))
checks=[]
for relative in ['runs/R19/final/candidate/C12-lock.json',
                 'runs/R19/final/forward/inputs/input-lock.json',
                 'runs/R19/final/forward/evaluation-lock.json',
                 'runs/R19/final/forward/review-preparation-lock.json',
                 'runs/R19/final/forward/production-lock.json']:
    lp=ROOT/relative
    original=json.loads(lp.read_text(encoding='utf-8-sig'))
    observations=[]
    for expected in original['files']:
        actual=entry(ROOT/expected['path'])
        observations.append(dict(expected=expected,actual=actual,matches=actual==expected))
    checks.append(dict(lock=entry(lp),all_match=all(x['matches'] for x in observations),files=observations))
save('identity-check.json',dict(phase='formal reception preflight',locks=checks,all_match=all(c['all_match'] for c in checks)))
print(json.dumps(dict(method_frozen=True,all_locks_match=all(c['all_match'] for c in checks),
                     production_files=len(checks[-1]['files'])),ensure_ascii=False))
raise SystemExit(0 if all(c['all_match'] for c in checks) else 1)
