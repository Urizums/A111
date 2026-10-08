import csv,json,copy,subprocess,sys,time,datetime
from pathlib import Path
from solver import E,instance,save
from checker import check,validate_dir
base=E/'smoke/valid';cfg=json.loads((base/'config.json').read_text(encoding='utf-8'));data=cfg['instance'];rows=list(csv.DictReader((base/'placements.csv').open(encoding='utf-8-sig')));reports=[]
def test(name,r,rule,dd=None):
 result=check(r,dd or data,cfg,'Q1-F1');assert not result['passed'] and any(e['rule']==rule for e in result['errors']),(name,result);save(E/f'boundary_tests/{name}/validation.json',result);save(E/f'boundary_tests/{name}/placements.json',r);reports.append({'name':name,'rejected':True,'required_rule':rule})
r=copy.deepcopy(rows);r[1]['item_id']=r[0]['item_id'];test('duplicate_id',r,'unique_id')
r=copy.deepcopy(rows);r[1].update({k:r[0][k] for k in ['x_cm','y_cm','z_cm']});test('overlap',r,'nonoverlap')
r=copy.deepcopy(rows);i=next(i for i,x in enumerate(r) if x['cargo_type']=='G4');r[i].update(orientation='yxz',dx_cm=60,dy_cm=80);test('directional_orientation',r,'directional_orientation')
r=copy.deepcopy(rows);i=next(i for i,x in enumerate(r) if x['support_ids']);r[i]['z_cm']=float(r[i]['z_cm'])+1;test('floating',r,'single_full_support')
r=copy.deepcopy(rows);r[0]['x_cm']='inf';test('nonfinite',r,'finite_positive_geometry')
d=copy.deepcopy(data)
for c in d['cargo']:c['quantity']=2 if c['cargo_type']=='G3' else 0
r=[{'task_id':'Q1-F1','vehicle_id':'V001','vehicle_type':'T1','item_id':f'G3-{i+1:04d}','cargo_type':'G3','x_cm':0,'y_cm':0,'z_cm':i*40,'dx_cm':70,'dy_cm':50,'dz_cm':40,'orientation':'xyz','support_ids':'' if i==0 else 'G3-0001'} for i in range(2)];test('fragile_bears_load',r,'nothing_above_fragile',d)
# Run actual external program calls on general user-supplied inputs.
calls=[];valid=instance()
for c in valid['cargo']:c['quantity']=12 if c['cargo_type']=='G1' else 0
invalid=copy.deepcopy(valid);invalid['cargo'][0]['l_cm']=-1
unfit=copy.deepcopy(valid);unfit['cargo'][0].update(l_cm=9999,w_cm=9999,h_cm=9999)
for name,dd,expected in [('generic_valid',valid,0),('invalid_dimensions',invalid,2),('unfit_item',unfit,2)]:
 p=E/f'boundary_tests/{name}/input.json';save(p,dd);cmd=[sys.executable,'-X','utf8','-B',str(E/'src/solver.py'),'--task','Q1-F1','--input',str(p),'--out',str(p.parent/'plan')];started=datetime.datetime.now(datetime.UTC).isoformat();t=time.perf_counter();proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8');stdout,stderr=proc.communicate(timeout=120);assert proc.returncode==expected
 if expected==0:assert validate_dir(p.parent/'plan')['passed']
 else:assert json.loads(stdout)['state']=='failed'
 calls.append({'name':name,'argv':cmd,'pid':proc.pid,'start_utc':started,'elapsed_seconds':time.perf_counter()-t,'returncode':proc.returncode,'stdout':stdout,'stderr':stderr,'status':'terminated normally','expected_status_verified':True})
save(E/'boundary_tests/summary.json',{'coordinate_negative_tests':reports,'actual_cli_calls':calls,'passed':True,'scope':'targeted receiving boundary checks, not global correctness proof'});print('boundary tests passed',len(reports),'negative geometries and',len(calls),'actual CLI subprocesses')
