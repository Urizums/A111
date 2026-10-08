"""Choose verified incumbents by original objective, combine finite Pareto archive."""
from pathlib import Path
import json,csv,shutil
from validator import validate

def main():
    E=Path(__file__).resolve().parents[1];I=json.loads((E/'data/instance.json').read_text(encoding='utf8'));C=json.loads((E/'configs/refined.json').read_text(encoding='utf8'));methods=['baseline_refined','classic_refined','improved_refined'];runtime={m:json.loads((E/'results'/m/'run_summary.json').read_text(encoding='utf8'))['elapsed_seconds'] for m in methods};chosen={}
    for name in ['Q1_fleet_T1','Q1_fleet_T2','Q2_min_vehicles','Q2_min_cost']:
        pool=[]
        for m in methods:
            root=E/'results'/m/name;s=json.loads((root/'summary.json').read_text(encoding='utf8'));rows=list(csv.DictReader((root/'placements.csv').open(encoding='utf-8-sig')));ck=validate(I,C,rows,True);assert ck['valid'],ck['errors'];pool.append((m,root,s,ck))
        key=lambda x: (x[2]['cost'],x[2]['truck_count'],runtime[x[0]]) if name=='Q2_min_cost' else (x[2]['truck_count'],x[2]['cost'],runtime[x[0]])
        m,root,s,ck=min(pool,key=key);chosen[name]={'root':root.relative_to(E).as_posix(),'method':m,'truck_count':ck['truck_count'],'cost':ck['cost'],'valid':True,'source_of_choice':'minimize requested primary objective, then secondary, then full-route runtime; author recheck'}
    single=E/'results/selected_single';single.mkdir(exist_ok=True);archive={};records=[]
    for vt in ['T1','T2']:
        allpts=[]
        for m in methods:
            pp=json.loads((E/'results'/m/'pareto.json').read_text(encoding='utf8'))[vt]
            for p in pp:allpts.append({**p,'method':m,'source_root':E/'results'/m/p['scenario']})
        unique={}
        for p in allpts:unique.setdefault(tuple(p['counts']),p)
        pts=list(unique.values());front=[p for p in pts if not any(pp['UV']>=p['UV'] and pp['UW']>=p['UW'] and (pp['UV']>p['UV'] or pp['UW']>p['UW']) for pp in pts)];archive[vt]=[]
        for index,p in enumerate(sorted(front,key=lambda p:p['UV'])):
            name=f'{vt}_P{index:02d}';target=single/name;target.mkdir(exist_ok=True)
            for fn in ['placements.csv','support_loads.csv','summary.json']:shutil.copyfile(p['source_root']/fn,target/fn)
            rows=list(csv.DictReader((target/'placements.csv').open(encoding='utf-8-sig')));check=validate(I,C,rows,False);assert check['valid'],check['errors']
            archive[vt].append({'scenario':name,'counts':p['counts'],'UV':check['UV'],'UW':check['UW'],'source':p['source_root'].relative_to(E).as_posix(),'method':p['method']});records.append({'scenario':name,'valid':True,'errors':check['errors']})
    (single/'pareto.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2),encoding='utf8')
    selected={'scenarios':chosen,'single_root':single.relative_to(E).as_posix(),'rule':'best checked official candidate; finite merged archive, no complete-frontier or global-optimum claim','created_by':'/root/r19_l4_executor'}
    (E/'results/selected.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf8');(E/'checks/selected_recheck.json').write_text(json.dumps({'full':chosen,'single':records,'independent_acceptance':False},ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(selected,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
