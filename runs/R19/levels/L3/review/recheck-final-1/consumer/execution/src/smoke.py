import copy,json,time
from pathlib import Path
from solver import instance,solve,write_plan,save,E
from checker import validate_dir,check
d=instance()
for c,n in zip(d['cargo'],[8,8,2,4,6]):c['quantity']=n
cfg={'gap':3,'pressure':500,'run_seconds':60,'declared_window_seconds':120,'memory_target_MB':1800}
r,m=solve(d,'Q1-F1','maxrect',0,.2,cfg);p=E/'smoke/valid';write_plan(p,r,m,cfg,d);v=validate_dir(p);assert v['passed'],v['errors']
bad=copy.deepcopy(r);bad[0]['x_cm']=9999;bv=check(bad,d,cfg,'Q1-F1');assert not bv['passed'] and any(e['rule']=='boundary_top_gap' for e in bv['errors']);save(E/'smoke/invalid_boundary/validation.json',bv);save(E/'smoke/invalid_boundary/placements.json',bad)
press=copy.deepcopy(r)
for rr in press:
 if rr['support_ids']:
  # Tested an intentionally too-low physical pressure parameter, preserving coordinates.
  break
pv=check(press,d,{**cfg,'pressure':1},'Q1-F1');assert not pv['passed'] and any(e['rule']=='cumulative_pressure' for e in pv['errors']);save(E/'smoke/invalid_pressure/validation.json',pv)
save(E/'smoke/summary.json',{'valid':v['passed'],'items':len(r),'N':m['N'],'contains_standard_fragile_directional':True,'fragile_on_standard':any(x['cargo_type']=='G3' and x['support_ids'] for x in r),'illegal_boundary_rejected':not bv['passed'],'illegal_pressure_rejected':not pv['passed'],'metrics':m})
assert any(x['cargo_type']=='G3' and x['support_ids'] for x in r),'smoke must exercise fragile standard support'
print(json.dumps({'smoke_pass':True,'N':m['N'],'Uv':m['Uv'],'Uw':m['Uw'],'fragile_on_standard':any(x['cargo_type']=='G3' and x['support_ids'] for x in r)},ensure_ascii=False))
