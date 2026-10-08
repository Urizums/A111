"""Source-derived conservative static checker, NOT an optimizer or verdict.

cm/kg convention. Full-bottom support and uniform redistribution are assumptions.
Input adapters/alternative physics will require an explicit receipt after freeze.
"""
from collections import Counter, defaultdict
from itertools import combinations, permutations
import json, math
from pathlib import Path

HERE=Path(__file__).resolve().parent
def source_catalog():
    audit=json.loads((HERE/'independent-source-audit.json').read_text(encoding='utf-8'))
    cargo={}
    for row in audit['docx']['tables'][0]['rows'][1:]:
        cargo[row[0]]={'kind':row[1], 'dims':tuple(float(x) for x in row[2].split('×')),
                       'mass':float(row[3]),'count':int(row[4])}
    p={x['paragraph']:x['text'] for x in audit['docx']['paragraphs']}
    import re
    vehicles={}
    for t,ids in [('T1',(4,5,6)),('T2',(8,9,10))]:
        dims=tuple(float(x) for x in re.findall(r'(\d+)cm',p[ids[0]]))
        vehicles[t]={'dims':dims,'payload':float(re.search(r'(\d+)kg',p[ids[1]])[1]),
                     'cost':float(re.search(r'(\d+)\s*元',p[ids[2]])[1])}
    return cargo,vehicles

def overlap_rectangle(a,b):
    x0=max(a['x'],b['x']); y0=max(a['y'],b['y'])
    x1=min(a['x']+a['dx'],b['x']+b['dx']); y1=min(a['y']+a['dy'],b['y']+b['dy'])
    return (x0,y0,x1,y1) if x1>x0 and y1>y0 else None

def union_area(rectangles):
    """Exact finite rectangle union by x strips, avoids double-counting."""
    if not rectangles: return 0.0
    xs=sorted({r[0] for r in rectangles}|{r[2] for r in rectangles})
    total=0.0
    for x0,x1 in zip(xs,xs[1:]):
        spans=sorted((r[1],r[3]) for r in rectangles if r[0]<x1 and r[2]>x0)
        length=0.0
        if spans:
            lo,hi=spans[0]
            for a,b in spans[1:]:
                if a>hi: length+=hi-lo; lo,hi=a,b
                else: hi=max(hi,b)
            length+=hi-lo
        total+=(x1-x0)*length
    return total

