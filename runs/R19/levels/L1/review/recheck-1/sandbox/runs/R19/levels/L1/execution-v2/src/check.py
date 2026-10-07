"""Independent sweep of exported boxes. Does not import packing feasibility.
Full support and local vertical stress are checked by planar cell partition.
"""
import math,itertools,re
from contracts import validate_config,finite_number
import numpy as np
TOL=1e-7

def _physical_check_truck(tr,cfg):
    boxes=tr['items'];v=tr['vehicle'];types={c['id']:c for c in cfg['cargo']};errors=[];maxstress=0.;minclear=float('inf');support_contacts=[]
    def bad(rule,ids):errors.append({'rule':rule,'items':ids})
    if sum(i['weight'] for i in boxes)>v['payload']+TOL:bad('payload',[tr.get('truck_id')])
    for i in boxes:
      c=types[i['type_id']];ds=[i['dx'],i['dy'],i['dz']];coords=[i['x'],i['y'],i['z']]
      if not all(x>=-TOL for x in coords) or any(coords[k]+ds[k]>v['dims'][k]-(cfg['clearance'] if k==2 else 0)+TOL for k in range(3)):bad('boundary_clearance',[i['item_id']])
      if sorted(ds)!=sorted(c['dims']) or abs(i['weight']-c['weight'])>TOL:bad('dimensions_weight',[i['item_id']])
      if c['category']!='standard' and ds!=c['dims'] and not(c['category']=='fragile' and cfg.get('fragile_rotation') and ds==[c['dims'][1],c['dims'][0],c['dims'][2]]):bad('orientation',[i['item_id']])
      if c['category']=='fragile' and cfg.get('fragile_floor_only') and i['z']>TOL:bad('fragile_floor_only',[i['item_id']])
      if sorted(i.get('orientation',[]))!=[0,1,2] or any(abs(c['dims'][i['orientation'][k]]-ds[k])>TOL for k in range(3)):bad('orientation_label',[i['item_id']])
      minclear=min(minclear,v['dims'][2]-i['z']-i['dz'])
    # Independent pairwise positive-volume intersections.
    pos=np.array([[i[k] for k in ['x','y','z']] for i in boxes]);dim=np.array([[i[k] for k in ['dx','dy','dz']] for i in boxes])
    if len(boxes):
      hit=np.ones((len(boxes),len(boxes)),dtype=bool)
      for k in range(3):hit &= np.minimum((pos+dim)[:,k,None],(pos+dim)[None,:,k])-np.maximum(pos[:,k,None],pos[None,:,k])>TOL
      for a,b in zip(*np.nonzero(np.triu(hit,1))):bad('overlap',[boxes[a]['item_id'],boxes[b]['item_id']])
      if cfg.get('directional_center_each',True):
        for a in boxes:
          if a['category']!='directional':continue
          for b in boxes:
            if abs(a['z']+a['dz']-b['z'])>TOL:continue
            if min(a['x']+a['dx'],b['x']+b['dx'])-max(a['x'],b['x'])<=TOL or min(a['y']+a['dy'],b['y']+b['dy'])-max(a['y'],b['y'])<=TOL:continue
            cx,cy=b['x']+b['dx']/2,b['y']+b['dy']/2
            if not(a['x']-TOL<=cx<=a['x']+a['dx']+TOL and a['y']-TOL<=cy<=a['y']+a['dy']+TOL):bad('directional_contact_center',[a['item_id'],b['item_id']])
    # All exact x/y boundaries induce rectangular cells. Each column independently
    # proves no gaps and computes vertical forces + moments without redistribution.
    xs=sorted(set([i['x'] for i in boxes]+[i['x']+i['dx'] for i in boxes]));ys=sorted(set([i['y'] for i in boxes]+[i['y']+i['dy'] for i in boxes]));acc={i['item_id']:[0.,0.,0.,0.] for i in boxes}
    if len(xs)>1 and len(ys)>1:
      xa,ya=np.array(xs),np.array(ys);xc=(xa[:-1]+xa[1:])/2;yc=(ya[:-1]+ya[1:])/2;area=np.diff(xa)[:,None]*np.diff(ya)[None,:]/10000
      surface=np.zeros(area.shape);category=np.zeros(area.shape,dtype=int);pressure=np.zeros(area.shape)
      def region(i):return np.ix_(np.where((xc>=i['x'])&(xc<i['x']+i['dx']))[0],np.where((yc>=i['y'])&(yc<i['y']+i['dy']))[0])
      for i in sorted(boxes,key=lambda b:b['z']):
        s=region(i);h=surface[s];cats=category[s]
        if np.any(abs(h-i['z'])>TOL):bad('support_gap',[i['item_id']])
        if np.any(cats==2):bad('fragile_loaded',[i['item_id']])
        if i['category']=='fragile' and i['z']>TOL and np.any(cats!=1):bad('fragile_support',[i['item_id']])
        surface[s]=i['z']+i['dz'];category[s]={'standard':1,'fragile':2,'directional':3}[i['category']]
      for i in sorted(boxes,key=lambda b:b['z'],reverse=True):
        s=region(i);stress=pressure[s];ar=area[s];xmesh=np.broadcast_to(xc[:,None],area.shape)[s];ymesh=np.broadcast_to(yc[None,:],area.shape)[s]
        mxstress=float(stress.max());maxstress=max(maxstress,mxstress)
        if mxstress>cfg['bearing']+TOL:bad('cumulative_bearing',[i['item_id']])
        acc[i['item_id']]=[float(np.sum(stress*ar)),float(np.sum(stress*ar*xmesh)),float(np.sum(stress*ar*ymesh)),float(ar[stress>0].sum())]
        pressure[s]+=i['weight']/(i['dx']*i['dy']/10000)
    for i in boxes:
      load,mx,my,contact=acc[i['item_id']]
      if load>0:
        cx,cy=mx/load,my/load
        if not(i['x']-TOL<=cx<=i['x']+i['dx']+TOL and i['y']-TOL<=cy<=i['y']+i['dy']+TOL):bad('combined_center_of_mass',[i['item_id']])
        support_contacts.append({'item_id':i['item_id'],'upper_load_kg':load,'contact_area_m2':contact,'mean_pressure':load/contact,'top_area_mean_pressure':load/(i['dx']*i['dy']/10000),'resultant_x':cx,'resultant_y':cy})
    # Deduplicate cell-level failures while retaining involved IDs.
    unique={(e['rule'],tuple(e['items'])):e for e in errors}
    return {'valid':not unique,'errors':list(unique.values()),'max_local_pressure_kg_m2':maxstress,'min_top_clearance_cm':minclear,'support_contacts':support_contacts}

