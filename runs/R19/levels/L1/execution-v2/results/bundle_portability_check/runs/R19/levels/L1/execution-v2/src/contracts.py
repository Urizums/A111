"""Original D-question identities; scenario values may vary, identities may not.

This is an input contract, not an additional packing constraint. The category
map is the five rows of official attachment 1. normalize.py pins its SHA256.
"""
import math

SOURCE_CATEGORIES = {'G1': 'standard', 'G2': 'standard', 'G3': 'fragile',
                     'G4': 'directional', 'G5': 'directional'}


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_config(cfg):
    if not isinstance(cfg, dict):
        raise ValueError('config must be an object')
    for name, identities in [('cargo', set(SOURCE_CATEGORIES)), ('vehicles', {'T1', 'T2'})]:
        records = cfg.get(name)
        if not isinstance(records, list) or not records or any(not isinstance(r, dict) for r in records):
            raise ValueError(name + ' must contain records')
        ids = [r.get('id') for r in records]
        if any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
            raise ValueError(name + ': duplicate or invalid identities')
        # A single available vehicle type is a lawful fixed-type scenario.
        if (name == 'cargo' and set(ids) != identities) or not set(ids) <= identities:
            raise ValueError(name + ': unsupported original identities')
        for r in records:
            ds = r.get('dims')
            if not isinstance(ds, (list, tuple)) or len(ds) != 3 or any(not finite_number(x) or x <= 0 for x in ds):
                raise ValueError(name + ': dimensions must be positive finite numbers')
            keys = ['weight'] if name == 'cargo' else ['payload', 'cost']
            if any(not finite_number(r.get(k)) or r[k] <= 0 for k in keys):
                raise ValueError(name + ': positive finite physical fields required')
            if name == 'cargo':
                if r.get('category') != SOURCE_CATEGORIES[r['id']]:
                    raise ValueError('source category identity mismatch: ' + r['id'])
                q = r.get('quantity')
                if not isinstance(q, int) or isinstance(q, bool) or q < 0:
                    raise ValueError('quantity must be a nonnegative integer')
    if not finite_number(cfg.get('clearance')) or cfg['clearance'] < 0:
        raise ValueError('clearance must be finite and nonnegative')
    if not finite_number(cfg.get('bearing')) or cfg['bearing'] <= 0:
        raise ValueError('bearing must be positive and finite')
    for flag in ['fragile_rotation', 'fragile_floor_only', 'directional_center_each']:
        if flag in cfg and not isinstance(cfg[flag], bool):
            raise ValueError(flag + ' must be boolean')
    return cfg
