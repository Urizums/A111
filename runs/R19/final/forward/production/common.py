"""Source-bound input audit. Standard library only; source is never modified."""
import hashlib, json, math
from pathlib import Path
TOL = 1e-8

def number(v, name, positive=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f'{name}: finite numerical value required')
    if (positive and v <= 0) or (not positive and v < 0):
        raise ValueError(f'{name}: invalid sign')
    return float(v)

def read_input(path):
    blob = Path(path).read_bytes()
    data = json.loads(blob.decode('utf-8-sig'))
    if len(data['vehicles']) != 1:
        raise ValueError('This implementation supports exactly one homogeneous vehicle type')
    v = data['vehicles'][0]
    if not isinstance(v['id'], str) or not v['id']:
        raise ValueError('vehicle id must be a nonempty string')
    for k in ['length_m','width_m','height_m','payload_kg']:
        number(v[k], k, True)
    number(v['cost_CNY'], 'cost_CNY')
    number(data['clearance_m'], 'clearance_m')
    number(data['standard_limit_kg_per_m2'], 'standard_limit_kg_per_m2')
    if data['clearance_m'] >= v['height_m']:
        raise ValueError('clearance leaves no usable height')
    items = {}
    type_ids = set()
    for t in data['types']:
        if t['id'] in type_ids:
            raise ValueError('duplicate type id')
        type_ids.add(t['id'])
        if t['category'] not in ['standard','fragile']:
            raise ValueError('unsupported source category')
        for k in ['length_m','width_m','height_m','mass_kg']:
            number(t[k], k, True)
        for item_id in t['item_ids']:
            if not isinstance(item_id, str) or not item_id or item_id in items:
                raise ValueError('invalid or duplicated item id')
            items[item_id] = {k: t[k] for k in ['category','length_m','width_m','height_m','mass_kg']}
            items[item_id]['type_id'] = t['id']
    if not items:
        raise ValueError('empty instance is outside the requested nonempty transport task')
    return data, items, hashlib.sha256(blob).hexdigest()

def write_json(path, obj):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
