"""Recompute feasibility from raw identities, geometry and recursive external load."""
import argparse, json, math
from collections import defaultdict
from pathlib import Path
from common import TOL, read_input, write_json

def verify(data, items, solution, source_hash=None):
    errors=[]; v=data['vehicles'][0]
    result={'valid':False,'errors':errors,'per_vehicle':{},'per_item':{},'recomputed_objective':None,'tolerance':TOL}
    def fail(msg): errors.append(msg)
    if source_hash is not None and solution.get('source_sha256') != source_hash:
        fail('source_sha256 differs from actual raw bytes')
    if solution.get('vehicle_type_id') != v['id']:
        fail('vehicle_type_id differs from source')
    rows=solution.get('placements')
    if not isinstance(rows,list):
        fail('placements must be a list'); return result
    by_id={}; by_truck=defaultdict(list); structurally_ok=True
    for p in rows:
        if not isinstance(p,dict):
            fail('placement must be an object'); structurally_ok=False; continue
        name=p.get('item_id'); truck=p.get('vehicle_id')
        if not isinstance(name,str) or name not in items:
            fail(f'unknown source item: {name}'); structurally_ok=False; continue
        if name in by_id:
            fail(f'duplicate item: {name}'); structurally_ok=False; continue
        if not isinstance(truck,str) or not truck:
            fail(f'{name}: invalid vehicle_id'); structurally_ok=False; continue
        for k in ['x_m','y_m','z_m']:
            value=p.get(k)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                fail(f'{name}: {k} must be finite'); structurally_ok=False
        if 'support_id' not in p or (p['support_id'] is not None and not isinstance(p['support_id'],str)):
            fail(f'{name}: missing/invalid support_id'); structurally_ok=False
        for k in ['category','type_id','length_m','width_m','height_m','mass_kg']:
            if k in p and p[k] != items[name][k]:
                fail(f'{name}: output {k} conflicts with raw identity')
        by_id[name]=p; by_truck[truck].append(name)
    missing=sorted(set(items)-set(by_id))
    if missing: fail(f'missing source items: {missing}')
    if not structurally_ok: return result
    actual_support={}
    for truck,names in by_truck.items():
        mass=sum(items[n]['mass_kg'] for n in names)
        result['per_vehicle'][truck]={'mass_kg':mass,'payload_slack_kg':v['payload_kg']-mass,'item_count':len(names)}
        if mass>v['payload_kg']+TOL: fail(f'{truck}: payload exceeded')
        for name in names:
            p=by_id[name]; t=items[name]; x,y,z=(p[k] for k in ['x_m','y_m','z_m'])
            ex=x+t['length_m']; ey=y+t['width_m']; ez=z+t['height_m']
            if min(x,y,z)<-TOL or ex>v['length_m']+TOL or ey>v['width_m']+TOL or ez>v['height_m']-data['clearance_m']+TOL:
                fail(f'{name}: boundary or top clearance violated')
            candidates=[]
            if abs(z)<=TOL:
                actual_support[name]=None
            else:
                for lower in names:
                    if lower==name: continue
                    q=by_id[lower]; u=items[lower]
                    if (abs(q['z_m']+u['height_m']-z)<=TOL and q['x_m']<=x+TOL and q['y_m']<=y+TOL
                        and q['x_m']+u['length_m']>=ex-TOL and q['y_m']+u['width_m']>=ey-TOL):
                        candidates.append(lower)
                if len(candidates)!=1:
                    fail(f'{name}: needs exactly one full-face support, found {candidates}')
                    actual_support[name]=None
                else:
                    actual_support[name]=candidates[0]
                    if items[candidates[0]]['category']!='standard':
                        fail(f'{name}: supported by fragile item')
            if p.get('support_id')!=actual_support[name]: fail(f'{name}: declared support disagrees with geometry')
            result['per_item'][name]={'source_category':t['category'],'source_mass_kg':t['mass_kg'],
                'computed_support_id':actual_support[name],'top_z_m':ez,'top_clearance_m':v['height_m']-ez}
        for i,a in enumerate(names):
            p=by_id[a]; ta=items[a]
            for b in names[i+1:]:
                q=by_id[b]; tb=items[b]
                separated=any(p[k]+ta[d]<=q[k]+TOL or q[k]+tb[d]<=p[k]+TOL
                              for k,d in [('x_m','length_m'),('y_m','width_m'),('z_m','height_m')])
                if not separated: fail(f'{a}/{b}: positive-volume overlap')
    children=defaultdict(list)
    for name,parent in actual_support.items():
        if parent is not None: children[parent].append(name)
    def transmitted(name,visited):
        if name in visited: raise ValueError('support cycle')
        return items[name]['mass_kg']+sum(transmitted(c,visited|{name}) for c in children[name])
    for name in by_id:
        try: external=sum(transmitted(c,{name}) for c in children[name])
        except ValueError as e: fail(str(e)); continue
        t=items[name]; area=t['length_m']*t['width_m']; pressure=external/area
        result['per_item'][name].update({'external_load_kg':external,'top_area_m2':area,'external_load_kg_per_m2':pressure,
            'standard_load_slack_kg_per_m2':data['standard_limit_kg_per_m2']-pressure if t['category']=='standard' else None})
        if t['category']=='fragile' and children[name]: fail(f'{name}: fragile top bears cargo')
        if t['category']=='standard' and pressure>data['standard_limit_kg_per_m2']+TOL:
            fail(f'{name}: cumulative external load {pressure:g} exceeds {data["standard_limit_kg_per_m2"]:g} kg/m2')
    objective={'vehicle_count':len(by_truck),'total_cost_CNY':len(by_truck)*v['cost_CNY']}
    result['recomputed_objective']=objective
    stated=solution.get('objective')
    if not isinstance(stated,dict) or any(isinstance(stated.get(k),bool) or not isinstance(stated.get(k),(int,float)) or
        not math.isfinite(stated[k]) or stated[k]!=val for k,val in objective.items()):
        fail('reported objective differs from raw-source recomputation')
    result['valid']=not errors
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',required=True); ap.add_argument('--solution',required=True); ap.add_argument('--output',required=True)
    a=ap.parse_args(); data,items,digest=read_input(a.input)
    sol=json.loads(Path(a.solution).read_text(encoding='utf-8-sig'))
    result=verify(data,items,sol,digest); write_json(a.output,result)
    print(f"Verification: valid={result['valid']}; errors={result['errors']}")
    raise SystemExit(0 if result['valid'] else 1)
if __name__=='__main__': main()
