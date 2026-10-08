"""Baseline and targeted critical-parameter variants, using the same item identities."""
import argparse, copy, math
from common import read_input, write_json
from solve import solve
from verify import verify

def experiments(data,items,digest):
    variants=[]
    for label,limit,payload in [('original',150,500),('load_160',160,500),('load_100_boundary',100,500),('load_99',99,500),
        ('load_60_boundary',60,500),('load_59',59,500),('payload_360_boundary',150,360),('payload_359',150,359)]:
        d=copy.deepcopy(data); d['standard_limit_kg_per_m2']=limit; d['vehicles'][0]['payload_kg']=payload
        s=solve(d,items,digest if label=='original' else None); c=verify(d,items,s,None)
        variants.append({'case':label,'standard_limit_kg_per_m2':limit,'payload_kg':payload,'objective':s['objective'],
            'placements':s['placements'],'valid':c['valid'],'errors':c['errors'],'search':s['search'],
            'optimality':s['optimality'],'is_original_input':label=='original'})
        if not c['valid']: raise AssertionError(f'{label}: {c["errors"]}')
    v=data['vehicles'][0]; ids=sorted(items)
    l,w,h=(next(iter(items.values()))[k] for k in ['length_m','width_m','height_m'])
    nx=math.floor(v['length_m']/l); ny=math.floor(v['width_m']/w); slots=nx*ny
    baseline={'schema':'fixed-box-solution/1','source_sha256':digest,'vehicle_type_id':v['id'],'placements':[]}
    for index,name in enumerate(ids):
        truck=index//slots; slot=index%slots
        baseline['placements'].append({'item_id':name,'vehicle_id':f'T{truck+1}','x_m':slot%nx*l,'y_m':slot//nx*w,'z_m':0,'support_id':None})
    count=math.ceil(len(ids)/slots); baseline['objective']={'vehicle_count':count,'total_cost_CNY':count*v['cost_CNY']}
    check=verify(data,items,baseline,digest)
    if not check['valid']: raise AssertionError('Floor baseline unexpectedly invalid')
    return {'floor_only_baseline':{'solution':baseline,'checks':check},'parameter_variants':variants,
        'scope':'Only the listed deterministic variants; no empirical road, axle or loading-channel measurements.'}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(); d,i,h=read_input(a.input); r=experiments(d,i,h); write_json(a.output,r)
    print([(v['case'],v['objective']) for v in r['parameter_variants']])
if __name__=='__main__': main()
