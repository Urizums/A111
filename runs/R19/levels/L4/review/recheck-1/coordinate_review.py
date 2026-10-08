from pathlib import Path
from collections import Counter,defaultdict
from math import prod,isfinite
import csv,json,time
import numpy as np
from independent_checks import validate as frozen_validate
OUT=Path(__file__).resolve().parent;ROOT=Path(__file__).resolve().parents[6];E=ROOT/'runs/R19/levels/L4/execution'
BASE=json.loads((OUT/'consumer/data/raw_rebuilt.json').read_text(encoding='utf-8'))
def close(a,b):return abs(float(a)-float(b))<=1e-6*max(1,abs(float(a)))
def check(path,data=None,single=False,run_frozen=False):
    data=data or BASE;cfg=json.loads((path/'summary.json').read_text(encoding='utf-8'))['config']; eps=1e-7
    rows=list(csv.DictReader((path/'placements.csv').open(encoding='utf-8-sig',newline='')))
    cargo={g['id']:g for g in data['cargo']};vehicles={v['id']:v for v in data['vehicles']};groups=defaultdict(list);errors=[]
    ids=[r['item_id'] for r in rows];count=Counter(r['cargo_type'] for r in rows)
    if len(ids)!=len(set(ids)):errors.append('duplicate_id')
    for g in cargo:
        if count[g]>cargo[g]['quantity'] or (not single and count[g]!=cargo[g]['quantity']):errors.append('inventory:'+g)
    for row in rows:
        g=cargo[row['cargo_type']];dims=[float(row[k]) for k in ['l','w','h']]
        if any(not isfinite(float(row[k])) for k in ['x','y','z','l','w','h']):errors.append('nonfinite')
        if sorted(dims)!=sorted(g['dims']):errors.append('source_dimension')
        if g['class']=='oriented' and dims!=g['dims']:errors.append('fixed_orientation')
        if g['class']=='fragile' and cfg.get('fragile_orientation')=='original_height' and dims[2]!=g['dims'][2]:errors.append('fragile_height')
        ori=row['orientation']
        if sorted(ori)!=['H','L','W'] or [g['dims']['LWH'.index(c)] for c in ori]!=dims:errors.append('orientation_code')
        if not row['item_id'].startswith(g['id']+'-') or not 1<=int(row['item_id'].split('-')[-1])<=g['quantity']:errors.append('id_source_range')
        groups[row['truck_id']].append(row)
    stats=[];loads=[];chains=[];frozen=[];comparisons=[]
    for tid,rs in groups.items():
        typ=rs[0]['vehicle_type'];v=vehicles[typ];n=len(rs)
        if set(r['vehicle_type'] for r in rs)!={typ}:errors.append('truck_type')
        a=np.array([[float(r[k]) for k in ['x','y','z','l','w','h']] for r in rs]); low=a[:,:3]; high=low+a[:,3:]
        if (low< -eps).any() or (a[:,3:]<=0).any():errors.append('low_or_positive_size')
        if (high>np.array([v['dims'][0],v['dims'][1],v['dims'][2]-cfg['gap_cm']])+eps).any():errors.append('boundary_gap')
        overlap=np.all(np.minimum(high[:,None,:],high[None,:,:])-np.maximum(low[:,None,:],low[None,:,:])>eps,axis=2)
        if np.triu(overlap,1).any():errors.append('positive_overlap')
        parents={};mass=np.array([cargo[r['cargo_type']]['mass'] for r in rs]);ext=np.zeros(n)
        for i,r in enumerate(rs):
            if abs(low[i,2])<=eps:
                if r['support_ids']!='FLOOR':errors.append('floor_metadata')
                continue
            support=np.flatnonzero((abs(high[:,2]-low[i,2])<=eps)&(low[:,0]<=low[i,0]+eps)&(low[:,1]<=low[i,1]+eps)&(high[:,0]>=high[i,0]-eps)&(high[:,1]>=high[i,1]-eps))
            if len(support)!=1:errors.append('single_full_support');continue
            j=int(support[0]);parents[i]=j
            if r['support_ids']!=rs[j]['item_id']:errors.append('parent_metadata')
            if cargo[rs[j]['cargo_type']]['class']=='fragile':errors.append('fragile_top')
            if cargo[r['cargo_type']]['class']=='fragile' and cargo[rs[j]['cargo_type']]['class']!='standard':errors.append('fragile_base')
            center=(low[i,:2]+high[i,:2])/2
            if cargo[rs[j]['cargo_type']]['class']=='oriented' and (any(center<low[j,:2]-eps) or any(center>high[j,:2]+eps)):errors.append('oriented_center')
        for i in sorted(range(n),key=lambda j:low[j,2],reverse=True):
            if i in parents:
                j=parents[i];ext[j]+=mass[i]+ext[i]
                if mass[i]+ext[i]>cfg['pressure_kg_m2']*a[i,3]*a[i,4]/10000+eps:errors.append('contact_pressure')
        for i,r in enumerate(rs):
            limit=cfg['pressure_kg_m2']*a[i,3]*a[i,4]/10000
            if ext[i]>limit+eps:errors.append('cumulative_pressure')
            loads.append({'id':r['item_id'],'truck':tid,'external':float(ext[i]),'limit':float(limit)})
        if mass.sum()>v['capacity']+eps:errors.append('weight')
        weight=float(mass.sum());volume=float(np.prod(a[:,3:],axis=1).sum())
        stats.append({'truck_id':tid,'vehicle_type':typ,'items':n,'mass_kg':weight,'volume_cm3':volume,'UV':volume/prod(v['dims']),'UW':weight/v['capacity'],'cost':v['cost']})
        if run_frozen and tid==max(groups,key=lambda k:len(groups[k])):
            cat={g['id']:{'dims':g['dims'],'class':('directed' if g['class']=='oriented' else g['class']),'mass':g['mass'],'quantity':g['quantity']} for g in data['cargo']}
            its=[{'id':r['item_id'],'type':r['cargo_type'],'mass':cargo[r['cargo_type']]['mass'],**{k:float(r[k]) for k in ['x','y','z','l','w','h']}} for r in rs]
            tv={'L':v['dims'][0],'W':v['dims'][1],'H':v['dims'][2],'capacity':v['capacity'],'cost':v['cost']}
            fr=frozen_validate(tv,its,cat,pressure_basis='contact');frozen.append({'truck':tid,'items':n,'result':fr})
            if not fr['valid']:errors.append('frozen_checker')
        for i in range(n):
            if ext[i]==max(ext) and ext[i]>0:
                descendants=[]
                for j in range(n):
                    cur=j
                    while cur in parents:
                        cur=parents[cur]
                        if cur==i:descendants.append({'id':rs[j]['item_id'],'mass':float(mass[j])});break
                chains.append({'base':rs[i]['item_id'],'truck':tid,'external':float(ext[i]),'hand_sum_of_descendant_weights':sum(x['mass'] for x in descendants),'descendants':descendants})
    metrics={'truck_count':len(stats),'cost':sum(s['cost'] for s in stats),'volume_cm3':sum(s['volume_cm3'] for s in stats),'mass_kg':sum(s['mass_kg'] for s in stats)}
    metrics['UV']=metrics['volume_cm3']/sum(prod(vehicles[s['vehicle_type']]['dims']) for s in stats)
    metrics['UW']=metrics['mass_kg']/sum(vehicles[s['vehicle_type']]['capacity'] for s in stats)
    summary=json.loads((path/'summary.json').read_text(encoding='utf-8'))
    for k,v in metrics.items():
        comparisons.append({'field':k,'independent':v,'reported':summary.get(k),'match':close(v,summary[k])})
    reportedloads={r['item_id']:r for r in csv.DictReader((path/'support_loads.csv').open(encoding='utf-8-sig',newline=''))}
    for l in loads:
        r=reportedloads.get(l['id'])
        if r is None or not close(l['external'],r['external_load_kg']) or not close(l['limit'],r['load_limit_kg']):errors.append('reported_load_disagreement')
    return {'path':str(path.relative_to(ROOT)),'rows':len(rows),'single':single,'inventory':dict(count),'errors':sorted(set(errors)),
            'valid':not errors,'metrics':metrics,'trucks':stats,'summary_comparisons':comparisons,
            'all_summary_metrics_match':all(c['match'] for c in comparisons),'max_chains':chains,'frozen_representative_checks':frozen}

