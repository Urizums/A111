"""Verify authorized locks and freeze this preparation payload, excluding self."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def entry(path):
    return dict(path=path.relative_to(ROOT).as_posix(), size_bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


sources = []
for relative in ('runs/R19/final/candidate/C12-lock.json',
                 'runs/R19/final/forward/inputs/input-lock.json'):
    lockpath = ROOT/relative
    lock = json.loads(lockpath.read_text(encoding='utf-8-sig'))
    checks = []
    for expected in lock['files']:
        actual = entry(ROOT/expected['path'])
        checks.append(dict(expected=expected, actual=actual,
                           matches=all(actual[k] == expected[k] for k in ('path','size_bytes','sha256'))))
    sources.append(dict(lock=entry(lockpath), files=checks, all_match=all(c['matches'] for c in checks)))
observations = json.loads((HERE/'control-observations.json').read_text(encoding='utf-8'))
sourcecheck = dict(authorized_locks=sources,
                  acceptance_identity=entry(ROOT/'runs/R19/final/forward/acceptance.json'))
(HERE/'source-identity-observations.json').write_text(json.dumps(sourcecheck,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
payload = [entry(p) for p in sorted(HERE.rglob('*')) if p.is_file()
           and '__pycache__' not in p.parts and p.name not in ('result.json','manifest.json')]
result = dict(schema='C12-forward-review-preparation/1', phase='preparation',
    state='complete_stopped', production_read=False, production_verdict=False,
    frozen_at=datetime.now(timezone.utc).isoformat(),
    source_locks_match=all(s['all_match'] for s in sources),
    controls=dict(count=len(observations['controls']),
        all_agree=all(c['control_agrees'] for c in observations['controls']),
        false_acceptances=observations['false_acceptances'], false_rejections=observations['false_rejections']),
    mandatory=[dict(id=b, verdict='unverified', reason='Production not authorized or received; preparation is not production acceptance')
               for b in ('b1','b2','b3','b4','b5')],
    telemetry=dict(provider=None,model=None,tokens=None,cost=None),
    processes='All preparation commands started by this reviewer have terminal receipts; none left running',
    next_action='Stop writes and notify root; wait for actual frozen production lock, then write only review/',
    payload=payload,
    limitations=['22 self-constructed controls are not actual production receiver tests or production smoke',
                 'No production computation, workflow consumption, Chinese paper/source review or PDF rendering performed',
                 'No causal comparison, level/prize/October performance claim'])
(HERE/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest = dict(schema='C12-forward-review-preparation-manifest/1',
                files=[entry(p) for p in sorted(HERE.rglob('*')) if p.is_file()
                       and '__pycache__' not in p.parts and p.name != 'manifest.json'])
(HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(state=result['state'],source_locks_match=result['source_locks_match'],controls=result['controls'],
                     payload_files=len(payload),manifest_files=len(manifest['files']),production_verdict=False),ensure_ascii=False))
raise SystemExit(0 if result['source_locks_match'] and result['controls']['all_agree'] else 1)