def _invalid(rule, detail=None):
    error={'rule':rule}
    if detail is not None:error['detail']=detail
    return {'valid':False,'errors':[error],'trucks':[]}


def check_truck(tr,cfg):
    """Bind all physical branches to authoritative scenario/source metadata.

    Contradictory output metadata is rejected, then known valid geometry is
    audited using the source category/weight/vehicle; no input is mutated.
    """
    try:validate_config(cfg)
    except ValueError as e:return _invalid('invalid_source_config',str(e))
    errors=[]
    def bad(rule,ids=None):errors.append({'rule':rule,'items':ids or []})
    if not isinstance(tr,dict) or not isinstance(tr.get('items'),list):return _invalid('invalid_truck_schema')
    vid=tr.get('vehicle_type');vehicles={v['id']:v for v in cfg['vehicles']}
    if not isinstance(vid,str) or vid not in vehicles:return _invalid('unknown_vehicle_type')
    v=vehicles[vid];export=tr.get('vehicle')
    if not isinstance(export,dict) or any(export.get(k)!=v[k] for k in ['id','dims','payload','cost']):bad('vehicle_source_mismatch',[tr.get('truck_id')])
    types={c['id']:c for c in cfg['cargo']};boxes=[]
    for exported in tr['items']:
        if not isinstance(exported,dict):bad('invalid_item_schema');continue
        i=dict(exported);iid=i.get('item_id');tid=i.get('type_id')
        if not isinstance(tid,str) or tid not in types:bad('unknown_cargo_type',[str(iid)]);continue
        c=types[tid];match=re.fullmatch(r'(G[1-5])-(\d{4,})',iid) if isinstance(iid,str) else None
        if not match or match[1]!=tid or len(match[2])>max(4,len(str(c['quantity']))) or not(1<=int(match[2])<=c['quantity']) or iid!=f'{tid}-{int(match[2]):04d}':bad('item_source_identity',[str(iid)])
        if not isinstance(iid,str):continue
        if i.get('category')!=c['category']:bad('category_source_mismatch',[iid])
        if not finite_number(i.get('weight')) or abs(i['weight']-c['weight'])>TOL:bad('weight_source_mismatch',[iid])
        if 'truck_id' in i and i['truck_id']!=tr.get('truck_id'):bad('truck_assignment_mismatch',[iid])
        if any(not finite_number(i.get(k)) for k in ['x','y','z','dx','dy','dz']) or any(i[k]<=0 for k in ['dx','dy','dz']):bad('nonfinite_or_invalid_geometry',[iid]);continue
        ori=i.get('orientation')
        if not isinstance(ori,list) or len(ori)!=3 or any(type(x)!=int for x in ori) or sorted(ori)!=[0,1,2]:
            bad('orientation_label',[iid]);i['orientation']=[0,1,2]
        # Output category and weight can never control support, centroid, stress
        # or payload. Preserve geometry so the physical counterexample is seen.
        i['category']=c['category'];i['weight']=c['weight'];boxes.append(i)
    report=_physical_check_truck({**tr,'vehicle':v,'items':boxes},cfg)
    report['errors']=errors+report['errors'];report['valid']=not report['errors']
    return report


