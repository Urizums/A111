"""Original-source physical receiver, independent of any producer checker.

Canonical interchange is reviewer-local, not an extra required producer schema:
vehicles [{id, type_id}], placements [{item_id, vehicle_id, x_m, y_m, z_m}].
Any conversion from a frozen producer artifact must be explicit and lossless.
"""
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

EPS = 1e-9  # arithmetic tolerance, never a substitute for domain checks


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check(raw, packet):
    errors = []
    def err(code, **detail):
        errors.append(dict(code=code, **detail))
    types = {}
    items = {}
    for typ in raw.get('types', []):
        if typ.get('id') in types:
            err('raw_duplicate_type', type_id=typ.get('id'))
        types[typ.get('id')] = typ
        for key in ('length_m', 'width_m', 'height_m', 'mass_kg'):
            if not finite(typ.get(key)) or typ[key] <= 0:
                err('raw_domain', type_id=typ.get('id'), field=key)
        if typ.get('category') not in ('standard', 'fragile'):
            err('raw_category', type_id=typ.get('id'))
        for item_id in typ.get('item_ids', []):
            if not isinstance(item_id, str) or not item_id or item_id in items:
                err('raw_item_identity', item_id=item_id)
            items[item_id] = typ
    source_vehicles = {}
    for vehicle in raw.get('vehicles', []):
        vid = vehicle.get('id')
        if vid in source_vehicles:
            err('raw_duplicate_vehicle_type', type_id=vid)
        source_vehicles[vid] = vehicle
        for key in ('length_m', 'width_m', 'height_m', 'payload_kg', 'cost_CNY'):
            if not finite(vehicle.get(key)) or vehicle[key] <= 0:
                err('raw_domain', type_id=vid, field=key)
    for key in ('clearance_m', 'standard_limit_kg_per_m2'):
        if not finite(raw.get(key)) or raw[key] < 0:
            err('raw_domain', field=key)
    if errors:
        return dict(valid=False, errors=errors, recomputed=None)
    vehicles = {}
    for vehicle in packet.get('vehicles', []):
        vid, tid = vehicle.get('id'), vehicle.get('type_id')
        if not isinstance(vid, str) or not vid or vid in vehicles:
            err('vehicle_identity', vehicle_id=vid)
            continue
        if tid not in source_vehicles:
            err('unknown_vehicle_type', vehicle_id=vid, type_id=tid)
            continue
        vehicles[vid] = source_vehicles[tid]
        for key in ('length_m', 'width_m', 'height_m', 'payload_kg', 'cost_CNY'):
            if key in vehicle and (not finite(vehicle[key]) or vehicle[key] != source_vehicles[tid][key]):
                err('vehicle_source_conflict', vehicle_id=vid, field=key)
    placements = packet.get('placements', [])
    count = Counter(p.get('item_id') for p in placements)
    for item_id in items:
        if count[item_id] != 1:
            err('item_multiplicity', item_id=item_id, count=count[item_id])
    geometry = {}
    for pos in placements:
        item_id, vid = pos.get('item_id'), pos.get('vehicle_id')
        if item_id not in items:
            err('unknown_item', item_id=item_id)
            continue
        typ = items[item_id]
        for key in ('category', 'length_m', 'width_m', 'height_m', 'mass_kg'):
            if key in pos and (pos[key] != typ[key] or (key != 'category' and not finite(pos[key]))):
                err('item_source_conflict', item_id=item_id, field=key)
        if 'type_id' in pos and pos['type_id'] != typ['id']:
            err('item_source_conflict', item_id=item_id, field='type_id')
        if vid not in vehicles:
            err('unknown_vehicle', item_id=item_id, vehicle_id=vid)
        coords = [pos.get(k) for k in ('x_m', 'y_m', 'z_m')]
        if not all(finite(v) for v in coords):
            err('coordinate_domain', item_id=item_id)
            continue
        if count[item_id] != 1 or vid not in vehicles:
            continue
        x, y, z = coords
        l, w, h = [typ[k] for k in ('length_m', 'width_m', 'height_m')]
        geometry[item_id] = dict(vid=vid, box=(x,y,z,x+l,y+w,z+h), typ=typ)
        if any(v < -EPS for v in coords):
            err('negative_coordinate', item_id=item_id)
        vehicle = vehicles[vid]
        maxima = (vehicle['length_m'], vehicle['width_m'], vehicle['height_m']-raw['clearance_m'])
        if any(v > m+EPS for v,m in zip((x+l,y+w,z+h), maxima)):
            err('vehicle_bounds_or_clearance', item_id=item_id)
    ids = list(geometry)
    for i, a in enumerate(ids):
        ga = geometry[a]
        for b in ids[i+1:]:
            gb = geometry[b]
            if ga['vid'] != gb['vid']:
                continue
            aa, bb = ga['box'], gb['box']
            if all(min(aa[k+3], bb[k+3])-max(aa[k],bb[k]) > EPS for k in range(3)):
                err('overlap', items=[a,b])
    support = {}
    activation = dict(nonfloor_items=0, support_edges=0, recursive_depth=0, fragile_on_standard=0)
    for item_id, g in geometry.items():
        a = g['box']
        if abs(a[2]) <= EPS:
            support[item_id] = None
            continue
        activation['nonfloor_items'] += 1
        lower = []
        for other, q in geometry.items():
            b = q['box']
            if other != item_id and g['vid'] == q['vid'] and abs(a[2]-b[5]) <= EPS and all(
                b[k] <= a[k]+EPS and b[k+3] >= a[k+3]-EPS for k in (0,1)):
                lower.append(other)
        if len(lower) != 1:
            err('single_complete_support', item_id=item_id, candidates=lower)
            continue
        support[item_id] = lower[0]
        activation['support_edges'] += 1
        lt = geometry[lower[0]]['typ']
        if lt['category'] != 'standard':
            err('fragile_bears_cargo', lower=lower[0], upper=item_id)
        if g['typ']['category'] == 'fragile' and lt['category'] == 'standard':
            activation['fragile_on_standard'] += 1
    outside_load = {item_id: 0.0 for item_id in geometry}
    for item_id, g in geometry.items():
        node, depth, seen = item_id, 0, {item_id}
        while support.get(node) is not None:
            node = support[node]
            if node in seen:
                err('support_cycle', item_id=item_id)
                break
            seen.add(node)
            depth += 1
            outside_load[node] += g['typ']['mass_kg']
        activation['recursive_depth'] = max(activation['recursive_depth'], depth)
    stresses = {}
    for item_id, load in outside_load.items():
        typ = geometry[item_id]['typ']
        stress = load/(typ['length_m']*typ['width_m'])
        stresses[item_id] = stress
        if typ['category'] == 'standard' and stress > raw['standard_limit_kg_per_m2']+EPS:
            err('cumulative_standard_load', item_id=item_id, stress_kg_per_m2=stress)
        if typ['category'] == 'fragile' and load > EPS:
            err('fragile_external_load', item_id=item_id, load_kg=load)
    masses = defaultdict(float)
    for g in geometry.values():
        masses[g['vid']] += g['typ']['mass_kg']
    for vid, mass in masses.items():
        if mass > vehicles[vid]['payload_kg']+EPS:
            err('payload', vehicle_id=vid, mass_kg=mass)
    # Used vehicles drive the raw objective; declared unused vehicles are visible.
    used = sorted(masses)
    unused = sorted(set(vehicles)-set(used))
    objective = [len(used), sum(vehicles[vid]['cost_CNY'] for vid in used)]
    for key, expected in [('vehicle_count', objective[0]), ('total_cost_CNY', objective[1])]:
        if key in packet and (not finite(packet[key]) or abs(packet[key]-expected) > EPS):
            err('objective_report_conflict', field=key)
    return dict(valid=not errors, errors=errors, recomputed=dict(
        lexicographic_objective=objective, mass_by_vehicle_kg=dict(masses),
        cumulative_external_load_kg=outside_load, stress_kg_per_m2=stresses,
        support=support, activation=activation, unused_declared_vehicles=unused))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('raw', type=Path)
    parser.add_argument('packet', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = check(json.loads(args.raw.read_text(encoding='utf-8-sig')),
                   json.loads(args.packet.read_text(encoding='utf-8-sig')))
    content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.out:
        args.out.write_text(content+'\n', encoding='utf-8')
    print(content)
    raise SystemExit(0 if result['valid'] else 2)