def main():
    start=time.perf_counter();results=[]
    selected=json.loads((E/'results/selected.json').read_text(encoding='utf-8'))
    for key,v in selected['scenarios'].items():
        r=check(E/v['root'],run_frozen=True);r['scenario']=key;results.append(r)
        print(key,r['valid'],r['metrics'],flush=True)
    for p in sorted((E/'results/selected_single').glob('T*/summary.json')):
        r=check(p.parent,single=True);results.append(r);print(p.parent.name,r['valid'],r['metrics'],flush=True)
    for folder in ['baseline_refined','classic_refined','improved_refined']:
        if not (E/'results'/folder).exists():continue
        for p in sorted((E/'results'/folder).glob('Q*_*/summary.json')):
            if 'single' in p.parent.name:continue
            r=check(p.parent);results.append(r)
    for p in sorted((E/'results/experiments').glob('*/summary.json')):
        data=json.loads((p.parent/'input.json').read_text(encoding='utf-8'))
        r=check(p.parent,data);results.append(r);print('experiment',p.parent.name,r['valid'],flush=True)
    out={'scope':'independent all-coordinate checks; all final, 3 formal refined methods, all17 parameter cases','results':results,
         'all_valid':all(r['valid'] for r in results),'all_summary_metrics_match':all(r['all_summary_metrics_match'] for r in results),'elapsed_seconds':time.perf_counter()-start}
    (OUT/'coordinate-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('COUNT',len(results),'ALL',out['all_valid'],out['all_summary_metrics_match'],'TIME',out['elapsed_seconds'])
if __name__=='__main__':main()
