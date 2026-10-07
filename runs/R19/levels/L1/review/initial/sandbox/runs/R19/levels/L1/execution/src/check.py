"""Independent sweep of exported boxes. Does not import packing feasibility.
Full support and local vertical stress are checked by planar cell partition.
"""
import math,itertools
import numpy as np
TOL=1e-7

def check_truck(tr,cfg):
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

def check_fleet(fleet,cfg,complete=True):
    ids=[i['item_id'] for t in fleet for i in t['items']];errs=[];reports=[];counts={c['id']:sum(i['type_id']==c['id'] for t in fleet for i in t['items']) for c in cfg['cargo']}
    if len(ids)!=len(set(ids)):errs.append({'rule':'duplicate_ids'})
    for c in cfg['cargo']:
      n=counts[c['id']]
      if n>c['quantity'] or(complete and n!=c['quantity']):errs.append({'rule':'inventory_conservation','type':c['id'],'actual':n,'expected':c['quantity']})
    for t in fleet:
      r=check_truck(t,cfg);reports.append({'truck_id':t.get('truck_id'),**r});errs+=r['errors']
    return {'valid':not errs,'complete':complete,'counts':counts,'errors':errs,'trucks':reports,'tolerance_cm':TOL,'force_model':'vertical cell force transfer; own mass uniformly distributed, nonnegative reactions; no dynamic claim'}
