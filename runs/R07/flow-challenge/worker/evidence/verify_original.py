import csv,json,hashlib,ast
from pathlib import Path
root=Path(__file__).resolve().parents[1]
inputs=root/'inputs'; out=json.loads((root/'results/allocation.json').read_text()); rules=json.loads((inputs/'rules.json').read_text())
with (inputs/'requests.csv').open(encoding='utf-8-sig',newline='') as f: source=list(csv.DictReader(f))
rows=out['requests']; expected_ids=[x['request_id'] for x in source]
assert [x['request_id'] for x in rows]==expected_ids, 'request identity/order coverage'
assert [x['source_row'] for x in rows]==list(range(2,2+len(source))), 'CSV source-line coverage'
assert [x['record'] for x in rows]==source, 'raw source records preserved'
assert [x['priority'] for x in rows]==[x['priority'] for x in source], 'priority preserved'
assert out['processing_order']==['R01','R05','R07','R02','R04'], 'priority/submitted_at/request_id ordering'
expected={'R01':'ready','R02':'conflict','R03':'needs_info','R04':'conflict','R05':'ready','R06':'needs_info','R07':'ready'}
assert {x['request_id']:x['status'] for x in rows}==expected, 'status outcomes'
for x in rows:
 basis=rules['complete_statuses']['ready'] if x['status']=='ready' else rules['complete_statuses']['conflict'] if x['status']=='conflict' else rules['incomplete']
 assert x['rule_basis']==basis, f"rule basis {x['request_id']}"
assert out['summary']=={'ready':3,'conflict':2,'needs_info':2}
assert out['inventory_after']==[
 {'equipment_id':'E01','date':'2026-10-08','initial_units':2,'remaining_units':0},
 {'equipment_id':'E02','date':'2026-10-08','initial_units':3,'remaining_units':2},
 {'equipment_id':'E03','date':'2026-10-08','initial_units':1,'remaining_units':0}]
byid={x['request_id']:x for x in rows}
assert byid['R03']['status']=='needs_info' and 'missing room' in byid['R03']['reason'] and byid['R03']['allocation_order'] is None
assert byid['R06']['status']=='needs_info' and 'unknown equipment_id E99' in byid['R06']['reason'] and byid['R06']['allocation_order'] is None
for x in rows:
 if x['status']=='ready': assert '建议调配' in x['advice']
 if x['status']=='conflict': assert '库存不足' in x['advice']
manifest=json.loads((inputs/'manifest.json').read_text())['files']
for entry in manifest:
 original=Path(entry['source_path']).read_bytes(); copied=(inputs/entry['name']).read_bytes()
 assert len(original)==entry['bytes']==len(copied) and hashlib.sha256(original).hexdigest()==entry['sha256']==hashlib.sha256(copied).hexdigest(), entry['name']
for entry in out['source_files']:
 assert entry['sha256']==hashlib.sha256((inputs/entry['file']).read_bytes()).hexdigest(), entry['file']
checklist=(root/'successor/missing-information-checklist.md').read_text()
assert all(token in checklist for token in ['R03','R06','补充使用房间','器材代码 E99','☐'])
code=(root/'tool/allocator.py').read_text()
tree=ast.parse(code)
imports=set()
for node in ast.walk(tree):
 if isinstance(node,ast.Import): imports.update(alias.name.split('.')[0] for alias in node.names)
 elif isinstance(node,ast.ImportFrom) and node.module: imports.add(node.module.split('.')[0])
assert not imports.intersection({'urllib','socket','requests'}), 'unexpected network library import'
print(json.dumps({'verdict':'pass','original_request_count':len(source),'source_rows_preserved':True,'priority_sort':out['processing_order'],'status_counts':out['summary'],'inventory':out['inventory_after'],'needs_info_ids':['R03','R06'],'source_byte_hashes_match':True,'successor_checklist_ids':['R03','R06'],'limit':'coordinator source-based check; native independent review pending'},ensure_ascii=False,indent=2))
