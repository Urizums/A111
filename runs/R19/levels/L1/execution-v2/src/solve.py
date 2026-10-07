"""Offline full-support height-map constructive solver; cm, kg, yuan.
No external solution or network dependency. Run from any cwd.
"""
from pathlib import Path
import argparse, json, math, time, itertools, hashlib
import numpy as np
from scipy.ndimage import maximum_filter1d, minimum_filter1d
from scipy.optimize import milp, LinearConstraint, Bounds
ROOT=Path(__file__).resolve().parents[1]
DEFAULT={'vehicles':[{'id':'T1','dims':[420,210,220],'payload':6000,'cost':450},{'id':'T2','dims':[680,245,250],'payload':10000,'cost':700}], 'cargo':[{'id':'G1','category':'standard','dims':[60,40,30],'weight':12,'quantity':800},{'id':'G2','category':'standard','dims':[50,35,25],'weight':8,'quantity':1000},{'id':'G3','category':'fragile','dims':[70,50,40],'weight':15,'quantity':300},{'id':'G4','category':'directional','dims':[80,60,50],'weight':25,'quantity':400},{'id':'G5','category':'directional','dims':[40,40,60],'weight':18,'quantity':500}], 'clearance':3,'bearing':500,'fragile_rotation':False}

def extrema(a,n,m,maximum=False):
    f=maximum_filter1d if maximum else minimum_filter1d
    b=f(a,n,axis=0,mode='nearest');b=f(b,m,axis=1,mode='nearest')
    return b[n//2:n//2+a.shape[0]-n+1,m//2:m//2+a.shape[1]-m+1]

def orientations(c,cfg):
    if c['category']=='standard':return sorted(set(itertools.permutations(c['dims'])))
    if c['category']=='fragile' and cfg.get('fragile_rotation'):return sorted(set([tuple(c['dims']),tuple([c['dims'][1],c['dims'][0],c['dims'][2]])]))
    return [tuple(c['dims'])]

def grid_unit(cfg):
    # exact rational source/scenario coordinates, at most 0.1 cm denominator
    vals=[round(x*10) for c in cfg['cargo'] for x in c['dims']]
    return math.gcd(*vals)/10

class Truck:
    def __init__(self,v,cfg):
        self.v=v;self.cfg=cfg;self.u=grid_unit(cfg);self.shape=tuple(int(x/self.u+1e-8) for x in v['dims'][:2])
        self.h=np.zeros(self.shape);self.cat=np.zeros(self.shape,dtype=np.int8);self.rem=np.full(self.shape,1e12)
        self.items=[];self.weight=0;self.cache={};self.version=0
        self.bx0=np.full(self.shape,-1e12);self.by0=np.full(self.shape,-1e12);self.bx1=np.full(self.shape,1e12);self.by1=np.full(self.shape,1e12)
    def find(self,c,ceiling,mode='compact'):
        if self.weight+c['weight']>self.v['payload']+1e-8:return None
        best=None
        for dx,dy,dz in orientations(c,self.cfg):
            nx,ny=round(dx/self.u),round(dy/self.u)
            if nx>self.shape[0] or ny>self.shape[1]:continue
            key=(nx,ny)
            if key not in self.cache:
                self.cache[key]=(extrema(self.h,nx,ny),extrema(self.h,nx,ny,True),extrema(self.cat,nx,ny),extrema(self.cat,nx,ny,True),extrema(self.rem,nx,ny),extrema(self.bx0,nx,ny,True),extrema(self.by0,nx,ny,True),extrema(self.bx1,nx,ny),extrema(self.by1,nx,ny),extrema((self.cat==2).astype(np.int8),nx,ny,True))
            low,high,cl,ch,rem,bx0,by0,bx1,by1,frag=self.cache[key]
            ok=(abs(high-low)<1e-7)&(high+dz<=ceiling+1e-7)&(frag==0)
            if c.get('floor_only'):ok &= high==0
            if self.cfg.get('directional_center_each',True):
                centerx=np.arange(ok.shape[0])[:,None]*self.u+dx/2;centery=np.arange(ok.shape[1])[None,:]*self.u+dy/2
                ok &= (centerx>=bx0-1e-7)&(centerx<=bx1+1e-7)&(centery>=by0-1e-7)&(centery<=by1+1e-7)
            if c['category']=='fragile':ok &= ((high==0)|((cl==1)&(ch==1)))
            if c['category']=='fragile' and self.cfg.get('fragile_floor_only'):ok &= high==0
            pressure=c['weight']/(dx*dy/10000)
            ok &= ((high==0)|(rem+1e-7>=pressure))
            xi,yi=np.nonzero(ok)
            if not len(xi):continue
            if mode=='compact':score=xi*self.u + yi*self.u*self.v['dims'][0]/self.v['dims'][1] + high[xi,yi]*0.02
            elif mode=='low':score=high[xi,yi]*10000+yi*self.u*10+xi*self.u
            elif mode=='high':score=-high[xi,yi]*10000+yi*self.u*10+xi*self.u
            else:score=yi*self.u*1000+xi*self.u+high[xi,yi]*0.01
            ix=int(np.argmin(score)); cand=(float(score[ix]),xi[ix],yi[ix],float(high[xi[ix],yi[ix]]),dx,dy,dz,pressure)
            # Prefer physical volume per occupied area where geometric scores tie.
            if best is None or cand[0]<best[0]-1e-7 or (abs(cand[0]-best[0])<1e-7 and dz>best[6]):best=cand
        return best
    def add(self,c,p,serial):
        _,i,j,z,dx,dy,dz,pressure=p;nx,ny=round(dx/self.u),round(dy/self.u);s=np.s_[i:i+nx,j:j+ny]
        self.rem[s]=np.minimum(self.cfg['bearing'],np.where(self.h[s]>0,self.rem[s]-pressure,self.cfg['bearing']))
        self.h[s]=z+dz;self.cat[s]={'standard':1,'fragile':2,'directional':3}[c['category']]
        if c['category']=='directional':
            self.bx0[s]=i*self.u;self.by0[s]=j*self.u;self.bx1[s]=i*self.u+dx;self.by1[s]=j*self.u+dy
        else:self.bx0[s]=-1e12;self.by0[s]=-1e12;self.bx1[s]=1e12;self.by1[s]=1e12
        self.weight+=c['weight'];self.items.append({'item_id':f"{c['id']}-{serial:04d}",'type_id':c['id'],'x':float(i*self.u),'y':float(j*self.u),'z':z,'dx':dx,'dy':dy,'dz':dz,'weight':c['weight'],'category':c['category'],'orientation':[c['dims'].index(dx),c['dims'].index(dy),c['dims'].index(dz)]})
        # axis permutations for equal sides are canonicalized independently later
        self.cache.clear();self.version+=1

def strategy_list(budget=12):
    # Declared deterministic alternatives: fragile support preparation and ordering.
    out=[]
    for dirfirst in [True,False]:
      for mode in ['compact','low']:
       for fraction in [0.65,0.8,1.0]:
        out.append({'dirfirst':dirfirst,'mode':mode,'fraction':fraction,'standard_order':['G2','G1']})
    if budget>12:
      for mode in ['compact','high','low']:
       for fraction in [0.55,0.7,0.85,1.0]:
        out.append({'dirfirst':True,'mode':mode,'fraction':fraction,'standard_order':['G1','G2']})
    return out[:budget]

def pack(v,cfg,remaining,strategy,serials=None):
    tr=Truck(v,cfg);serials=serials or {c['id']:0 for c in cfg['cargo']};cargo={c['id']:c for c in cfg['cargo']}; H=v['dims'][2]-cfg['clearance'];mode=strategy['mode']
    def fill(t,ceiling):
        c=cargo[t]
        while remaining[t]>0:
            p=tr.find(c,ceiling,mode)
            if p is None:break
            remaining[t]-=1;serials[t]+=1;tr.add(c,p,serials[t])
    if remaining.get('G3',0):
        reserve=cargo['G3']['dims'][2]
        phaseH=H-reserve
        if strategy['dirfirst']:
            for t in ['G4','G5']:
                if t in cargo:fill(t,min(phaseH,strategy['fraction']*H))
        for t in strategy['standard_order']:
            if t in cargo:fill(t,phaseH)
        fill('G3',H)
    for t in ['G4','G5']+strategy['standard_order']+['G3']:
        if t in cargo:fill(t,H)
    return tr

def fleet_fixed(v,cfg,strategy):
    rem={c['id']:c['quantity'] for c in cfg['cargo']};serials=dict.fromkeys(rem,0);fleet=[]
    while sum(rem.values()):
        t=pack(v,cfg,rem,strategy,serials)
        if not t.items:raise ValueError(f'Unpackable items: {rem}')
        fleet.append({'vehicle_type':v['id'],'vehicle':v,'items':t.items})
        if len(fleet)>sum(c['quantity'] for c in cfg['cargo']):raise ValueError('no progress')
    return fleet

def module_pack(v,cfg,remaining,variant=0,serials=None):
    """Targeted repair for fragmented fragile support: explicit load-bearing pads.
    Source dimensions only; changed-dimension scenarios fall back to generic map.
    """
    tr=Truck(v,cfg);cs={c['id']:c for c in cfg['cargo']};serials=serials or dict.fromkeys(cs,0);H=v['dims'][2]-cfg['clearance']
    if [cs[k]['dims'] for k in ['G1','G2','G3','G4','G5']]!=[c['dims'] for c in DEFAULT['cargo']]:return pack(v,cfg,remaining,strategy_list()[4],serials)
    def make(kind):
      items=[]
      def one(t,x,y,z,dx,dy,dz):items.append((t,x,y,z,dx,dy,dz))
      if kind=='g4':
        n=min(3,int((H-65)//50));pad=int((H-40-50*n)//25)
        if n<1 or pad<1:return None
        if remaining['G4']<n or remaining['G2']<pad*2:return None
        for k in range(n):one('G4',0,0,k*50,80,60,50)
        for k in range(pad):
          for x in [0,35]:one('G2',x,0,n*50+k*25,35,50,25)
        one('G3',0,0,n*50+pad*25,70,50,40);return 80,60,items
      if kind=='g5':
        if variant>=4 and H>=245 and remaining['G5']>=12 and remaining['G2']>=2:
          for k in range(3):
            for x in [0,40]:
              for y in [0,40]:one('G5',x,y,k*60,40,40,60)
          for x in [5,40]:one('G2',x,15,180,35,50,25)
          one('G3',5,15,205,70,50,40);return 80,80,items
        n=int((H-70)//60);pad=int((H-40-60*n)//30)
        if n<1 or pad<1 or remaining['G5']<n*4 or remaining['G1']<pad*2:return None
        for k in range(n):
          for x in [0,40]:
            for y in [0,40]:one('G5',x,y,k*60,40,40,60)
        for k in range(pad):
          for x in [0,40]:one('G1',x,10,n*60+k*30,40,60,30)
        one('G3',5,15,n*60+pad*30,70,50,40);return 80,80,items
      if kind=='mix':
        opts=[]
        for a in range(min(int((H-40)//30),remaining['G1']//2,math.ceil(remaining['G1']/max(2,2*remaining['G3'])))+1):
          for b in range(min(int((H-40)//25),remaining['G2']//2,math.ceil(remaining['G2']/max(2,2*remaining['G3'])))+1):
            if a+b==0 or a*30+b*25>H-40:continue
            area=.48 if a else .35;vol=a*2*.072+b*2*.04375+.14
            opts.append((vol/area,a,b))
        if not opts:return None
        _,a,b=max(opts)
        for k in range(a):
          for x in [0,40]:one('G1',x,0,k*30,40,60,30)
        for k in range(b):
          for x in [0,35]:one('G2',x,0,a*30+k*25,35,50,25)
        one('G3',0,0,a*30+b*25,70,50,40);return (80 if a else 70),(60 if a else 50),items
      t='G1' if kind=='s1' else 'G2';dz=30 if t=='G1' else 25;dx=40 if t=='G1' else 35;dy=60 if t=='G1' else 50
      # Reserve at least a two-box pad for every still unassigned fragile item.
      allowed=max(1,remaining[t]//max(2,2*remaining['G3']))
      n=min(int((H-40)//dz),remaining[t]//2,allowed+(variant%2))
      if n<1:return None
      for k in range(n):
        for x in [0,dx]:one(t,x,0,k*dz,dx,dy,dz)
      one('G3',(dx*2-70)/2,(dy-50)/2,n*dz,70,50,40);return dx*2,dy,items
    order=['g4','g5','s2','s1'] if variant<2 else ['g5','g4','s1','s2']
    if variant>=4:order=['g4','g5','mix'] if variant%2==0 else ['g5','g4','mix']
    while remaining['G3']>0:
      choices=[]
      for kind in order:
        mod=make(kind)
        if mod is None:continue
        dx,dy,items=mod;zmax=max(i[3]+i[6] for i in items);wt=sum(cs[i[0]]['weight'] for i in items)
        c={'id':'module','category':'module','dims':[dx,dy,zmax],'weight':wt,'floor_only':True}
        p=tr.find(c,H,'compact')
        if p is not None:choices.append((kind,p,items));break
      if not choices:break
      kind,p,items=choices[0];bx,by=p[1]*tr.u,p[2]*tr.u
      for t,x,y,z,dx,dy,dz in sorted(items,key=lambda i:i[3]):
        c=cs[t];density=c['weight']/(dx*dy/10000);pp=(0,round((bx+x)/tr.u),round((by+y)/tr.u),z,dx,dy,dz,density)
        remaining[t]-=1;serials[t]+=1;tr.add(c,pp,serials[t])
    for t in (['G5','G4','G1','G2','G3'] if variant%2 else ['G4','G5','G2','G1','G3']):
      c=cs[t]
      while remaining[t]>0:
        p=tr.find(c,H,'compact')
        if p is None:break
        remaining[t]-=1;serials[t]+=1;tr.add(c,p,serials[t])
    return tr

def fleet_module(v,cfg,variant):
    rem={c['id']:c['quantity'] for c in cfg['cargo']};ser=dict.fromkeys(rem,0);f=[]
    while sum(rem.values()):
      tr=module_pack(v,cfg,rem,variant,ser)
      if not tr.items:raise ValueError(f'Unpackable: {rem}')
      f.append({'vehicle_type':v['id'],'vehicle':v,'items':tr.items})
    return canonicalize(f,cfg)

def stats(fleet,cfg):
    V=sum(math.prod(c['dims'])*c['quantity'] for c in cfg['cargo']);W=sum(c['weight']*c['quantity'] for c in cfg['cargo'])
    if not fleet:return {}
    return {'vehicles':len(fleet),'cost':sum(t['vehicle']['cost'] for t in fleet),'volume_cm3':sum(math.prod([i['dx'],i['dy'],i['dz']]) for t in fleet for i in t['items']),'weight_kg':sum(i['weight'] for t in fleet for i in t['items']),'volume_rate':sum(math.prod([i['dx'],i['dy'],i['dz']]) for t in fleet for i in t['items'])/sum(math.prod(t['vehicle']['dims']) for t in fleet),'load_rate':sum(i['weight'] for t in fleet for i in t['items'])/sum(t['vehicle']['payload'] for t in fleet),'vehicle_counts':{v['id']:sum(t['vehicle_type']==v['id'] for t in fleet) for v in cfg['vehicles']}}

def canonicalize(fleet,cfg):
    cs={c['id']:c for c in cfg['cargo']};seq=dict.fromkeys(cs,0)
    for j,t in enumerate(fleet,1):
      t['truck_id']=f'V{j:03d}'
      for i in t['items']:
        seq[i['type_id']]+=1;i['item_id']=f"{i['type_id']}-{seq[i['type_id']]:04d}";i['truck_id']=t['truck_id']
        dims=cs[i['type_id']]['dims']; i['orientation']=next(list(p) for p in itertools.permutations(range(3)) if all(abs(dims[p[k]]-i[['dx','dy','dz'][k]])<1e-7 for k in range(3)))
    return fleet

def patterns_master(pool,cfg,objective,seconds=30,upper_bound=None):
    types=[c['id'] for c in cfg['cargo']];a=np.array([[sum(i['type_id']==t for i in p['items']) for p in pool] for t in types]);q=np.array([c['quantity'] for c in cfg['cargo']]);cost=np.array([p['vehicle']['cost'] for p in pool])
    # Optimize each requested primary objective directly; preserve known incumbent
    # in the caller when the integer search stops on its time limit.
    c=np.ones(len(pool)) if objective=='count' else cost
    constraints=[LinearConstraint(a,q,q)]
    if upper_bound is not None:constraints.append(LinearConstraint(c,-np.inf,upper_bound))
    r=milp(c,integrality=np.ones(len(pool)),bounds=Bounds(np.zeros(len(pool)),np.full(len(pool),np.inf)),constraints=constraints,options={'time_limit':seconds,'mip_rel_gap':0})
    if r.x is None:return None,{'status':int(r.status),'message':r.message}
    fleet=[]
    for p,n in zip(pool,np.rint(r.x).astype(int)):
        for _ in range(n):fleet.append(json.loads(json.dumps(p)))
    return canonicalize(fleet,cfg),{'status':int(r.status),'message':r.message,'pool_size':len(pool),'restricted_pool_optimal':r.status==0,'solver_gap':float(r.mip_gap) if r.mip_gap is not None else None,'dual_bound':float(r.mip_dual_bound) if r.mip_dual_bound is not None else None,'objective_value':float(r.fun),'incumbent_cut':upper_bound}

def run(cfg,budget,out):
    from check import check_fleet
    validate_config(cfg)
    out.mkdir(parents=True,exist_ok=True);strategies=strategy_list(budget);records=[];best={};pool=[];single={}
    for v in cfg['vehicles']:
      candidates=[]; singles=[]
      for k,s in enumerate(strategies):
        tic=time.perf_counter();f=canonicalize(fleet_fixed(v,cfg,s),cfg);dt=time.perf_counter()-tic
        st=stats(f,cfg);check=check_fleet(f,cfg,True)
        records.append({'task':v['id'],'strategy_id':k,'strategy':s,'seconds':dt,'statistics':st,'valid':check['valid']})
        if not check['valid']:raise RuntimeError(check)
        candidates.append((st['vehicles'],st['cost'],k,f));pool.extend(f)
        rem={c['id']:c['quantity'] for c in cfg['cargo']};tr=pack(v,cfg,rem,s);sf=canonicalize([{'vehicle_type':v['id'],'vehicle':v,'items':tr.items}],cfg);ss=stats(sf,cfg);singles.append({'strategy_id':k,'statistics':ss,'fleet':sf})
        print(v['id'],k,st['vehicles'],round(st['volume_rate'],4),round(dt,2),flush=True)
      winner=min(candidates,key=lambda x:x[:3]);best[v['id']]=winner[3]
      # Additional density anchors: skip fragile preparation and target cargo ranking.
      for order in [['G5','G1','G2','G4','G3'],['G1','G2','G5','G4','G3'],['G4','G1','G2','G5','G3'],['G2','G1','G5','G4','G3']]:
        tr=Truck(v,cfg);rem={c['id']:c['quantity'] for c in cfg['cargo']};serials=dict.fromkeys(rem,0)
        for name in order:
          c=next(c for c in cfg['cargo'] if c['id']==name)
          while rem[name]>0:
            p=tr.find(c,v['dims'][2]-cfg['clearance'],'compact')
            if p is None:break
            rem[name]-=1;serials[name]+=1;tr.add(c,p,serials[name])
        sf=canonicalize([{'vehicle_type':v['id'],'vehicle':v,'items':tr.items}],cfg);ss=stats(sf,cfg);singles.append({'strategy_id':'anchor-'+','.join(order),'statistics':ss,'fleet':sf})
      nd=[x for x in singles if not any(y['statistics']['volume_rate']>=x['statistics']['volume_rate']-1e-10 and y['statistics']['load_rate']>=x['statistics']['load_rate']-1e-10 and (y['statistics']['volume_rate']>x['statistics']['volume_rate']+1e-10 or y['statistics']['load_rate']>x['statistics']['load_rate']+1e-10) for y in singles)]
      seen=set();single[v['id']]=[]
      for p in nd:
        key=(p['statistics']['volume_cm3'],p['statistics']['weight_kg'])
        if key not in seen:single[v['id']].append(p);seen.add(key)
      (out/f'fixed_{v["id"]}.json').write_text(json.dumps({'config':cfg,'fleet':best[v['id']],'statistics':stats(best[v['id']],cfg)},ensure_ascii=False),encoding='utf8')
    # Remove identical count patterns to keep master modest; preserve first geometry.
    uniq={}
    for p in pool:
      key=(p['vehicle_type'],tuple(sum(i['type_id']==c['id'] for i in p['items']) for c in cfg['cargo']))
      uniq.setdefault(key,p)
    pool=list(uniq.values());master={}
    for obj in ['count','cost']:
      f,receipt=patterns_master(pool,cfg,obj)
      if f is None: f=min(best.values(),key=lambda f:(len(f),stats(f,cfg)['cost']) if obj=='count' else (stats(f,cfg)['cost'],len(f)))
      report=check_fleet(f,cfg,True)
      if not report['valid']:raise RuntimeError(report)
      master[obj]={'config':cfg,'fleet':f,'statistics':stats(f,cfg),'master':receipt};(out/f'mixed_{obj}.json').write_text(json.dumps(master[obj],ensure_ascii=False),encoding='utf8')
    (out/'single_pareto.json').write_text(json.dumps({'config':cfg,'solutions':single},ensure_ascii=False),encoding='utf8')
    (out/'search_records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
    return best,master,single,records

def validate_config(cfg):
    from contracts import validate_config as validate_source_contract
    return validate_source_contract(cfg)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=ROOT/'configs/base.json');ap.add_argument('--out',type=Path,default=ROOT/'results/main');ap.add_argument('--budget',type=int,default=12);args=ap.parse_args()
    cfg=json.loads(args.config.read_text(encoding='utf-8-sig'))
    run(cfg,args.budget,args.out)
