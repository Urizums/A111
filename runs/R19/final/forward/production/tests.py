"""Actual rejection experiments; all mutations in memory, original raw unchanged."""
import argparse, copy, json
from pathlib import Path
from common import read_input, write_json
from verify import verify

def run(data,items,sol,digest):
    cases=[]
    def check(name,candidate,expected):
        r=verify(data,items,candidate,digest)
        cases.append({'case':name,'expected_acceptance':expected,'accepted':r['valid'],
            'assertion_passed':r['valid']==expected,'errors':r['errors'],'mutated_solution':candidate if name!='original_valid' else None})
    check('original_valid',sol,True)
    triple=copy.deepcopy(sol)
    triple['placements']=[{'item_id':k,'vehicle_id':'T1','x_m':x,'y_m':0,'z_m':z,'support_id':s}
        for k,x,z,s in [('S1',0,0,None),('S2',0,1,'S1'),('F1',0,2,'S2'),('S3',1,0,None)]]
    check('transmitted_160_exceeds_150',triple,False)
    direct=copy.deepcopy(triple)
    direct['placements'][2]['category']='standard'
    check('output_category_cannot_launder_identity',direct,False)
    adjacent=copy.deepcopy(sol)
    adjacent['placements']=[{'item_id':k,'vehicle_id':'T1','x_m':x,'y_m':0,'z_m':z,'support_id':s}
        for k,x,z,s in [('S1',0,0,None),('S2',0,1,'S1'),('S3',1,0,None),('F1',1,1,'S2')]]
    check('same_height_neighbor_not_support',adjacent,False)
    fragile=copy.deepcopy(sol)
    fragile['placements']=[{'item_id':k,'vehicle_id':'T1','x_m':x,'y_m':0,'z_m':z,'support_id':s}
        for k,x,z,s in [('F1',0,0,None),('S1',0,1,'F1'),('S2',1,0,None),('S3',1,1,'S2')]]
    check('fragile_cannot_support',fragile,False)
    overlap=copy.deepcopy(sol)
    overlap['placements']=[{'item_id':k,'vehicle_id':'T1','x_m':0,'y_m':0,'z_m':0,'support_id':None} for k in items]
    check('overlap_rejected',overlap,False)
    missing=copy.deepcopy(sol); missing['placements'].pop(); check('missing_id_rejected',missing,False)
    duplicate=copy.deepcopy(sol); duplicate['placements'].append(copy.deepcopy(duplicate['placements'][0])); check('duplicate_id_rejected',duplicate,False)
    nonfinite=copy.deepcopy(sol); nonfinite['placements'][0]['x_m']=float('nan')
    r=verify(data,items,nonfinite,digest)
    cases.append({'case':'NaN_rejected','expected_acceptance':False,'accepted':r['valid'],'assertion_passed':not r['valid'],
        'errors':r['errors'],'mutation':'first placement x_m=float(nan); not serialized as valid numeric input'})
    boundary=copy.deepcopy(sol); boundary['placements'][0]['z_m']=3.15
    check('top_clearance_rejected',boundary,False)
    objective=copy.deepcopy(sol); objective['objective']['total_cost_CNY']=0
    check('objective_recomputed_from_raw',objective,False)
    payload=copy.deepcopy(sol)
    altered=copy.deepcopy(data); altered['vehicles'][0]['payload_kg']=359
    r=verify(altered,items,payload,None)
    cases.append({'case':'payload_360_exceeds_359','expected_acceptance':False,'accepted':r['valid'],
        'assertion_passed':not r['valid'],'errors':r['errors'],'parameter_variant':{'payload_kg':359}})
    return {'all_assertions_passed':all(c['assertion_passed'] for c in cases),'cases':cases,
        'claim_limit':'Author self-check only; controlled rejection cases do not establish general checker correctness or independent acceptance.'}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input',required=True); p.add_argument('--solution',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(); data,items,digest=read_input(a.input); sol=json.loads(Path(a.solution).read_text(encoding='utf-8-sig'))
    r=run(data,items,sol,digest); write_json(a.output,r)
    print(f"Actual test assertions: {sum(c['assertion_passed'] for c in r['cases'])}/{len(r['cases'])}")
    raise SystemExit(0 if r['all_assertions_passed'] else 1)
if __name__=='__main__': main()
