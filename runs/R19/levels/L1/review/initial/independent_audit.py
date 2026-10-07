"""Independent raw-OOXML data and full placement audit. Imports no author code.
Review-plan.md frozen formula/constraint implementation; no solving.
"""
from pathlib import Path
import json, zipfile, re, xml.etree.ElementTree as ET, itertools, collections, math, csv, time
import numpy as np
ROOT=Path(__file__).resolve().parents[6]
OUT=Path(__file__).resolve().parent
EXEC=ROOT/'runs/R19/levels/L1/execution'
def raw_config():
    with zipfile.ZipFile(ROOT/'runs/R19/inputs/raw/附件1.docx') as z:
        xml=ET.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    body=xml.find('w:body',ns); pp=[''.join(e.text or '' for e in p.findall('.//w:t',ns)) for p in body.findall('w:p',ns)]
    cfg={'vehicles':[],'cargo':[],'clearance':3,'bearing':500,'fragile_rotation':False,'directional_center_each':True,'fragile_floor_only':False,'version':'3.0'}
    for i,dimpos in enumerate([3,7],1):
        cfg['vehicles'].append({'id':f'T{i}','dims':list(map(float,re.findall(r'(\d+)\s*cm',pp[dimpos]))),'payload':float(re.search(r'(\d+)kg',pp[dimpos+1])[1]),'cost':float(re.search(r'(\d+)\s*元',pp[dimpos+2])[1])})
    tab=body.find('w:tbl',ns)
    for tr in tab.findall('w:tr',ns)[1:]:
        vals=[''.join(e.text or '' for e in tc.findall('.//w:t',ns)) for tc in tr.findall('w:tc',ns)]
        cfg['cargo'].append({'id':vals[0],'category':{'标准件':'standard','易碎件':'fragile','定向件':'directional'}[vals[1]],'dims':list(map(float,vals[2].split('×'))),'weight':float(vals[3]),'quantity':int(vals[4])})
    return cfg
