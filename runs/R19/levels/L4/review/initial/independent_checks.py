"""Reviewer-owned coordinate checks and synthetic controls, not a packing solver.
Canonical inputs are deliberately independent of any future production schema.
Lengths cm, masses kg, force variables kg-equivalent, area cm2 converted /10000.
"""
from collections import Counter
from itertools import combinations, permutations
from math import isfinite
import numpy as np
from scipy.optimize import linprog

TOL = 1e-7

def contact(a, b):
    x0, y0 = max(a['x'], b['x']), max(a['y'], b['y'])
    x1 = min(a['x']+a['l'], b['x']+b['l'])
    y1 = min(a['y']+a['w'], b['y']+b['w'])
    return (x0, y0, x1, y1) if x1-x0 > TOL and y1-y0 > TOL else None

def union_area(rects):
    if not rects:
        return 0.0
    xs = sorted(set([r[0] for r in rects] + [r[2] for r in rects]))
    result = 0.0
    for x0, x1 in zip(xs, xs[1:]):
        ys = sorted((r[1], r[3]) for r in rects if r[0] < (x0+x1)/2 < r[2])
        cover, end = 0.0, None
        for a, b in ys:
            cover += b-a if end is None else max(0.0, b-max(a, end))
            end = b if end is None else max(end, b)
        result += (x1-x0)*cover
    return result

def validate(truck, items, catalog, *, pressure_basis='top', full_support_all=True, directed_center=True):
    errors, supports, contacts = [], {}, []
    ids = [i['id'] for i in items]
    if len(set(ids)) != len(ids):
        errors.append('duplicate_item_id')
    for i in items:
        values = [i[k] for k in ['x','y','z','l','w','h','mass']]
        if not all(isfinite(v) for v in values) or min(i[k] for k in ['l','w','h','mass']) <= 0:
            return {'errors': ['invalid_numeric'], 'valid': False}
        if i['type'] not in catalog:
            return {'errors': ['unknown_cargo_type'], 'valid': False}
        c = catalog[i['type']]
        if abs(i['mass']-c['mass']) > TOL:
            errors.append('mass_not_source_bound')
        dims = (i['l'],i['w'],i['h'])
        allowed = [tuple(c['dims'])] if c['class']=='directed' else set(permutations(c['dims']))
        if not any(all(abs(a-b)<=TOL for a,b in zip(dims,d)) for d in allowed):
            errors.append('orientation')
        if min(i['x'],i['y'],i['z']) < -TOL or i['x']+i['l'] > truck['L']+TOL or i['y']+i['w'] > truck['W']+TOL:
            errors.append('boundary')
        if i['z']+i['h'] > truck['H']-3+TOL:
            errors.append('safety_gap')
    for a,b in combinations(items,2):
        if all(min(a[k]+a[d],b[k]+b[d])-max(a[k],b[k])>TOL for k,d in [('x','l'),('y','w'),('z','h')]):
            errors.append('overlap')
    if sum(i['mass'] for i in items)>truck['capacity']+TOL:
        errors.append('truck_weight')
    for u, upper in enumerate(items):
        if abs(upper['z']) <= TOL:
            r=(upper['x'],upper['y'],upper['x']+upper['l'],upper['y']+upper['w'])
            contacts.append((u,None,r))
            supports[u]=[]
            continue
        direct=[]
        for v, lower in enumerate(items):
            if u==v or abs(lower['z']+lower['h']-upper['z'])>TOL:
                continue
            r=contact(upper,lower)
            if r:
                direct.append((v,r)); contacts.append((u,v,r))
                if catalog[lower['type']]['class']=='fragile':
                    errors.append('fragile_topped')
                if catalog[upper['type']]['class']=='fragile' and catalog[lower['type']]['class']!='standard':
                    errors.append('fragile_nonstandard_support')
                if directed_center and catalog[lower['type']]['class']=='directed':
                    cx,cy=upper['x']+upper['l']/2,upper['y']+upper['w']/2
                    if not (lower['x']-TOL<=cx<=lower['x']+lower['l']+TOL and lower['y']-TOL<=cy<=lower['y']+lower['w']+TOL):
                        errors.append('directed_upper_center')
        supports[u]=direct
        if not direct:
            errors.append('floating')
        area=union_area([r for _,r in direct])
        if (full_support_all or catalog[upper['type']]['class']=='fragile') and abs(area-upper['l']*upper['w'])>TOL:
            errors.append('incomplete_support')
    metrics={'volume_cm3':sum(i['l']*i['w']*i['h'] for i in items), 'weight_kg':sum(i['mass'] for i in items)}
    metrics['UV']=metrics['volume_cm3']/(truck['L']*truck['W']*truck['H'])
    metrics['UV_usable']=metrics['volume_cm3']/(truck['L']*truck['W']*(truck['H']-3))
    metrics['UW']=metrics['weight_kg']/truck['capacity']
    force_result=None
    if not errors and items:
        variables=[]
        for u,v,r in contacts:
            for x,y in [(r[0],r[1]),(r[0],r[3]),(r[2],r[1]),(r[2],r[3])]:
                variables.append((u,v,x,y))
        A=np.zeros((len(items)*3,len(variables)))
        for j,(u,v,x,y) in enumerate(variables):
            A[3*u:3*u+3,j]=[1,x,y]
            if v is not None:
                A[3*v:3*v+3,j]=[-1,-x,-y]
        b=np.array([q for i in items for q in [i['mass'],i['mass']*(i['x']+i['l']/2),i['mass']*(i['y']+i['w']/2)]])
        capA=np.zeros((len(items),len(variables)))
        cap=[]
        for n,i in enumerate(items):
            for j,(_,v,_,_) in enumerate(variables):
                if v==n: capA[n,j]=1
            area=i['l']*i['w'] if pressure_basis=='top' else union_area([r for _,v,r in contacts if v==n])
            cap.append(500*area/10000)
        result=linprog(np.zeros(len(variables)),A_ub=capA,b_ub=cap,A_eq=A,b_eq=b,bounds=(0,None),method='highs',options={'time_limit':10})
        force_result={'status':int(result.status),'message':result.message,'pressure_basis':pressure_basis,'time_limit_seconds':10}
        if result.success:
            force_result.update({'incoming_loads_kg':(capA@result.x).tolist(),'limits_kg':cap,
                                 'max_balance_residual':float(np.max(abs(A@result.x-b))),
                                 'minimum_reaction':float(np.min(result.x))})
        else:
            errors.append('static_load_infeasible' if result.status==2 else 'static_load_unverified')
    return {'valid':not errors,'errors':sorted(set(errors)),'metrics':metrics,'forces':force_result}

def inventory_errors(items,catalog,complete):
    count=Counter(i['type'] for i in items)
    errors=[]
    if len({i['id'] for i in items})!=len(items):errors.append('duplicate_item_id')
    if set(count)-set(catalog):errors.append('unknown_cargo_type')
    for t,c in catalog.items():
        if count[t]>c['quantity']:errors.append('inventory_excess')
        if complete and count[t]!=c['quantity']:errors.append('inventory_missing_or_excess')
    return sorted(set(errors))

def aggregate(trucks,results):
    return {'N':len(trucks),'cost':sum(t['cost'] for t in trucks),
            'UV':sum(r['metrics']['volume_cm3'] for r in results)/sum(t['L']*t['W']*t['H'] for t in trucks),
            'UW':sum(r['metrics']['weight_kg'] for r in results)/sum(t['capacity'] for t in trucks)}
