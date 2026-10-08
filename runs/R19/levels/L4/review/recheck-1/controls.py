from pathlib import Path
import csv,json,subprocess,time,copy
O=Path(__file__).resolve().parent; C=O/'consumer'; D=json.loads((C/'data/raw_rebuilt.json').read_text(encoding='utf8')); CFG=json.loads((C/'configs/refined.json').read_text(encoding='utf8'))
BASE=list(csv.DictReader((O.parent/'initial/valid_single_real_row.csv').open(encoding='utf-8-sig',newline=''))); F=list(BASE[0]); records=[]
T=O/'controls';T.mkdir(exist_ok=True)
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=True),encoding='utf8')
def run(name,rows=None,data=None,cfg=None,legal=False,solve=False,infeasible=False):
    p=T/name;p.mkdir();save(p/'data.json',D if data is None else data);save(p/'config.json',CFG if cfg is None else cfg)
    if solve:cmd=['py','-3.12','-X','utf8','-B','code/solve.py','--data',str(p/'data.json'),'--config',str(p/'config.json'),'--out',str(p/'run'),'--method','maxrects']
    else:
        with (p/'placements.csv').open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=F);w.writeheader();w.writerows(BASE if rows is None else rows)
        cmd=['py','-3.12','-X','utf8','-B','code/validator.py','--data',str(p/'data.json'),'--config',str(p/'config.json'),'--placements',str(p/'placements.csv'),'--out',str(p/'result.json'),'--single']
    t=time.perf_counter();r=subprocess.run(cmd,cwd=C,text=True,encoding='utf8',capture_output=True);elapsed=time.perf_counter()-t
    (p/'stdout.txt').write_text(r.stdout,encoding='utf8');(p/'stderr.txt').write_text(r.stderr,encoding='utf8')
    dest=(p/'run/failure.json') if solve else p/'result.json';out=json.loads(dest.read_text(encoding='utf8')) if dest.exists() else None
    successful=list((p/'run').rglob('summary.json')) if solve else []
    ok=(r.returncode==0 and (bool(successful) if solve else out is not None and out.get('valid') is True)) if legal else (r.returncode!=0 and out is not None and out.get('valid') is False and not successful)
    if infeasible:ok=ok and out.get('status')=='infeasible_input' and 'G1' in out.get('message','') and 'cannot fit' in out.get('message','') and 'Traceback' not in r.stderr
    rec={'name':name,'command':cmd,'cwd':str(C),'exit_code':r.returncode,'elapsed_seconds':elapsed,'expected':'legal' if legal else ('clear_infeasible' if infeasible else 'reject'),'observed_result':out,'successful_summary_files':[str(x.relative_to(O)) for x in successful],'assertion_passed':bool(ok),'process_state':'finished'}
    save(p/'receipt.json',rec);records.append(rec);save(O/'controls-progress.json',records);print(name,r.returncode,ok,flush=True)
run('valid_real_floor',legal=True)
r=copy.deepcopy(BASE);r2=copy.deepcopy(r[0]);r2['item_id']='G1-0002';r2['x']=float(r[0]['l']);r.append(r2);run('valid_boundary_touch',r,legal=True)
r=copy.deepcopy(BASE);r2=copy.deepcopy(r[0]);r2['item_id']='G1-0002';r2['z']=float(r[0]['h']);r2['support_ids']=r[0]['item_id'];r.append(r2);run('valid_supported_stack',r,legal=True)
d=copy.deepcopy(D);d['cargo'][2]['quantity']=0;run('valid_zero_class_quantity',data=d,legal=True)
for k in ['x','y','z','l','w','h']:
    for val,label in [(float('nan'),'nan'),(float('inf'),'posinf'),(-float('inf'),'neginf')]:
        r=copy.deepcopy(BASE);r[0][k]=str(val);run('csv_'+k+'_'+label,r)
for k in ['x','y','z']:
    r=copy.deepcopy(BASE);r[0][k]=-1;run('negative_'+k,r)
