"""Integrate source-bound independent reception, preserving its original verdicts."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser()
p.add_argument('action', choices=['check', 'integrate'])
a = p.parse_args()
def read(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))
for rel in ['runs/R20/review/initial-lock.json', 'runs/R20/review/source-recheck-lock.json']:
    for row in read(rel)['files']:
        b = (ROOT / row['path']).read_bytes()
        assert (len(b), hashlib.sha256(b).hexdigest()) == (row['size_bytes'], row['sha256'])
scope = ROOT / 'runs/R20/review/source-recheck'
manifest = read('runs/R20/review/source-recheck/manifest.json')
for row in manifest['files']:
    b = (scope / row['path']).read_bytes()
    assert (len(b), hashlib.sha256(b).hexdigest()) == (row['bytes'], row['sha256'])
assert hashlib.sha256((scope / 'manifest.json').read_bytes()).hexdigest() == 'f754b911d8fad05c25502aa69c472fca0968b581ad3cb89e3aec0b49bd501166'
for f in scope.glob('command-*.json'):
    r = json.loads(f.read_text(encoding='utf-8'))
    assert r['state'] == 'finished' and r['end'] and r['exit_code'] == 0
first = read('runs/R20/review/initial/first-result.json')
addendum = read('runs/R20/review/source-recheck/source-recheck-result.json')
assert all(first['domains'][k]['verdict'] == 'PASS' for k in ['d1', 'd2', 'd3', 'd4', 'd5'])
assert not addendum['initial_domain_implication']['necessary_defect_found']
assert addendum['final_residual_lineage_exact_match'] and addendum['origin_pool_comparisons_all_match']
assert all(addendum['boundary_controls'][k] for k in ['ready_equal_origin_admitted', 'ready_after_origin_excluded',
    'single_late_coordinate_blocks_whole_vector', '95_of_96_incomplete_vector_rejected'])
correction = addendum['initial_first_result_path_correction']
b = (ROOT / correction['correct_path']).read_bytes()
assert (len(b), hashlib.sha256(b).hexdigest()) == (correction['correct_bytes'], correction['correct_sha256'])
assert not (ROOT / correction['wrong_path']).exists()
assert read(correction['correct_path'])['state'] == 'finished' and read(correction['correct_path'])['exit_code'] == 0
initial = ROOT / 'runs/R20/review/initial'
before = json.loads((initial / 'command-freeze-before-holdout.json').read_text(encoding='utf-8'))
future = json.loads((initial / 'command-holdout-evaluation.json').read_text(encoding='utf-8'))
assert read(correction['correct_path'])['end']['utc'] < before['begin']['utc']
assert before['end']['utc'] < future['begin']['utc']
if a.action == 'check':
    print(json.dumps(dict(independent_first_gates='d1-d5 PASS', initial_frozen_files=144, informed_addendum_files=14,
        source_reference_corrected_separately=True, calibration_raw_vectors=84, eligible_vectors=83,
        production_injection_claimed=False, future_evaluation_once_after_first_freeze=True,
        future_nominal90_coverage=first['holdout_evaluation']['nominal90_interval_coverage'],
        limits='One synthetic task, author repairs retained, informed addendum separate; no award, official compliance or generality.'), ensure_ascii=False))
else:
    sys.path.insert(0, str(ROOT / 'scripts'))
    import continuation as ctl
    with ctl.locked(ROOT):
        state = ctl.load(ROOT)
        old = read('runs/R20/before/task-identities.json')
        assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
        assert not state['execution']['current_native_pending']
        receipt = 'runs/R20/coordination/data-reception-check-command.json'
        assert read(receipt)['state'] == 'finished' and read(receipt)['exit_code'] == 0
        task = ctl.task_map(state)['R20-04']; attempt = task['attempts'][-1]
        result = 'runs/R20/R20-04-result.json'
        assert not (ROOT / result).exists()
        ctl.write_json(ROOT / result, dict(task_id=task['id'], attempt_id=attempt['id'], requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='t1', status='pass', evidence=['runs/R20/execution-lock.json',
                'runs/R20/review/initial-lock.json', 'runs/R20/review/source-recheck-lock.json', receipt])],
            effect=dict(target='Original data workflow through complete Chinese paper and independent reception',
                hypothesis='The sparse-request derived C12 workflow supports an executable scientific solution and receiving review.',
                baseline='Frozen original problem/raw and external d1-d5; R19 historical diagnoses retained.',
                conditions='Distinct fresh builder/executor/acceptor; same authors/receivers repair their own failures; first production frozen before holdout.',
                observations=dict(independent_domains={k: v['verdict'] for k,v in first['domains'].items()},
                    paper_pages=11, predicted_and_decision_keys=1344, actual_raw_rerun=True,
                    complete_pdf_view=True, calibration_source_recheck='informed independent raw reconstruction',
                    metadata_wrong_path='Original initial JSON retained; separate source correction.',
                    historical_author_and_receiver_failures='Preserved in frozen versions/commands, no resets.',
                    future_holdout=first['holdout_evaluation']),
                limits='Single synthetic task, not actual October contest, award or general superiority. Future coverage 85.71% below nominal90 is a disclosed limit, not a retroactive gate. Calibration injection was independent reconstruction, not a callable production consumer.',
                metrics=dict(tokens=None, cost=None)), next_action='R20-05: source-bound synthesis; only demonstrated source clarifications receive a separate document identity and forward reception.'))
        ctl.finish(state, ROOT, 'R20-04', result)
        ctl.begin(state, ROOT, 'R20-05', receipt)
        state['execution'].update(current_frontier_task='R20-05', current_report='runs/R20/REPORT.md',
            R20_status='original_data_paper_independently_accepted_scoped',
            current_task_process_state='All R20 production/reception actors terminal; source synthesis active.')
        assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
        assert not ctl.validate(state, ROOT)
        ctl.write_json(ROOT / 'state/continuation.json', state); ctl.synchronize(ROOT, state)
        cp = read('state/checkpoint.json')
        cp.update(current_frontier_task='R20-05', current_report='runs/R20/REPORT.md', current_native_pending=[],
            next_action='R20-05: integrate actual scientific evidence and narrow document-only source decisions; preserve first failures and holdout history.',
            termination=None, unpublished_work=True, R20_status=state['execution']['R20_status'])
        ctl.write_json(ROOT / 'state/checkpoint.json', cp)
    print(json.dumps(dict(task='R20-04 done', frontier='R20-05', old_task_identities_preserved=60)))