def check(records, *, full_batch=False, fragile_rotation='six', fragile_support='union', eps=1e-7, gap_cm=3, pressure_limit=500, own_mass=False):
    cargo,vehicles=source_catalog()
    violations=[]; groups=defaultdict(list); counts=Counter(); seen=set()
    def fail(code, **detail): violations.append({'code':code, **detail})
    for k,r0 in enumerate(records):
        r=dict(r0)
        required={'item_id','cargo_type','vehicle_id','vehicle_type','x','y','z','dx','dy','dz'}
        if not required.issubset(r): fail('schema',row=k); continue
        if r['item_id'] in seen: fail('duplicate_id',item=r['item_id'])
        seen.add(r['item_id'])
        if r['cargo_type'] not in cargo or r['vehicle_type'] not in vehicles:
            fail('unknown_type',row=k); continue
        if not all(isinstance(r[x],(int,float)) and math.isfinite(r[x]) for x in ['x','y','z','dx','dy','dz']):
            fail('nonfinite',row=k); continue
        if any(r[x]<=0 for x in ['dx','dy','dz']): fail('nonpositive_size',row=k); continue
        c=cargo[r['cargo_type']]; v=vehicles[r['vehicle_type']]
        counts[r['cargo_type']]+=1
        allowed=set(permutations(c['dims']))
        if c['kind']=='定向件': allowed={c['dims']}
        if c['kind']=='易碎件' and fragile_rotation=='upright':
            a,b,h=c['dims']; allowed={(a,b,h),(b,a,h)}
        if not any(all(abs(u-w)<=eps for u,w in zip((r['dx'],r['dy'],r['dz']),d)) for d in allowed):
            fail('orientation_or_size',item=r['item_id'])
        if any(r[x]<-eps for x in ['x','y','z']): fail('negative_coordinate',item=r['item_id'])
        if r['x']+r['dx']>v['dims'][0]+eps or r['y']+r['dy']>v['dims'][1]+eps or r['z']+r['dz']>v['dims'][2]-gap_cm+eps:
            fail('bounds_or_clearance',item=r['item_id'])
        groups[r['vehicle_id']].append(r)
    for t,c in cargo.items():
        if counts[t]>c['count']: fail('inventory_excess',cargo_type=t)
        if full_batch and counts[t]!=c['count']: fail('full_batch_coverage',cargo_type=t,actual=counts[t],required=c['count'])
    summaries=[]
    for vid,rs in groups.items():
        if len({r['vehicle_type'] for r in rs})!=1: fail('vehicle_type_conflict',vehicle=vid)
        v=vehicles[rs[0]['vehicle_type']]
        mass=sum(cargo[r['cargo_type']]['mass'] for r in rs)
        volume=sum(math.prod(cargo[r['cargo_type']]['dims']) for r in rs)
        if mass>v['payload']+eps: fail('payload',vehicle=vid,mass_kg=mass)
        for a,b in combinations(rs,2):
            if all(min(a[q]+a['d'+q],b[q]+b['d'+q])-max(a[q],b[q])>eps for q in ['x','y','z']):
                fail('overlap',items=[a['item_id'],b['item_id']])
        incoming={i:0.0 for i in range(len(rs))}; floor_mass=0.0; max_pressure=0.0
        for i in sorted(range(len(rs)),key=lambda i:rs[i]['z'],reverse=True):
            a=rs[i]; transmitted=cargo[a['cargo_type']]['mass']+incoming[i]
            if abs(a['z'])<=eps: floor_mass+=transmitted; continue
            supports=[]
            for j,b in enumerate(rs):
                if j==i or abs(b['z']+b['dz']-a['z'])>eps: continue
                rectangle=overlap_rectangle(a,b)
                if rectangle:
                    area=(rectangle[2]-rectangle[0])*(rectangle[3]-rectangle[1])
                    supports.append((j,rectangle,area))
                    if cargo[b['cargo_type']]['kind']=='易碎件': fail('on_fragile',items=[a['item_id'],b['item_id']])
                    if cargo[b['cargo_type']]['kind']=='定向件':
                        cx=a['x']+a['dx']/2; cy=a['y']+a['dy']/2
                        if not (b['x']-eps<=cx<=b['x']+b['dx']+eps and b['y']-eps<=cy<=b['y']+b['dy']+eps):
                            fail('directional_center',items=[a['item_id'],b['item_id']])
            bottom=a['dx']*a['dy']; covered=union_area([r for _,r,_ in supports])
            if abs(covered-bottom)>max(eps,bottom*1e-10): fail('full_support',item=a['item_id'],covered=covered,bottom=bottom)
            if cargo[a['cargo_type']]['kind']=='易碎件':
                standard=[(j,r,area) for j,r,area in supports if cargo[rs[j]['cargo_type']]['kind']=='标准件']
                if union_area([r for _,r,_ in standard])<bottom-max(eps,bottom*1e-10): fail('fragile_standard_support',item=a['item_id'])
                if fragile_support=='single' and not any(area>=bottom-max(eps,bottom*1e-10) for _,_,area in standard):
                    fail('fragile_single_standard_support',item=a['item_id'])
            total_contact=sum(area for _,_,area in supports)
            if total_contact>covered+eps: fail('overlapping_supports',item=a['item_id'])
            for j,rectangle,area in supports:
                load=transmitted*area/bottom
                incoming[j]+=load
                pressure=(load+(cargo[rs[j]['cargo_type']]['mass'] if own_mass else 0))/(area/10000)
                max_pressure=max(max_pressure,pressure)
                if pressure>pressure_limit+eps: fail('cumulative_pressure',item=rs[j]['item_id'],pressure_kg_m2=pressure)
        if abs(floor_mass-mass)>max(eps,mass*1e-10): fail('load_conservation',vehicle=vid,ground_kg=floor_mass,mass_kg=mass)
        summaries.append({'vehicle_id':vid,'vehicle_type':rs[0]['vehicle_type'],'count':len(rs),
                          'mass_kg':mass,'volume_cm3':volume,'Uv':volume/math.prod(v['dims']),
                          'Uw':mass/v['payload'],'cost':v['cost'],'max_pressure_kg_m2':max_pressure})
    return {'scope':'conservative full-support / uniform redistribution model only',
            'valid_under_declared_model':not violations,'violations':violations,'counts':dict(counts),
            'vehicles':summaries,'N':len(summaries),'C':sum(v['cost'] for v in summaries)}

def compare_metrics(recomputed, reported, tolerance=1e-9):
    """Independent metric check; no paper parsing or author checker dependency."""
    mismatch=[]
    for name in ['N','C']:
        if name not in reported or not isinstance(reported[name],(int,float)) or not math.isfinite(reported[name]) or abs(recomputed[name]-reported[name])>tolerance:
            mismatch.append(name)
    for truth in recomputed['vehicles']:
        row=next((v for v in reported.get('vehicles',[]) if v.get('vehicle_id')==truth['vehicle_id']),None)
        for name in ['mass_kg','volume_cm3','Uv','Uw']:
            if row is None or name not in row or not isinstance(row[name],(int,float)) or not math.isfinite(row[name]) or abs(truth[name]-row[name])>tolerance*max(1,abs(truth[name])):
                mismatch.append(f"{truth['vehicle_id']}:{name}")
    return mismatch
