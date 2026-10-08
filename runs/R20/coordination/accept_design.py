"""Check frozen handoff bytes, then accept design scope and start actual execution."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('action',choices=['check','integrate'])
args = parser.parse_args()

def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

lock = read('runs/R20/design-lock.json')
manifest = read('runs/R20/design/manifest.json')
for entry in lock['files']+manifest['files']:
    data = (ROOT/entry['path']).read_bytes()
    assert len(data)==entry['size_bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],entry['path']
assert len(manifest['files'])==24 and len(lock['files'])==26
skill = ROOT/'runs/R20/design/forge-freshfood-flow'
files = [p for p in skill.rglob('*') if p.is_file()]
assert len(files)==5 and all(p.suffix=='.md' for p in files)
assert all(read(f'runs/R20/design/evidence/{name}')['state']=='finished' for name in [
    '001-material-read.json','002-audit-raw.json','003-one-day-smoke.json','004-resource-boundary-smoke.json',
    '005-design-verification.json','006-archive-recovery.json','007-design-verification.json','008-package-manifest.json'])
assert read('runs/R20/design/checkpoint.json')['unresolved_host_calls']==[]
if args.action=='check':
    print(json.dumps(dict(frozen_files=26,manifest_payload_files=24,workflow_markdown_files=5,
        source_bound=True,scope='Handoff identity and finished design evidence; not full execution or scientific acceptance.')))
else:
    sys.path.insert(0,str(ROOT/'scripts'))
    import continuation as ctl
    with ctl.locked(ROOT):
        state = ctl.load(ROOT)
        old = read('runs/R20/before/task-identities.json')
        assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
        assert not state['execution']['current_native_pending']
        receipt = read('runs/R20/coordination/design-reception-check-command.json')
        assert receipt['state']=='finished' and receipt['exit_code']==0
        task = ctl.task_map(state)['R20-03']
        attempt = task['attempts'][-1]
        result = 'runs/R20/R20-03-result.json'
        assert not (ROOT/result).exists()
        ctl.write_json(ROOT/result,dict(task_id='R20-03',attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='t1',status='pass',evidence=['runs/R20/design-lock.json','runs/R20/design/HANDOFF.md',
                'runs/R20/design/REPORT.md','runs/R20/coordination/design-reception-check-command.json'])],
            effect=dict(target='Fresh sparse-request reusable data workflow design',
                hypothesis='C12 can guide a usable source-aware research-to-paper handoff on original data.',
                baseline='Source-bound synthetic raw/request; scoped spring and C12 toy evidence retained.',
                conditions='Fresh builder, only specified C12/request/raw; author audit and finite one-day smoke; root reads full design.',
                observations=dict(workflow_docs=5,frozen_files=26,raw_audit=True,bounded_smoke='one day 96 keys',
                    informed_acceptor_preparation='Separate source-interface v2, never sent to builder',
                    full_paper=False,independent_formal_acceptance=False),
                limits='Usable design only. Not independently accepted full solution or model-performance proof. Historical weather/promotion and holiday transfer limitations explicit.',
                metrics=dict(tokens=None,cost=None)),next_action='R20-04: distinct fresh executor actually consumes frozen design through full paper, then independent reception.'))
        ctl.finish(state,ROOT,'R20-03',result)
        ctl.begin(state,ROOT,'R20-04','runs/R20/coordination/design-reception-check-command.json')
        state['execution'].update(current_frontier_task='R20-04',current_report='runs/R20/REPORT.md',
            current_task_process_state='Frozen design received; distinct executor dispatch follows. Formal data/paper reception pending.',
            R20_design_lock='runs/R20/design-lock.json')
        assert not ctl.validate(state,ROOT)
        ctl.write_json(ROOT/'state/continuation.json',state)
        ctl.synchronize(ROOT,state)
        cp = read('state/checkpoint.json')
        cp.update(current_frontier_task='R20-04',current_report='runs/R20/REPORT.md',current_native_pending=[],
            next_action='R20-04: fresh executor consumes frozen design to full original-data result/Chinese paper; independent acceptor follows frozen production.',
            termination=None,unpublished_work=True)
        ctl.write_json(ROOT/'state/checkpoint.json',cp)
    print(json.dumps(dict(design_task='done',frontier='R20-04',previous_tasks_preserved=60)))
