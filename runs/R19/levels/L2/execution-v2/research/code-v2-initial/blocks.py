"""Finite certified protected blocks; constructor independent of validate.py."""
import math,json,time
import numpy as np
CACHE={};CERTIFICATES=[]
def catalog(types,v,config,orientations):
 key=json.dumps([types,v,config.get('pressure',500),config.get('fragile_fixed',False)],sort_keys=True)
 if key in CACHE:return CACHE[key]
 start=time.perf_counter();out=[];seen=set();failed=[]
 from validate import validate
 lookup={t['cargo_type']:t for t in types};ids={t['cargo_type']:i for i,t in enumerate(types)}
 H=v['dims'][2]-v['clearance_mm'];pressure=config.get('pressure',500)
 def part(t,x,y,z,ds,ori):return {'cargo_type':t,'x_mm':x,'y_mm':y,'z_mm':z,'dx_mm':ds[0],'dy_mm':ds[1],'dz_mm':ds[2],'orientation_id':ori}
 def add(parts,tag):
  if not parts:return
  bw=max(p['x_mm']+p['dx_mm'] for p in parts);bh=max(p['y_mm']+p['dy_mm'] for p in parts)
  if bw>v['dims'][0] or bh>v['dims'][1] or max(p['z_mm']+p['dz_mm'] for p in parts)>H:return
  ident=json.dumps(parts,sort_keys=True)
  if ident in seen:return
  seen.add(ident);items=[];rows=[];counts=[0]*len(types)
  for i,p in enumerate(parts):
   t=lookup[p['cargo_type']];iid='B'+str(i);counts[ids[t['cargo_type']]]+=1
   items.append({'item_id':iid,'cargo_type':t['cargo_type'],'category':t['category'],'canonical_l_mm':t['dims'][0],'canonical_w_mm':t['dims'][1],'canonical_h_mm':t['dims'][2],'weight_kg':t['weight']})
   rows.append({'vehicle_id':'B','vehicle_type':v['type_id'],'item_id':iid,**p})
  z=validate(rows,items,[v],True,pressure,config.get('fragile_fixed',False))
  if not z['valid']:failed.append({'tag':tag,'counts':counts,'errors':z['errors']});return
  out.append({'width':bw,'depth':bh,'counts':counts,'mass':sum(lookup[p['cargo_type']]['weight'] for p in parts),'volume':sum(p['dx_mm']*p['dy_mm']*p['dz_mm'] for p in parts),'placements':parts,'tag':tag})
 frag=next((t for t in types if t['category']=='易碎件'),None)
 if frag and not config.get('fragile_floor',False):
  for std in [t for t in types if t['category']=='标准件']:
   for (sx,sy,sz),so in orientations(std):
    for (fx,fy,fz),fo in orientations(frag,config.get('fragile_fixed',False)):
     # Minimal enclosing grids and one-cell larger alternatives; 1 and 2 fragile rows.
     for nf_x,nf_y in [(1,1),(2,1),(1,2)]:
      mx=math.ceil(nf_x*fx/sx);my=math.ceil(nf_y*fy/sy)
      for nx,ny in [(mx,my),(mx+1,my),(mx,my+1)]:
       if nx>6 or ny>6:continue
       cap=(H-fz)//sz
       for k in sorted(set([1,max(1,cap//2),cap])):
        if k<1:continue
        ps=[part(std['cargo_type'],ix*sx,iy*sy,iz*sz,(sx,sy,sz),so) for iz in range(k) for ix in range(nx) for iy in range(ny)]
        ps += [part(frag['cargo_type'],ix*fx,iy*fy,k*sz,(fx,fy,fz),fo) for ix in range(nf_x) for iy in range(nf_y)]
        add(ps,'standard_grid')
  # Directional base with each directly supported standard cell center inside its base.
  # Relative dimensions derived from current data; misfit is rejected by checker.
  for base in [t for t in types if t['category']=='定向件']:
   bx,by,bz=base['dims'];nbx,nby=(1,1) if base['cargo_type']=='G4' else (2,2)
   BW,BY=nbx*bx,nby*by
   for std in [t for t in types if t['category']=='标准件']:
    # Heightwise standard orientation is original width, height, length.
    sx,sy,sz=(std['dims'][1],std['dims'][2],std['dims'][0]);so='120'
    for (fx,fy,fz),fo in orientations(frag,config.get('fragile_fixed',False)):
     if 2*sx>BW or 2*sy>BY or fx>2*sx or fy>2*sy:continue
     ox=(BW-2*sx)//2;oy=(BY-2*sy)//2
     for k in range(1,(H-sz-fz)//bz+1):
      ps=[part(base['cargo_type'],ix*bx,iy*by,iz*bz,(bx,by,bz),'012') for iz in range(k) for ix in range(nbx) for iy in range(nby)]
      ps += [part(std['cargo_type'],ox+ix*sx,oy+iy*sy,k*bz,(sx,sy,sz),so) for ix in range(2) for iy in range(2)]
      ps += [part(frag['cargo_type'],ox+(2*sx-fx)//2,oy+(2*sy-fy)//2,k*bz+sz,(fx,fy,fz),fo)]
      add(ps,'protected_directional')
 CACHE[key]=out
 CERTIFICATES.append({'vehicle':v['type_id'],'config_pressure':pressure,'fragile_fixed':config.get('fragile_fixed',False),'accepted':len(out),'rejected':len(failed),'rejections':failed,'seconds':time.perf_counter()-start,'scope':'all candidate blocks explicitly checked before consumption'})
 return out

def pack(types,v,remaining,weights,config,orientations):
 blocks=catalog(types,v,config,orientations);L,W,H=v['dims'];H-=v['clearance_mm'];free=[(0,0,L,W)];cnt=np.zeros(len(types),int);mass=0.;parts=[]
 pressure=config.get('pressure',500);strict=config.get('fragile_fixed',False)
 bc=np.array([b['counts'] for b in blocks],int);bm=np.array([b['mass'] for b in blocks]);bw=np.array([b['width'] for b in blocks]);bd=np.array([b['depth'] for b in blocks]);bv=np.array([b['volume'] for b in blocks]);bs=bc@weights/(bw*bd) if blocks else []
 while free:
  rem=np.array(remaining)-cnt;best=None
  eligible=np.all(bc<=rem,axis=1)&(bm<=v['payload_kg']-mass+1e-8) if blocks else []
  for fi,(x,y,fl,fw) in enumerate(free):
   for ti,t in enumerate(types):
    if rem[ti]<=0:continue
    for (dx,dy,dz),ori in orientations(t,strict):
     if dx>fl or dy>fw or dz>H:continue
     cap=1 if t['category']=='易碎件' else min(H//dz,1+int(pressure*dx*dy/1e6/t['weight']+1e-9))
     k=min(cap,int(rem[ti]),int((v['payload_kg']-mass+1e-8)//t['weight']))
     if k<1:continue
     key=(weights[ti]*k/(dx*dy),k*dx*dy*dz,-fl*fw,-fi)
     if best is None or key>best[0]:best=(key,fi,'column',(ti,dx,dy,dz,ori,k))
   if blocks:
    idx=np.flatnonzero(eligible&(bw<=fl)&(bd<=fw))
    if len(idx):
     j=max(idx,key=lambda j:(bs[j],bv[j],-j));key=(float(bs[j]),int(bv[j]),-fl*fw,-fi)
     if best is None or key>best[0]:best=(key,fi,'block',int(j))
  if best is None:break
  _,fi,kind,d=best;x,y,fl,fw=free.pop(fi)
  if kind=='column':
   ti,dx,dy,dz,ori,k=d;cnt[ti]+=k;mass+=k*types[ti]['weight']
   parts += [{'cargo_type':types[ti]['cargo_type'],'x_mm':x,'y_mm':y,'z_mm':h*dz,'dx_mm':dx,'dy_mm':dy,'dz_mm':dz,'orientation_id':ori} for h in range(k)]
  else:
   b=blocks[d];dx,dy=b['width'],b['depth'];cnt+=b['counts'];mass+=b['mass']
   parts += [{**q,'x_mm':x+q['x_mm'],'y_mm':y+q['y_mm']} for q in b['placements']]
  if fl-dx>=fw-dy:
   if fl>dx:free.append((x+dx,y,fl-dx,fw))
   if fw>dy:free.append((x,y+dy,dx,fw-dy))
  else:
   if fw>dy:free.append((x,y+dy,fl,fw-dy))
   if fl>dx:free.append((x+dx,y,fl-dx,dy))
 return {'vehicle_type':v['type_id'],'counts':cnt.tolist(),'placements':parts}
