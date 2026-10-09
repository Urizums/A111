import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--first', type=Path, required=True)
parser.add_argument('--second', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.first.iterdir() if p.is_file()}
second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.second.iterdir() if p.is_file()}
assert first == second, 'clean rerun output bytes differ'
assert set(first) == {'results.json', 'coordinates.csv', 'days.csv', 'vectors.csv', 'selection-events.csv', '说明.md'}
report = {'status': 'byte_identical', 'files': first, 'first': str(args.first.resolve()),
          'clean_rerun': str(args.second.resolve()), 'independent': False,
          'limit': 'Deterministic reproduction from same raw input; not independent correctness judgment.'}
args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'PASS clean rerun: {len(first)} byte-identical artifacts')
