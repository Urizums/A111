"""Coordinate-only verification. Does not import or trust packing code."""
import json, csv, argparse
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from numeric_contract import input_errors,placement_errors,rejection

def validate(instance, config, rows, complete=True):
    errors=input_errors(instance,config)
    if errors:return rejection(errors)
    errors=placement_errors(rows,config.get('tolerance_cm',1e-6))
    if errors:return rejection(errors)
    cargo={g['id']:g for g in instance['cargo']}; vehicles={v['id']:v for v in instance['vehicles']}
    eps=config.get('tolerance_cm',1e-6); errors=[]; loads=[]; truckstats=[]
    counts=Counter(r['cargo_type'] for r in rows); ids=[r['item_id'] for r in rows]
    if len(set(ids))!=len(ids): errors.append('duplicate_item_id')
    for g in cargo:
        if counts[g]>cargo[g]['quantity'] or (complete and counts[g]!=cargo[g]['quantity']):errors.append('inventory:'+g)
    for r in rows:
        g=cargo.get(r['cargo_type'])
        if not g:errors.append('unknown_cargo');continue
        try:
            serial=int(r['item_id'].split('-')[-1])
            if not 1<=serial<=g['quantity'] or not r['item_id'].startswith(g['id']+'-'):errors.append('invalid_item_id')
        except (ValueError,KeyError):errors.append('invalid_item_id')
        d=[float(r[k]) for k in ['l','w','h']]
        if sorted(d)!=sorted(g['dims']):errors.append('dimension:'+r['item_id'])
        if g['class']=='oriented' and d!=g['dims']:errors.append('orientation:'+r['item_id'])
        if g['class']=='fragile' and config.get('fragile_orientation')=='original_height' and d[2]!=g['dims'][2]:errors.append('fragile_orientation:'+r['item_id'])
        ori=r.get('orientation','')
        if len(ori)!=3 or set(ori)!=set('LWH') or [g['dims']['LWH'.index(c)] for c in ori]!=d:errors.append('orientation_code:'+r['item_id'])
    bytruck=defaultdict(list)
    for r in rows:bytruck[r['truck_id']].append(r)
    for truck, rs in bytruck.items():
        types=set(r['vehicle_type'] for r in rs)
        if len(types)!=1 or next(iter(types)) not in vehicles:errors.append('truck_type');continue
        v=vehicles[next(iter(types))]; n=len(rs)
        a=np.array([[float(r[k]) for k in ['x','y','z','l','w','h']] for r in rs]); low=a[:,:3];hi=low+a[:,3:]
        if np.any(low < -eps) or np.any(hi>np.array([v['dims'][0],v['dims'][1],v['dims'][2]-config['gap_cm']])+eps):errors.append('boundary:'+truck)
        if np.any(a[:,3:]<=0):errors.append('nonpositive_size')
        overlap=np.all(np.minimum(hi[:,None,:],hi[None,:,:])-np.maximum(low[:,None,:],low[None,:,:])>eps,axis=2)
        if np.any(np.triu(overlap,1)):errors.append('overlap:'+truck)
        support={}; children=defaultdict(list)
        for i,r in enumerate(rs):
            if abs(low[i,2])<=eps:continue
            possible=np.where((np.abs(hi[:,2]-low[i,2])<=eps)&(low[:,0]<=low[i,0]+eps)&(low[:,1]<=low[i,1]+eps)&(hi[:,0]>=hi[i,0]-eps)&(hi[:,1]>=hi[i,1]-eps))[0]
            if len(possible)!=1:errors.append('full_support:'+r['item_id']);continue
            j=int(possible[0]);support[i]=j;children[j].append(i)
            if cargo[rs[j]['cargo_type']]['class']=='fragile':errors.append('fragile_top:'+rs[j]['item_id'])
            if cargo[r['cargo_type']]['class']=='fragile' and cargo[rs[j]['cargo_type']]['class']!='standard':errors.append('fragile_base:'+r['item_id'])
            center=(low[i,:2]+hi[i,:2])/2
            if cargo[rs[j]['cargo_type']]['class']=='oriented' and (np.any(center<low[j,:2]-eps) or np.any(center>hi[j,:2]+eps)):errors.append('center:'+r['item_id'])
        masses=np.array([cargo[r['cargo_type']]['mass'] for r in rs],dtype=float);external=np.zeros(n)
        for i in sorted(range(n),key=lambda j:low[j,2],reverse=True):
            if i in support:
                j=support[i];external[j]+=masses[i]+external[i]
                pressure=(masses[i]+external[i])/(a[i,3]*a[i,4]/10000)
                if pressure>config['pressure_kg_m2']+eps:errors.append('contact_pressure:'+rs[i]['item_id'])
        for i,r in enumerate(rs):
            area=a[i,3]*a[i,4]/10000
            if external[i]>config['pressure_kg_m2']*area+eps:errors.append('cumulative_load:'+r['item_id'])
            parent=rs[support[i]]['item_id'] if i in support else 'FLOOR'
            if str(r.get('support_ids',''))!=parent:errors.append('support_metadata:'+r['item_id'])
            loads.append({'truck_id':truck,'item_id':r['item_id'],'support_id':parent,'external_load_kg':float(external[i]),'top_area_m2':float(area),'load_limit_kg':config['pressure_kg_m2']*float(area)})
        weight=float(masses.sum()); volume=float(np.prod(a[:,3:],axis=1).sum())
        if weight>v['capacity']+eps:errors.append('capacity:'+truck)
        truckstats.append({'truck_id':truck,'vehicle_type':v['id'],'items':n,'mass_kg':weight,'volume_cm3':volume,'UV':volume/np.prod(v['dims']),'UW':weight/v['capacity'],'usable_UV':volume/(v['dims'][0]*v['dims'][1]*(v['dims'][2]-config['gap_cm'])),'cost':v['cost']})
    volume=sum(s['volume_cm3'] for s in truckstats);weight=sum(s['mass_kg'] for s in truckstats)
    return {'valid':not errors,'errors':sorted(set(errors)),'inventory':dict(counts),'truck_count':len(truckstats),'cost':sum(s['cost'] for s in truckstats),'mass_kg':weight,'volume_cm3':volume,'UV':volume/sum(np.prod(vehicles[s['vehicle_type']]['dims']) for s in truckstats) if truckstats else 0,'UW':weight/sum(vehicles[s['vehicle_type']]['capacity'] for s in truckstats) if truckstats else 0,'trucks':truckstats,'support_loads':loads}

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--config',required=True);p.add_argument('--placements',required=True);p.add_argument('--out',required=True);p.add_argument('--single',action='store_true');args=p.parse_args()
    result=validate(json.loads(Path(args.data).read_text(encoding='utf8')),json.loads(Path(args.config).read_text(encoding='utf8')),list(csv.DictReader(open(args.placements,encoding='utf-8-sig',newline=''))),not args.single)
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('VALID' if result['valid'] else result['errors']);return 0 if result['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
