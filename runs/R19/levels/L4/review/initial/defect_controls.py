from pathlib import Path
import json,csv,subprocess,copy,time
from independent_checks import validate as independent
OUT=Path(__file__).resolve().parent;C=OUT/'consumer'
def main():
    data=json.loads((C/'data/raw_rebuilt.json').read_text(encoding='utf-8'));cat={g['id']:{'dims':g['dims'],'mass':g['mass'],'quantity':g['quantity'],'class':'directed' if g['class']=='oriented' else g['class']} for g in data['cargo']}
    source=list(csv.DictReader((C/'results/selected_single/T1_P01/placements.csv').open(encoding='utf-8-sig',newline='')))
    row=next(r for r in source if float(r['z'])==0);row=dict(row);row['support_ids']='FLOOR'
    variants={'valid_single_real_row':[row],'NaN_coordinate':[dict(row,x='NaN')],
              'height_gap_violation':[dict(row,z='210')],
              'positive_overlap':[row,dict(row,item_id='G1-0002',x=str(float(row['x'])+1))]}
    results=[]
    for name,rows in variants.items():
        inp=OUT/(name+'.csv');out=OUT/(name+'-author-check.json')
        with inp.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerows(rows)
        args=['py','-3.12','-X','utf8','-B','code/validator.py','--data','data/raw_rebuilt.json','--config','configs/refined.json','--placements',str(inp),'--out',str(out),'--single']
        start=time.perf_counter();p=subprocess.run(args,cwd=C,capture_output=True,text=True,encoding='utf-8')
        observed=json.loads(out.read_text(encoding='utf-8'))
        tv=data['vehicles'][0];truck={'L':tv['dims'][0],'W':tv['dims'][1],'H':tv['dims'][2],'capacity':tv['capacity'],'cost':tv['cost']}
        items=[{'id':r['item_id'],'type':r['cargo_type'],'mass':cat[r['cargo_type']]['mass'],**{k:float(r[k]) for k in ['x','y','z','l','w','h']}} for r in rows]
        ir=independent(truck,items,cat)
        results.append({'name':name,'command':args,'exit_code':p.returncode,'elapsed_seconds':time.perf_counter()-start,
                       'stdout':p.stdout,'stderr':p.stderr,'author_valid':observed['valid'],'author_errors':observed['errors'],
                       'independent_valid':ir['valid'],'independent_errors':ir['errors']})
    (OUT/'defect-controls.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