def geomtol(*values): return 1e-6+1e-10*max([abs(float(v)) for v in values]+[0])
def audit(d,name,complete=True,config=None):
    cfg=raw_config() if config is None else config
    cs={c['id']:c for c in cfg['cargo']};vs={v['id']:v for v in cfg['vehicles']}
    issues=[]; nissues=0
    def bad(code,**kw):
        nonlocal nissues
        nissues+=1
        if len(issues)<50: issues.append({'code':code,**kw})
    if d.get('config') is not None and d['config']!=cfg: bad('input_config_mismatch')
    counts=collections.Counter();ids=[];trucks=[];records=[];totalV=0.;totalW=0.;totalCost=0.;capV=0.;capW=0.
    for tr in d['fleet']:
        v=vs.get(tr['vehicle_type'])
        if v is None:bad('unknown_vehicle',truck=tr.get('truck_id'));continue
        if tr.get('vehicle')!=v:bad('vehicle_field_mismatch',truck=tr.get('truck_id'))
        tid=tr['truck_id']; a=tr['items']; n=len(a); tcounts=collections.Counter(i['type_id'] for i in a)
        if not n:bad('empty_active_truck',truck=tid);continue
        pos=np.array([[i[k] for k in ['x','y','z']] for i in a],dtype=float)
        dim=np.array([[i[k] for k in ['dx','dy','dz']] for i in a],dtype=float); tops=pos+dim
        if not np.isfinite(pos).all() or not np.isfinite(dim).all():bad('nonfinite_geometry',truck=tid);continue
        weights=np.array([cs[i['type_id']]['weight'] for i in a]);vols=np.array([math.prod(cs[i['type_id']]['dims']) for i in a]); cats=[cs[i['type_id']]['category'] for i in a]
        for j,i in enumerate(a):
            c=cs[i['type_id']];counts[c['id']]+=1;ids.append(i['item_id'])
            if i['weight']!=c['weight'] or i['category']!=c['category']:bad('item_source_field_mismatch',item=i['item_id'])
            ori=i['orientation']
            if sorted(ori)!=[0,1,2] or tuple(dim[j])!=tuple(c['dims'][k] for k in ori):bad('orientation_dimensions',item=i['item_id'])
            if c['category']=='directional' and ori!=[0,1,2]:bad('directional_orientation',item=i['item_id'])
            if c['category']=='fragile':
                allowed=[tuple(c['dims'])]
                if cfg.get('fragile_rotation'): allowed.append(tuple([c['dims'][1],c['dims'][0],c['dims'][2]]))
                if tuple(dim[j]) not in allowed:bad('fragile_model_orientation',item=i['item_id'])
                if cfg.get('fragile_floor_only') and abs(pos[j,2])>geomtol(pos[j,2]):bad('fragile_floor_model',item=i['item_id'])
            limits=np.array(v['dims'])-[0,0,cfg['clearance']]
            if any(pos[j]<-geomtol(*pos[j])) or any(tops[j]>limits+geomtol(*tops[j],*limits)):bad('boundary_clearance',item=i['item_id'])
        mass=float(weights.sum());vv=float(vols.sum())
        if mass>v['payload']+1e-6+1e-10*mass:bad('payload',truck=tid,mass=mass)
        # All pairs independently; exact contacts accepted, strict positive overlap rejected.
        ij=np.triu_indices(n,1); overlap=np.minimum(tops[ij[0]],tops[ij[1]])-np.maximum(pos[ij[0]],pos[ij[1]])
        for p in np.flatnonzero(np.all(overlap>geomtol(*v['dims']),axis=1)):
            bad('collision',items=[a[ij[0][p]]['item_id'],a[ij[1][p]]['item_id']])
        # Direct contact adjacency for directional support rules, independent of author tags.
        for upper in range(n):
            if pos[upper,2]<=geomtol(pos[upper,2]):continue
            below=np.flatnonzero((np.abs(tops[:,2]-pos[upper,2])<=geomtol(pos[upper,2])) & (np.minimum(tops[:,0],tops[upper,0])-np.maximum(pos[:,0],pos[upper,0])>geomtol(*v['dims'])) & (np.minimum(tops[:,1],tops[upper,1])-np.maximum(pos[:,1],pos[upper,1])>geomtol(*v['dims'])))
            center=pos[upper,:2]+dim[upper,:2]/2
            for lower in below:
                if cats[lower]=='directional' and cfg.get('directional_center_each',True) and (any(center<pos[lower,:2]-geomtol(*center)) or any(center>tops[lower,:2]+geomtol(*center))):bad('direct_directional_centroid',upper=a[upper]['item_id'],lower=a[lower]['item_id'],center=center.tolist())
        # Atomic xy rectangles using every actual edge, not author's grid or checker.
        xs=np.unique(np.r_[pos[:,0],tops[:,0]]);ys=np.unique(np.r_[pos[:,1],tops[:,1]])
        cmx=(xs[:-1]+xs[1:])/2;cmy=(ys[:-1]+ys[1:])/2
        gx,gy=np.meshgrid(cmx,cmy,indexing='ij');areas=np.outer(np.diff(xs),np.diff(ys));gf=gx.ravel();hf=gy.ravel();af=areas.ravel()
        cover=(gf[None,:]>pos[:,0,None])&(gf[None,:]<tops[:,0,None])&(hf[None,:]>pos[:,1,None])&(hf[None,:]<tops[:,1,None])
        maxpress=np.zeros(n);extforce=np.zeros(n);mx=np.zeros(n);my=np.zeros(n);loadedarea=np.zeros(n)
        floorforce=0.; floormx=0.;floormy=0.;raycount=0
        for cell in np.flatnonzero(cover.any(axis=0)):
            active=np.flatnonzero(cover[:,cell]);active=active[np.argsort(pos[active,2])];raycount+=1
            if pos[active[0],2]>geomtol(pos[active[0],2]):bad('bottom_no_support',truck=tid,item=a[active[0]]['item_id'],xy=[float(gf[cell]),float(hf[cell])])
            if sum(cats[j]=='fragile' for j in active)>1:bad('fragile_vertical_stack',truck=tid)
            for low,up in zip(active[:-1],active[1:]):
                if abs(tops[low,2]-pos[up,2])>geomtol(tops[low,2],pos[up,2]):bad('support_gap',lower=a[low]['item_id'],upper=a[up]['item_id'])
                if cats[low]=='fragile':bad('fragile_loaded',lower=a[low]['item_id'],upper=a[up]['item_id'])
                if cats[up]=='fragile' and cats[low]!='standard':bad('fragile_nonstandard_support',lower=a[low]['item_id'],upper=a[up]['item_id'])
            press=0.
            for j in active[::-1]:
                maxpress[j]=max(maxpress[j],press)
                f=press*af[cell]/10000;extforce[j]+=f;mx[j]+=f*gf[cell];my[j]+=f*hf[cell]
                if press>1e-10:loadedarea[j]+=af[cell]/10000
                press+=weights[j]*10000/(dim[j,0]*dim[j,1])
            ff=press*af[cell]/10000;floorforce+=ff;floormx+=ff*gf[cell];floormy+=ff*hf[cell]
        if abs(floorforce-mass)>1e-6+mass*1e-10:bad('force_conservation',truck=tid,floor=floorforce,raw_mass=mass)
        expmx=float((weights*(pos[:,0]+dim[:,0]/2)).sum());expmy=float((weights*(pos[:,1]+dim[:,1]/2)).sum())
        if abs(floormx-expmx)>1e-5+1e-10*expmx or abs(floormy-expmy)>1e-5+1e-10*expmy:bad('moment_conservation',truck=tid)
        for j in range(n):
            if maxpress[j]>cfg['bearing']+1e-6+1e-10*cfg['bearing']:bad('cumulative_local_pressure',item=a[j]['item_id'],pressure=float(maxpress[j]))
            if extforce[j]>1e-9:
                cc=[mx[j]/extforce[j],my[j]/extforce[j]]
                if any(np.array(cc)<pos[j,:2]-geomtol(*cc)) or any(np.array(cc)>tops[j,:2]+geomtol(*cc)):bad('cumulative_centroid',item=a[j]['item_id'])
            else:cc=[None,None]
            records.append({'task':name,'truck_id':tid,'item_id':a[j]['item_id'],'external_kg':float(extforce[j]),'max_local_kg_m2':float(maxpress[j]),'loaded_contact_m2':float(loadedarea[j]),'contact_mean_kg_m2':float(extforce[j]/loadedarea[j]) if loadedarea[j]>0 else 0.,'whole_top_mean_kg_m2':float(extforce[j]*10000/(dim[j,0]*dim[j,1])),'resultant_x':cc[0],'resultant_y':cc[1]})
        minclear=float(v['dims'][2]-tops[:,2].max())
        trucks.append({'truck_id':tid,'vehicle_type':v['id'],'counts':dict(tcounts),'volume_cm3':vv,'weight_kg':mass,'volume_rate':vv/math.prod(v['dims']),'load_rate':mass/v['payload'],'minimum_top_clearance_cm':minclear,'max_local_pressure_kg_m2':float(maxpress.max()),'atomic_cells':raycount,'force_error_kg':floorforce-mass,'moment_error_kg_cm':[floormx-expmx,floormy-expmy]})
        totalV+=vv;totalW+=mass;totalCost+=v['cost'];capV+=math.prod(v['dims']);capW+=v['payload']
    if len(set(t['truck_id'] for t in d['fleet']))!=len(d['fleet']):bad('duplicate_truck_id')
    if len(set(ids))!=len(ids):bad('duplicate_item_ids')
    expected={f'{c["id"]}-{k:04d}' for c in cfg['cargo'] for k in range(1,c['quantity']+1)}
    if not set(ids)<=expected:bad('unknown_item_ids',examples=sorted(set(ids)-expected)[:10])
    if complete and set(ids)!=expected:bad('missing_or_extra_items',missing=len(expected-set(ids)),extra=len(set(ids)-expected))
    for cid,c in cs.items():
        if counts[cid]>c['quantity'] or (complete and counts[cid]!=c['quantity']):bad('inventory',type=cid,count=counts[cid],expected=c['quantity'])
    metrics={'vehicles':len(d['fleet']),'cost':totalCost,'volume_cm3':totalV,'weight_kg':totalW,'volume_rate':totalV/capV if capV else 0.,'load_rate':totalW/capW if capW else 0.,'vehicle_counts':dict(collections.Counter(t['vehicle_type'] for t in d['fleet']))}
    discrepancies={}
    for k,val in metrics.items():
        ref=d.get('statistics',{}).get(k)
        if isinstance(val,dict):
            if ref is not None and any(ref.get(x,0)!=val.get(x,0) for x in set(val)|set(ref)):discrepancies[k]={'reported':ref,'actual':val}
        elif ref is not None and abs(val-ref)>1e-9+abs(val)*1e-10:discrepancies[k]={'reported':ref,'actual':val}
    if discrepancies:bad('summary_metrics_mismatch',discrepancies=discrepancies)
    return {'task':name,'complete':complete,'valid':nissues==0,'violation_count':nissues,'violations':issues,'metrics':metrics,'counts':dict(counts),'trucks':trucks,'max_local_pressure_kg_m2':max([t['max_local_pressure_kg_m2'] for t in trucks]+[0]),'minimum_top_clearance_cm':min([t['minimum_top_clearance_cm'] for t in trucks]+[float('inf')])},records
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--dir',type=Path,default=EXEC/'results/final');ap.add_argument('--prefix',default='frozen-final');aa=ap.parse_args()
    names=['fixed_T1','fixed_T2','mixed_count','mixed_cost','single_T1_0','single_T1_1','single_T2_0'];reports=[];records=[];tic=time.perf_counter()
    for name in names:
        d=json.loads((aa.dir/f'{name}.json').read_text(encoding='utf-8'));r,rr=audit(d,name,not name.startswith('single'));reports.append(r);records+=rr
    with (OUT/f'{aa.prefix}-loads.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
    result={'independence':'original raw OOXML parsed here; no author check/solver imported','seconds':time.perf_counter()-tic,'reports':reports}
    (OUT/f'{aa.prefix}-independent-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'seconds':result['seconds'],'reports':[{k:r[k] for k in ['task','valid','violation_count','metrics','max_local_pressure_kg_m2','minimum_top_clearance_cm']} for r in reports]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
