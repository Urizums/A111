from pathlib import Path
import json,subprocess,time,copy,sys
OUT=Path(__file__).resolve().parent;C=OUT/'consumer'
def main():
    base=json.loads((C/'data/raw_rebuilt.json').read_text(encoding='utf-8'));cfg=json.loads((C/'configs/experiments.json').read_text(encoding='utf-8'))
    variant=copy.deepcopy(base)
    for g in variant['cargo']:g['quantity']=round(g['quantity']*.25)
    (C/'data/reviewer_variant750.json').write_text(json.dumps(variant,ensure_ascii=False,indent=2),encoding='utf-8')
    calls=[]
    for name,data in [('variant750','data/reviewer_variant750.json')]:
        args=['py','-3.12','-X','utf8','-B','code/solve.py','--data',data,'--config','configs/experiments.json','--out',f'reviewer_{name}','--method','maxrects']
        start=time.perf_counter();p=subprocess.run(args,cwd=C,capture_output=True,text=True,encoding='utf-8')
        calls.append({'name':name,'command':args,'elapsed_seconds':time.perf_counter()-start,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'ongoing':False})
    impossible=copy.deepcopy(base)
    for g in impossible['cargo']:g['dims']=[1000,1000,1000]
    (C/'data/reviewer_impossible.json').write_text(json.dumps(impossible,ensure_ascii=False,indent=2),encoding='utf-8')
    args=['py','-3.12','-X','utf8','-B','code/solve.py','--data','data/reviewer_impossible.json','--config','configs/experiments.json','--out','reviewer_impossible','--method','maxrects']
    start=time.perf_counter();p=subprocess.run(args,cwd=C,capture_output=True,text=True,encoding='utf-8')
    calls.append({'name':'cannot_fit_any_vehicle','command':args,'elapsed_seconds':time.perf_counter()-start,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'ongoing':False,
                  'interpretation':'Expected failure control; cannot produce successful full scenario'})
    (OUT/'secondary-cli-receipts.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2),encoding='utf-8')
    sys.path.insert(0,str(C/'code'))
    from experiments import experiment
    params=[]
    for name in ['base','fragile_original_height']:
        c=copy.deepcopy(cfg)
        if name=='fragile_original_height':c['fragile_orientation']='original_height'
        r=experiment(base,c,OUT/'reproduced_parameters',name);params.append(r)
    receipt={'cli_calls':calls,'parameter_calls':params,'scope':'actual changed-input CLI, actual infeasible input failure, base/fragile orientation parameter reruns'}
    (OUT/'secondary-runs.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,default=lambda x:x.item()),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False,indent=2,default=lambda x:x.item()))
if __name__=='__main__':main()
