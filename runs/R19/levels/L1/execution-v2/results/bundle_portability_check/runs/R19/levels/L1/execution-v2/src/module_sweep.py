import argparse,json,time
from pathlib import Path
from solve import ROOT,fleet_module,stats
from check import check_fleet
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--config',type=Path,default=ROOT/'configs/base.json');a=p.parse_args()
    if a.out.exists() and any(a.out.iterdir()):raise ValueError('Use an empty/new output directory')
    a.out.mkdir(parents=True,exist_ok=True);cfg=json.loads(a.config.read_text(encoding='utf-8-sig'))
    for v in cfg['vehicles']:
      for k in range(6):
        tic=time.perf_counter();f=fleet_module(v,cfg,k);report=check_fleet(f,cfg,True);seconds=time.perf_counter()-tic
        d={'config':cfg,'fleet':f,'statistics':stats(f,cfg),'seconds':seconds,'check':report};(a.out/f'{v["id"]}_{k}.json').write_text(json.dumps(d,ensure_ascii=False),encoding='utf8');print(v['id'],k,report['valid'],len(f),seconds,flush=True)
