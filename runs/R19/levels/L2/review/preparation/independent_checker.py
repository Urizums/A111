"""Independent review oracle, not solver. Raw anchors: DOCX paragraphs 13-19.
All dimensions mm; loads kg; pressure kg/m^2. Geometry rebuilds support edges.
Area-proportional cumulative transfer is a declared assumption, not unique physics.
"""
import math
from collections import Counter

def union_area(rects):
    xs=sorted({a for r in rects for a in (r[0],r[2])}); area=0.0
    for x0,x1 in zip(xs,xs[1:]):
        seg=sorted((r[1],r[3]) for r in rects if r[0]<x1 and r[2]>x0)
        length=0.0; end=None
        for lo,hi in seg:
            if end is None: length+=hi-lo; end=hi
            elif hi>end: length+=hi-max(lo,end); end=hi
        area+=(x1-x0)*length
    return area

def validate_layout(items, vehicles, placements, full=True, fragile_fixed=False, full_support_all=False, pressure_limit=500, tol=1e-7):
    errors=[]; warnings=[]; loads={}; contact=[]
    ids=[p.get('item_id') for p in placements]
    if len(set(ids))!=len(ids):errors.append({'rule':'duplicate_item'})
    unknown=set(ids)-set(items)
    if unknown: errors.append({'rule':'unknown_item','ids':sorted(unknown)})
    if full and set(ids)!=set(items):errors.append({'rule':'inventory_equality','missing':sorted(set(items)-set(ids))})
    boxes=[]
    for p in placements:
        i=items.get(p.get('item_id')); v=vehicles.get(p.get('vehicle_id'))
        if i is None or v is None:
            errors.append({'rule':'unknown_item_or_vehicle','item':p.get('item_id')}); continue
        xyz=p.get('xyz',[]); dims=p.get('dims',[]); weight=i.get('weight')
        values=xyz+dims+[weight]
        if len(xyz)!=3 or len(dims)!=3 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):
            errors.append({'rule':'nonfinite_or_missing','item':p['item_id']}); continue
        if any(x<=0 for x in dims) or weight<=0: errors.append({'rule':'nonpositive_dimension_or_weight','item':p['item_id']})
        cat=i['category']; canonical=tuple(i['dims']); actual=tuple(dims)
        allowed=set(__import__('itertools').permutations(canonical)) if cat=='standard' else {canonical,(canonical[1],canonical[0],canonical[2])} if cat=='fragile' and not fragile_fixed else {canonical}
        if actual not in allowed:errors.append({'rule':'orientation','item':p['item_id']})
        high=[xyz[k]+dims[k] for k in range(3)]; lim=[v['dims'][0],v['dims'][1],v['dims'][2]-v['clearance']]
        if any(x < -tol for x in xyz) or any(high[k]>lim[k]+tol for k in range(3)):
            errors.append({'rule':'boundary_clearance','item':p['item_id']})
        boxes.append({**p,'xyz':xyz,'dims':dims,'high':high,'weight':weight,'category':cat})
    byvehicle={}
    for b in boxes:byvehicle.setdefault(b['vehicle_id'],[]).append(b)
    metrics={}
    for vid,bs in byvehicle.items():
        v=vehicles[vid]; weight=sum(b['weight'] for b in bs); vol=sum(math.prod(b['dims']) for b in bs)
        metrics[vid]={'weight':weight,'volume_mm3':vol,'volume_utilization':vol/math.prod(v['dims']),'weight_utilization':weight/v['payload'],'cost':v['cost'],'counts':dict(Counter(b['cargo'] for b in bs))}
        if weight>v['payload']+tol:errors.append({'rule':'payload','vehicle':vid})
        for n,a in enumerate(bs):
            for b in bs[n+1:]:
                if all(min(a['high'][k],b['high'][k])-max(a['xyz'][k],b['xyz'][k])>tol for k in range(3)):
                    errors.append({'rule':'overlap','items':[a['item_id'],b['item_id']]})
        supports={b['item_id']:[] for b in bs}
        for u in bs:
            if abs(u['xyz'][2])<=tol:continue
            rects=[]
            for l in bs:
                if abs(l['high'][2]-u['xyz'][2])>tol:continue
                r=[max(u['xyz'][0],l['xyz'][0]),max(u['xyz'][1],l['xyz'][1]),min(u['high'][0],l['high'][0]),min(u['high'][1],l['high'][1])]
                area=max(0,r[2]-r[0])*max(0,r[3]-r[1])
                if area<=tol:continue
                rects.append(r); supports[u['item_id']].append((l,area));contact.append({'upper':u['item_id'],'lower':l['item_id'],'area_mm2':area})
                if l['category']=='fragile':errors.append({'rule':'fragile_no_load','items':[u['item_id'],l['item_id']]})
                if u['category']=='fragile' and l['category']!='standard':errors.append({'rule':'fragile_support_material','items':[u['item_id'],l['item_id']]})
                if l['category']=='directional':
                    center=[u['xyz'][k]+u['dims'][k]/2 for k in (0,1)]
                    if any(center[k]<l['xyz'][k]-tol or center[k]>l['high'][k]+tol for k in (0,1)):
                        errors.append({'rule':'directional_local_center','items':[u['item_id'],l['item_id']]})
            area=union_area(rects); footprint=u['dims'][0]*u['dims'][1]
            if not rects:errors.append({'rule':'floating','item':u['item_id']})
            if u['category']=='fragile' and area<footprint-tol:errors.append({'rule':'fragile_full_support','item':u['item_id'],'coverage':area/footprint})
            elif full_support_all and area<footprint-tol:errors.append({'rule':'declared_conservative_support','item':u['item_id'],'coverage':area/footprint})
            elif area<footprint-tol:warnings.append({'rule':'partial_nonfragile_support_requires_stability_assumption','item':u['item_id']})
        incoming={b['item_id']:0.0 for b in bs}
        for u in sorted(bs,key=lambda b:b['xyz'][2],reverse=True):
            uid=u['item_id']; ss=supports[uid]; total=u['weight']+incoming[uid]
            loads[uid]={'incoming_load_kg':incoming[uid],'self_plus_transmitted_kg':total}
            denom=sum(a for _,a in ss)
            for l,a in ss:
                force=total*a/denom; pressure=force/(a/1e6)
                incoming[l['item_id']]+=force
                if pressure>pressure_limit+tol:errors.append({'rule':'cumulative_contact_pressure','upper':uid,'lower':l['item_id'],'pressure_kg_m2':pressure})
        if abs(sum(b['weight']+incoming[b['item_id']] for b in bs if abs(b['xyz'][2])<=tol)-weight)>tol:
            errors.append({'rule':'load_conservation','vehicle':vid})
    return {'valid':not errors,'errors':errors,'warnings':warnings,'metrics':metrics,'loads':loads,'contacts':contact,'total_cost':sum(m['cost'] for m in metrics.values()),'vehicles_used':len(metrics),'inventory':dict(Counter(b['cargo'] for b in boxes))}