def check_fleet(fleet,cfg,complete=True):
    try:validate_config(cfg)
    except ValueError as e:return _invalid('invalid_source_config',str(e))
    if not isinstance(fleet,list) or not isinstance(complete,bool):return _invalid('invalid_fleet_schema')
    errs=[];reports=[];counts={c['id']:0 for c in cfg['cargo']};ids=[];truck_ids=[]
    for t in fleet:
        if isinstance(t,dict):
            truck_ids.append(t.get('truck_id'))
            for i in t.get('items',[]) if isinstance(t.get('items'),list) else []:
                if not isinstance(i,dict):continue
                iid=i.get('item_id');tid=i.get('type_id')
                if isinstance(iid,str):ids.append(iid)
                if isinstance(tid,str) and tid in counts:counts[tid]+=1
        r=check_truck(t,cfg);reports.append({'truck_id':t.get('truck_id') if isinstance(t,dict) else None,**r});errs+=r['errors']
    if len(ids)!=len(set(ids)):errs.append({'rule':'duplicate_ids'})
    if any(not isinstance(i,str) or not i for i in truck_ids) or len(set(str(i) for i in truck_ids))!=len(truck_ids):errs.append({'rule':'truck_identity'})
    for c in cfg['cargo']:
        n=counts[c['id']]
        if n>c['quantity'] or(complete and n!=c['quantity']):errs.append({'rule':'inventory_conservation','type':c['id'],'actual':n,'expected':c['quantity']})
    return {'valid':not errs,'complete':complete,'counts':counts,'errors':errs,'trucks':reports,'tolerance_cm':TOL,'source_contract':'original G1-G5 categories; scenario numeric fields; canonical physical metadata; revision F1','force_model':'vertical cell force transfer; own mass uniformly distributed, nonnegative reactions; no dynamic claim'}
