"""Actual paired CLI controls and unchanged full-coordinate checks for v2."""
from pathlib import Path
import json,csv,copy,subprocess,time,math
from validator import validate

E=Path(__file__).resolve().parents[1];OLD=E.parent/'execution';R=E.parents[4]
def readj(p):return json.loads(p.read_text(encoding='utf8'))
def writej(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def readrows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def writecsv(p,rs):
    with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def call(name,code,data,cfg,csvfile=None,single=False,out=None,method=None):
    if out is None:out=E/'checks/revision-controls'/f'{name}.json'
    cmd=['py','-3.12','-X','utf8','-B',str(code),'--data',str(data),'--config',str(cfg),'--out',str(out)]
    if csvfile is not None:cmd+=['--placements',str(csvfile)]
    if single:cmd+=['--single']
    if method:cmd+=['--method',method]
    started=time.perf_counter();p=subprocess.run(cmd,cwd=E,capture_output=True,text=True,encoding='utf8');record={'name':name,'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'elapsed_seconds':time.perf_counter()-started,'state':'completed','process_id':None}
    writej(E/'checks/revision-receipts'/f'{name}.json',record);return record

def main():
    control=E/'checks/revision-controls';control.mkdir(exist_ok=True);I=readj(E/'data/instance.json');C=readj(E/'configs/refined.json');data=E/'data/instance.json';cfg=E/'configs/refined.json'
    counterexample=R/'runs/R19/levels/L4/review/initial/NaN_coordinate.csv';base=readrows(counterexample);base[0]['x']='0.0';legal=control/'legal_pair.csv';writecsv(legal,base)
    original=call('original_v1_NaN',OLD/'code/validator.py',OLD/'data/instance.json',OLD/'configs/refined.json',counterexample,True);assert original['exit_code']==0 and readj(control/'original_v1_NaN.json')['valid']
    impossible=copy.deepcopy(I)
    for g in impossible['cargo']:g['quantity']=1 if g['id']=='G1' else 0
    impossible['cargo'][0]['dims']=[1001,1001,1001];impossiblefile=control/'impossible_1001.json';writej(impossiblefile,impossible)
    oldbad=call('original_v1_impossible',OLD/'code/solve.py',impossiblefile,cfg,out=control/'original_impossible',method='maxrects');assert oldbad['exit_code']!=0 and 'Traceback' in oldbad['stderr']
    controls=[]
    good=call('legal_pair',E/'code/validator.py',data,cfg,legal,True);assert good['exit_code']==0 and readj(control/'legal_pair.json')['valid'];controls.append({'name':'legal_pair','accepted':True,'exit_code':0})
    for field in ['x','y','z','l','w','h']:
        for label,value in [('NaN','NaN'),('positive_Inf','Infinity'),('negative_Inf','-Infinity')]:
            name='coordinate_'+field+'_'+label;p=control/(name+'.csv');rs=copy.deepcopy(base);rs[0][field]=value;writecsv(p,rs);r=call(name,E/'code/validator.py',data,cfg,p,True);j=readj(control/(name+'.json'));assert r['exit_code']==1 and not j['valid'] and any('invalid_numeric' in x for x in j['errors']);controls.append({'name':name,'rejected':True,'errors':j['errors'],'exit_code':r['exit_code']})
    for field,value in [('x',-1),('y',-1),('z',-1),('l',0),('w',-1),('h',0)]:
        name='coordinate_range_'+field;p=control/(name+'.csv');rs=copy.deepcopy(base);rs[0][field]=value;writecsv(p,rs);r=call(name,E/'code/validator.py',data,cfg,p,True);j=readj(control/(name+'.json'));assert r['exit_code']==1 and not j['valid'] and any('invalid_range' in x for x in j['errors']);controls.append({'name':name,'rejected':True,'errors':j['errors'],'exit_code':r['exit_code']})
    paths=[('cargo_length',('cargo',0,'dims',0)),('cargo_width',('cargo',0,'dims',1)),('cargo_height',('cargo',0,'dims',2)),('cargo_mass',('cargo',0,'mass')),('quantity',('cargo',0,'quantity')),('vehicle_length',('vehicles',0,'dims',0)),('payload',('vehicles',0,'capacity')),('cost',('vehicles',0,'cost'))]
    def assign(obj,path,value):
        for key in path[:-1]:obj=obj[key]
        obj[path[-1]]=value
    for field,path in paths:
        for label,value in [('NaN',float('nan')),('positive_Inf',float('inf')),('negative_Inf',float('-inf'))]:
            name='input_'+field+'_'+label;v=copy.deepcopy(I);assign(v,path,value);p=control/(name+'_input.json');writej(p,v)
            r=call(name,E/'code/solve.py',p,cfg,out=control/(name+'_out'),method='maxrects');j=readj(control/(name+'_out/failure.json'));assert r['exit_code']==2 and j['status']=='invalid_input' and 'Traceback' not in r['stderr'];assert not list((control/(name+'_out')).rglob('summary.json'));controls.append({'name':name,'rejected':True,'status':j['status'],'errors':j['errors'],'exit_code':r['exit_code']})
            # The receiving CLI independently invokes the same input gate before coordinate metrics.
            vr=call(name+'_receiver',E/'code/validator.py',p,cfg,legal,True);vj=readj(control/(name+'_receiver.json'));assert vr['exit_code']==1 and not vj['valid']
    for field,values in [('gap_cm',[-1,float('nan'),float('inf'),float('-inf')]),('pressure_kg_m2',[0,float('nan'),float('inf'),float('-inf')]),('tolerance_cm',[-1,float('nan'),float('inf'),float('-inf')])]:
        for k,value in enumerate(values):
            name=f'config_{field}_{k}';v=copy.deepcopy(C);v[field]=value;p=control/(name+'_config.json');writej(p,v);r=call(name,E/'code/validator.py',data,p,legal,True);j=readj(control/(name+'.json'));assert r['exit_code']==1 and not j['valid'];controls.append({'name':name,'rejected':True,'errors':j['errors'],'exit_code':r['exit_code']})
    for field,path,value in [('negative_mass',('cargo',0,'mass'),-1),('zero_length',('cargo',0,'dims',0),0),('negative_payload',('vehicles',0,'capacity'),-1),('zero_cost',('vehicles',0,'cost'),0),('negative_quantity',('cargo',0,'quantity'),-1),('fraction_quantity',('cargo',0,'quantity'),1.5)]:
        name='input_range_'+field;v=copy.deepcopy(I);assign(v,path,value);p=control/(name+'_input.json');writej(p,v);r=call(name,E/'code/solve.py',p,cfg,out=control/(name+'_out'),method='maxrects');j=readj(control/(name+'_out/failure.json'));assert r['exit_code']==2 and j['status']=='invalid_input';controls.append({'name':name,'rejected':True,'errors':j['errors'],'exit_code':r['exit_code']})
    bad=call('v2_impossible',E/'code/solve.py',impossiblefile,cfg,out=control/'v2_impossible',method='maxrects');failure=readj(control/'v2_impossible/failure.json');assert bad['exit_code']==3 and failure['status']=='infeasible_input' and '1001' in bad['stdout'] and 'Traceback' not in bad['stderr'];assert not list((control/'v2_impossible').rglob('summary.json'))
    # 12 official full outputs,4 selected singles and17 frozen parameter outputs: no optimization is repeated.
    full=[]
    for method in ['baseline_refined','classic_refined','improved_refined']:
        for name in ['Q1_fleet_T1','Q1_fleet_T2','Q2_min_vehicles','Q2_min_cost']:
            root=E/'results'/method/name;s=readj(root/'summary.json');ck=validate(I,C,readrows(root/'placements.csv'),True);assert ck['valid'],ck['errors']
            for key in ['truck_count','cost','volume_cm3','mass_kg','UV','UW']:assert math.isclose(ck[key],s[key],rel_tol=1e-9,abs_tol=1e-6)
            full.append({'root':root.relative_to(E).as_posix(),'valid':True,'truck_count':ck['truck_count'],'cost':ck['cost']})
    selected=readj(E/'results/selected.json')
    for vt,pps in readj(E/selected['single_root']/'pareto.json').items():
        for p in pps:
            root=E/selected['single_root']/p['scenario'];ck=validate(I,C,readrows(root/'placements.csv'),False);assert ck['valid'];full.append({'root':root.relative_to(E).as_posix(),'valid':True})
    for p in (E/'results/experiments').iterdir():
        if not (p/'summary.json').exists():continue
        s=readj(p/'summary.json');ck=validate(readj(p/'input.json'),s['config'],readrows(p/'placements.csv'),True);assert ck['valid'],(p,ck['errors']);full.append({'root':p.relative_to(E).as_posix(),'valid':True})
    for name,item in selected['scenarios'].items():
        r=call('full_'+name,E/'code/validator.py',data,cfg,E/item['root']/'placements.csv');assert r['exit_code']==0 and readj(control/('full_'+name+'.json'))['valid']
    result={'status':'author_revision_checks_passed_pending_informed_review','original_v1_NaN_false_acceptance_reproduced':original,'original_v1_impossible_traceback_retained':oldbad,'controls':controls,'v2_impossible_receipt':bad,'v2_impossible_failure':failure,'full_coordinate_groups':full,'group_count':len(full),'unchanged_geometry_and_objectives':True,'independent_review_status':'pending; original a4fail/a6partial not overwritten','no_nan_replacement_or_summary_on_invalid':True}
    writej(E/'checks/revision-checks.json',result);print({'controls':len(controls),'full_groups':len(full),'status':result['status']})
if __name__=='__main__':main()
