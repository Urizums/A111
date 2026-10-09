"""Retain two real affected-interface challenge fixtures; never alter original inputs."""
import argparse
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--inputs', type=Path, required=True)
parser.add_argument('--outputs', type=Path, required=True)
parser.add_argument('--fixtures', type=Path, required=True)
args = parser.parse_args()
raw_case = args.fixtures / 'conflicting-label-input'
shutil.copytree(args.inputs, raw_case)
with (raw_case / 'raw/labels.csv').open('a', encoding='utf-8', newline='') as handle:
    handle.write('2026-05-01,A,1,2026-05-02T09:00:00+08:00,111\n')
consumer_case = args.fixtures / 'future-label-consumer'
shutil.copytree(args.outputs, consumer_case)
path = consumer_case / 'results.json'
payload = json.loads(path.read_text(encoding='utf-8'))
coord = payload['origins'][0]['coordinates'][0]
raw_row = next(c for c in payload['origins'][1]['coordinates'] if c['target_date'] == coord['target_date'] and c['series_id'] == coord['series_id'])
coord['label'] = raw_row['label']
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(args.fixtures / 'fixture-design.json').write_text(json.dumps({
    'purpose': 'author relevant rejection tests; not blind independent checker evaluation',
    'raw_case': {'path': str(raw_case), 'defect': 'same coordinate/revision/arrival different actual_units'},
    'consumer_case': {'path': str(consumer_case), 'defect': 'valid actual source revision selected before its arrival'},
    'original_inputs_untouched': True
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Created retained same-version conflict and future-label consumer fixtures.')
