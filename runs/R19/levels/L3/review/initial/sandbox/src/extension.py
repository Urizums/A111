import json,re,itertools,copy,math
from solver import E,save,instance,solve,write_plan
from checker import validate_dir
def interval(v,scale):
 if isinstance(v,(int,float)):return (v*scale,v*scale)
 if v is None:return None
 nums=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',str(v))]
 if not nums:return None
 return (nums[0]*scale,(nums[1] if len(nums)>1 else nums[0])*scale)
def main():
 audit=json.loads((E/'data/raw_audit.json').read_text(encoding='utf-8'));s=audit['xlsx'];cells={c['cell']:c['value'] for c in s['箱装产品尺寸']['cells']};products=[]
 for r in range(3,11):
  bounds=[interval(cells.get(f'{a}{r}'),.1) for a in ['C','E','G']];labs=[interval(cells.get(f'{a}{r}'),.1) for a in ['B','D','F']]
  products.append({'row':r,'name':cells.get(f'A{r}'),'warehouse_interval_cm':bounds,'lab_interval_cm':labs,'upper_cm':[b[1] if b else None for b in bounds],'lower_cm':[b[0] if b else None for b in bounds],'weight_kg':None,'quantity':None,'category':None,'origin':'official dimensions only'})
 vc={c['cell']:c['value'] for c in s['车型尺寸']['cells']};vehicles=[]
 for r in range(7,12):
  bs=[interval(vc.get(f'{a}{r}'),100) for a in 'BCD'];vehicles.append({'row':r,'name':vc.get(f'A{r}'),'interval_cm':bs,'robust_cm':[b[0] if b else None for b in bs],'cost_raw':vc.get(f'E{r}'),'cost_unit':'yuan/1000km','capacity_kg':None,'origin':'official dimensions only'})
 fits=[]
 for p in products:
  for v in vehicles:
   if None in p['upper_cm'] or None in v['robust_cm']:fits.append({'product_row':p['row'],'vehicle_row':v['row'],'fits':None,'reason':'missing dimension'});continue
   dim=list(v['robust_cm']);dim[2]-=3;fit=any(all(a<=b for a,b in zip(o,dim)) for o in set(itertools.permutations(p['upper_cm'])))
   fits.append({'product_row':p['row'],'vehicle_row':v['row'],'fits':fit,'interpretation':'single item, orthogonal orientations assumed scenario; upper box / lower truck dimensions, 3cm gap'})
 save(E/'extension/attachment2_normalized.json',{'products':products,'vehicles':vehicles,'fits':fits,'excluded':['rail/water modality rows4-6: fee basis unclear','栏板车 rows12-18: not enclosed height','阶梯车厢 row19: noncuboid','Sheet3 empty'],'scope':'parser and robust single-item fit only; no official batch transportation optimization due to absent mass/quantity/type/payload/distance'})
 d=instance()
 for i,c in enumerate(d['cargo']):c['quantity']=4 if i==0 else 0
 d['vehicles'][0].update(l_cm=60,w_cm=40,h_cm=63,capacity_kg=6000);cfg={'gap':3,'pressure':500,'run_seconds':60}
 rows,m=solve(d,'Q1-S1','maxrect',0,0,cfg);out=E/'oracle/exact_volume';write_plan(out,rows,m,cfg,d);vr=validate_dir(out);assert vr['passed'] and len(rows)==2
 save(E/'oracle/proof.json',{'instance':'scenario T1=60x40x63cm; effective height60cm; four G1 originals; other quantities0','volume_upper_item_count':2,'reason':'effective box volume144000 cm3 / G1 volume72000cm3; floor stack2 at z0,30 achieves bound','solver_item_count':len(rows),'volume':m['volume_m3'],'mass':m['weight_kg'],'global_for_this_homogeneous_tiny_instance':True,'not_a_proof_for_original_full_instance':True})
 # Parent contact compression can fail while direct masses all look safe.
 save(E/'extension/summary.json',{'products':len(products),'enclosed_vehicle_rows':len(vehicles),'fit_tests':len(fits),'fits':sum(x['fits'] is True for x in fits),'unknown':sum(x['fits'] is None for x in fits),'tiny_oracle_passed':True})
 print(json.dumps(json.loads((E/'extension/summary.json').read_text(encoding='utf-8')),ensure_ascii=False))
if __name__=='__main__':main()
