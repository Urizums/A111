from independent_audit import raw_config,audit,OUT,EXEC
import json,time,sys
sys.path.insert(0,str(OUT/'sandbox/runs/R19/levels/L1/execution/src'))
from solve import pack,strategy_list,Truck,canonicalize
cfg=raw_config();tic=time.perf_counter();results={};pareto={}
for v in cfg['vehicles']:
    allrows=[]
    for k,strategy in enumerate(strategy_list()):
        tr=pack(v,cfg,{c['id']:c['quantity'] for c in cfg['cargo']},strategy)
        f=canonicalize([{'vehicle_type':v['id'],'vehicle':v,'items':tr.items}],cfg);d={'config':cfg,'fleet':f};r,_=audit(d,f'{v["id"]}-strategy{k}',False,cfg);allrows.append({'candidate':k,'solution':d,'own_audit':r})
    for order in [['G5','G1','G2','G4','G3'],['G1','G2','G5','G4','G3'],['G4','G1','G2','G5','G3'],['G2','G1','G5','G4','G3']]:
        tr=Truck(v,cfg);rem={c['id']:c['quantity'] for c in cfg['cargo']};serials=dict.fromkeys(rem,0)
        for cid in order:
            c=next(c for c in cfg['cargo'] if c['id']==cid)
            while rem[cid]>0:
                pos=tr.find(c,v['dims'][2]-cfg['clearance'],'compact')
                if pos is None:break
                rem[cid]-=1;serials[cid]+=1;tr.add(c,pos,serials[cid])
        f=canonicalize([{'vehicle_type':v['id'],'vehicle':v,'items':tr.items}],cfg);d={'config':cfg,'fleet':f};r,_=audit(d,f'{v["id"]}-anchor-{order}',False,cfg);allrows.append({'candidate':','.join(order),'solution':d,'own_audit':r})
    results[v['id']]=allrows
    nondominated=[]
    for row in allrows:
        x=row['own_audit']['metrics'];dominated=False
        for other in allrows:
            y=other['own_audit']['metrics']
            if y['volume_cm3']>=x['volume_cm3'] and y['weight_kg']>=x['weight_kg'] and (y['volume_cm3']>x['volume_cm3'] or y['weight_kg']>x['weight_kg']):dominated=True;break
        if not dominated and x not in nondominated:nondominated.append(x)
    pareto[v['id']]=nondominated
frozen=json.loads((EXEC/'results/final/single_pareto.json').read_text(encoding='utf-8'))['solutions'];matches={v:sorted((r['volume_cm3'],r['weight_kg']) for r in ps)==sorted((p['statistics']['volume_cm3'],p['statistics']['weight_kg']) for p in frozen[v]) for v,ps in pareto.items()}
result={'seconds':time.perf_counter()-tic,'all_candidates_valid':all(r['own_audit']['valid'] for rows in results.values() for r in rows),'candidate_count':sum(map(len,results.values())),'own_nondominated_metrics':pareto,'frozen_pareto_matches':matches,'candidates':results,'scope':'copied unmodified original finite32 single candidate generation; nondominance recomputed independently, no complete original Pareto claim'}
(OUT/'independent-single-pool-replay.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8');print(json.dumps({k:result[k] for k in ['seconds','all_candidates_valid','candidate_count','own_nondominated_metrics','frozen_pareto_matches']},ensure_ascii=False,indent=2))