for k in ['l','w','h']:
    for val in [0,-1]:
        r=copy.deepcopy(BASE);r[0][k]=val;run('nonpositive_'+k+'_'+str(val),r)
for val,label in [('','blank'),('bogus','text')]:
    r=copy.deepcopy(BASE);r[0]['x']=val;run('csv_'+label,r)
r=copy.deepcopy(BASE);r2=copy.deepcopy(r[0]);r2['item_id']='G1-0002';r.append(r2);run('positive_overlap',r)
r=copy.deepcopy(BASE);r[0]['z']=D['vehicles'][0]['dims'][2]-CFG['gap_cm']-float(r[0]['h'])+1;run('height_gap',r)
fields=[('cargo_dimension',('cargo',0,'dims',0)),('cargo_mass',('cargo',0,'mass')),('vehicle_dimension',('vehicles',0,'dims',0)),('vehicle_capacity',('vehicles',0,'capacity')),('vehicle_cost',('vehicles',0,'cost')),('quantity',('cargo',0,'quantity'))]
def mutate(obj,path,val):
    ptr=obj
    for k in path[:-1]:ptr=ptr[k]
    ptr[path[-1]]=val
for name,path in fields:
    for val,label in [(float('nan'),'nan'),(float('inf'),'posinf'),(-float('inf'),'neginf')]:
        d=copy.deepcopy(D);mutate(d,path,val);run('data_'+name+'_'+label,data=d)
    for val,label in [(0,'zero'),(-1,'negative'),(True,'boolean'),('12','string')]:
        if name=='quantity' and val==0:continue
        d=copy.deepcopy(D);mutate(d,path,val);run('data_'+name+'_'+label,data=d)
for val,label in [(1.5,'fraction'),(1.0,'float_integer')]:
    d=copy.deepcopy(D);d['cargo'][0]['quantity']=val;run('quantity_'+label,data=d)
for k in ['gap_cm','pressure_kg_m2','tolerance_cm']:
    for val,label in [(float('nan'),'nan'),(float('inf'),'posinf'),(-float('inf'),'neginf'),(-1,'negative')]:
        cfg=copy.deepcopy(CFG);cfg[k]=val;run('config_'+k+'_'+label,cfg=cfg)
cfg=copy.deepcopy(CFG);cfg['gap_cm']=220;run('gap_reaches_vehicle_height',cfg=cfg)
cfg=copy.deepcopy(CFG);cfg['pressure_kg_m2']=0;run('zero_pressure',cfg=cfg)
d=copy.deepcopy(D);d['cargo'][0]['mass']=float('nan');run('solver_invalid_mass',data=d,solve=True)
cfg=copy.deepcopy(CFG);cfg['gap_cm']=float('inf');run('solver_invalid_gap',cfg=cfg,solve=True)
d=copy.deepcopy(D)
for g in d['cargo']:g['quantity']=0
d['cargo'][0]['quantity']=1;d['cargo'][0]['dims']=[1001,1001,1001];run('solver_impossible_1001_cube',data=d,solve=True,infeasible=True)
d=copy.deepcopy(D)
for g in d['cargo']:g['quantity']=max(1,int(g['quantity']*.025))
cfg=copy.deepcopy(CFG);cfg.update(pattern_count_per_vehicle=12,inventory_restarts=2,master_time_limit_seconds=8)
run('solver_valid_changed_inventory',data=d,cfg=cfg,solve=True,legal=True)
save(O/'controls-summary.json',{'cases':len(records),'all_assertions_passed':all(r['assertion_passed'] for r in records),'failures':[r['name'] for r in records if not r['assertion_passed']],'legal_cases':[r['name'] for r in records if r['expected']=='legal'],'records':[str((T/r['name']/'receipt.json').relative_to(O)) for r in records],'actual_sum_subprocess_seconds':sum(r['elapsed_seconds'] for r in records)})
