"""Exact ordered-chain/vehicle assignment enumeration for identical fixed dimensions."""
import argparse, itertools, math, time
from common import TOL, read_input, write_json

def solve(data, items, source_hash=None):
    start = time.perf_counter()
    v = data['vehicles'][0]
    first = next(iter(items.values()))
    dims = tuple(first[k] for k in ['length_m','width_m','height_m'])
    if any(tuple(t[k] for k in ['length_m','width_m','height_m']) != dims for t in items.values()):
        raise ValueError('Exact solver requires all items to have identical fixed dimensions; no discretized heuristic fallback')
    l,w,h = dims
    nx = math.floor(v['length_m']/l+TOL)
    ny = math.floor(v['width_m']/w+TOL)
    nh = math.floor((v['height_m']-data['clearance_m'])/h+TOL)
    slots = nx*ny
    if min(nx,ny,nh) == 0 or any(t['mass_kg'] > v['payload_kg']+TOL for t in items.values()):
        raise ValueError('infeasible: an individual item cannot fit or exceeds payload')
    ids = tuple(sorted(items))
    total_mass = sum(t['mass_kg'] for t in items.values())
    lower = max(1, math.ceil((total_mass-TOL)/v['payload_kg']), math.ceil(len(ids)/(slots*nh)))
    stats = {'permutation_cut_candidates':0, 'legal_chain_partitions':0, 'vehicle_assignments':0}
    def legal(chain):
        if len(chain) > nh:
            return False
        carried = 0.0
        for name in reversed(chain):
            t=items[name]
            if t['category']=='fragile' and carried>TOL:
                return False
            if t['category']=='standard' and carried/(l*w)>data['standard_limit_kg_per_m2']+TOL:
                return False
            carried += t['mass_kg']
        return True
    for count in range(lower, len(ids)+1):
        for order in itertools.permutations(ids):
            for cut in range(1 << (len(ids)-1)):
                stats['permutation_cut_candidates'] += 1
                chains=[]; current=[]
                for i,name in enumerate(order):
                    current.append(name)
                    if i==len(ids)-1 or cut & (1<<i):
                        chains.append(tuple(current)); current=[]
                if len(chains)>slots*count or not all(legal(c) for c in chains):
                    continue
                stats['legal_chain_partitions'] += 1
                masses=[sum(items[k]['mass_kg'] for k in c) for c in chains]
                for assignments in itertools.product(range(count),repeat=len(chains)):
                    stats['vehicle_assignments'] += 1
                    if len(set(assignments)) != count:
                        continue
                    groups=[[j for j,a in enumerate(assignments) if a==truck] for truck in range(count)]
                    if any(len(g)>slots or sum(masses[j] for j in g)>v['payload_kg']+TOL for g in groups):
                        continue
                    placements=[]
                    for truck,g in enumerate(groups):
                        for slot,j in enumerate(g):
                            chain=chains[j]
                            for level,name in enumerate(chain):
                                placements.append({'item_id':name,'vehicle_id':f'T{truck+1}',
                                    'x_m':(slot % nx)*l,'y_m':(slot // nx)*w,'z_m':level*h,
                                    'support_id':None if level==0 else chain[level-1]})
                    stats['elapsed_seconds']=time.perf_counter()-start
                    return {'schema':'fixed-box-solution/1','source_sha256':source_hash,
                        'vehicle_type_id':v['id'],'placements':sorted(placements,key=lambda p:p['item_id']),
                        'objective':{'vehicle_count':count,'total_cost_CNY':count*v['cost_CNY']},
                        'optimality':{'status':'proved_for_supported_identical_dimensions',
                            'vehicle_lower_bound':lower,'achieved_vehicle_count':count,
                            'all_smaller_vehicle_counts_examined':list(range(lower,count)),
                            'floor_slots_per_vehicle':slots,'height_levels_available':nh,
                            'basis':'Geometric grid injection bound; exhaustive ordered chains and truck assignments; lexicographic cost is fixed per identical truck.'},
                        'search':stats}
    raise ValueError('No feasible fleet found; inspect source constraints')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',required=True); ap.add_argument('--output',required=True)
    args=ap.parse_args()
    data,items,digest=read_input(args.input)
    result=solve(data,items,digest); write_json(args.output,result)
    print(f"Produced {args.output}: {result['objective']}")
if __name__=='__main__': main()
