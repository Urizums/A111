"""Check existing terminal evidence and package structure before administrative freeze."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--production', type=Path, required=True)
args = parser.parse_args()
base = args.production
observations = []
for index in range(1, 11):
    matches = list((base / 'evidence').glob(f'{index:03d}-*.json'))
    assert len(matches) == 1, f'nonunique command record {index}'
    path = matches[0]
    receipt = json.loads(path.read_text(encoding='utf-8'))
    assert receipt['state'] == 'finished'
    for key in ['argv', 'cwd', 'begin', 'end', 'exit_code', 'stdout', 'stderr', 'stdout_base64', 'stderr_base64']:
        assert key in receipt, (path.name, key)
    expected = 2 if index in [5, 6] else 0
    assert receipt['exit_code'] == expected, (path.name, receipt['exit_code'])
    observations.append({'record': 'evidence/' + path.name, 'actual_child_exit_code': receipt['exit_code'],
                         'state': receipt['state'], 'interpretation': 'expected rejection' if expected else 'successful command'})
assert not (base / 'fixtures/conflict-output').exists(), 'invalid source must not publish result'
workflow_files = list((base / 'calibration-flow').rglob('*'))
assert all(path.suffix == '.md' for path in workflow_files if path.is_file()), 'skill must be pure Markdown'
assert not list(base.rglob('__pycache__'))
assert not list(base.rglob('*.pyc'))
author = json.loads((base / 'checks/author-receiving-check.json').read_text(encoding='utf-8'))
assert author['status'] == 'author_checks_pass' and author['independent'] is False
rerun = json.loads((base / 'checks/clean-reproduction.json').read_text(encoding='utf-8'))
assert rerun['status'] == 'byte_identical'
script = json.loads((base / 'script-reproduction/reproduction.json').read_text(encoding='utf-8'))
assert script['status'] == 'byte_identical'
for name in ['README.md', 'handoff.md', 'brief-and-gates.md', 'process-history.json', 'checkpoint.json']:
    assert (base / name).is_file()
report = {'status': 'author_delivery_ready', 'independent': False,
          'terminal_commands_before_this_check': observations, 'pure_markdown_workflow_files': 3,
          'no_invalid_publication': True, 'no_pycache': True,
          'claim_limit': 'Administrative and author checks only; no independent correctness/generality verdict.',
          'model': None, 'tokens': None, 'cost': None}
(base / 'checks/final-readiness.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS author delivery readiness: 10 prior terminal receipts, both expected rejections, pure Markdown workflow, two reproductions.')
