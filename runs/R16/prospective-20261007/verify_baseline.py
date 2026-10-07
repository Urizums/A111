"""Independent raw-data receiving check for baseline.csv output."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, json
from docx import Document

HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'source'/'official_extracted'/'D_corrected'
raw=Document(SRC/'附件1.docx').tables[0]
products={}
for row in raw.rows[1:]:
    code,category,dims,mass,qty=[c.text.strip() for c in row.cells]
    products[code]={'category':category,'dims':tuple(map(int,dims.split('×'))),'kg':float(mass),'qty':int(qty)}
truckdata={1:(420,210,220,6000,450),2:(680,245,250,10000,700)}
plans=defaultdict(list)
with (HERE/'placements.csv').open(encoding='utf-8-sig',newline='') as f:
    for r in csv.DictReader(f): plans[(r['plan'],int(r['truck_no']))].append(r)
issues=[]; plan_result={}
for typ in (1,2):
    L,W,H,cap,cost=truckdata[typ]
    plan=f'all_type_{typ}'; keys=[k for k in plans if k[0]==plan]
    types=Counter(); vol=mass=0
    per_truck=[]
    for (pname,no),boxes in sorted((k,v) for k,v in plans.items() if k[0]==plan):
        tkg=0
        for i,b in enumerate(boxes):
            code=b['code']; rawp=products.get(code)
            if rawp is None:
                issues.append({'plan':plan,'truck':no,'issue':'unknown_code','item':code}); continue
            types[code]+=1
            x,y,z,a,bw,h=[int(b[s]) for s in ('x_cm','y_cm','z_cm','pose_L_cm','pose_W_cm','pose_H_cm')]
            kg=float(b['unit_kg']); tkg+=kg; mass+=kg; vol+=a*bw*h
            if kg!=rawp['kg']: issues.append({'plan':plan,'truck':no,'item':b['item_id'],'issue':'unit_mass_mismatch'})
            if min(x,y,z)<0: issues.append({'plan':plan,'truck':no,'issue':'negative_coordinate'})
            if x+a>L or y+bw>W or z+h>H-3: issues.append({'plan':plan,'truck':no,'item':b['item_id'],'issue':'boundary_or_3cm_clearance'})
            if z!=0: issues.append({'plan':plan,'truck':no,'item':b['item_id'],'issue':'not_floor_supported'})
            dims=rawp['dims']; pose=(a,bw,h)
            if code in ('G4','G5') and pose!=dims: issues.append({'plan':plan,'truck':no,'item':b['item_id'],'issue':'directional_orientation'})
            if code not in ('G4','G5') and sorted(pose)!=sorted(dims): issues.append({'plan':plan,'truck':no,'item':b['item_id'],'issue':'pose_not_permutation'})
            for q in boxes[:i]:
                qx,qy,qz,qa,qb,qh=[int(q[s]) for s in ('x_cm','y_cm','z_cm','pose_L_cm','pose_W_cm','pose_H_cm')]
                if x<qx+qa and qx<x+a and y<qy+qb and qy<y+bw and z<qz+qh and qz<z+h:
                    issues.append({'plan':plan,'truck':no,'items':[b['item_id'],q['item_id']],'issue':'3d_intersection'}); break
        if tkg>cap+1e-8: issues.append({'plan':plan,'truck':no,'issue':'payload_over','kg':tkg,'capacity':cap})
        per_truck.append({'truck':no,'pieces':len(boxes),'kg':tkg,'payload_pct':100*tkg/cap,
            'space_pct':100*sum(int(b['pose_L_cm'])*int(b['pose_W_cm'])*int(b['pose_H_cm']) for b in boxes)/(L*W*H)})
    for code,p in products.items():
        if types[code]!=p['qty']: issues.append({'plan':plan,'code':code,'issue':'quantity','expected':p['qty'],'actual':types[code]})
    n=len(keys)
    plan_result[plan]={'trucks':n,'pieces':sum(types.values()),'mass_kg':mass,'volume_cm3':vol,
        'cost_yuan':n*cost,'mean_space_pct':sum(t['space_pct'] for t in per_truck)/n if n else 0,
        'mean_payload_pct':sum(t['payload_pct'] for t in per_truck)/n if n else 0,
        'max_truck_payload_kg':max((t['kg'] for t in per_truck),default=0),
        'truck_rows':per_truck}
result={'checker':'independent coordinate reader + raw DOCX quantity/dimension reconstruction','plans':plan_result,'issue_count':len(issues),'issues':issues}
(HERE/'independent-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'issue_count':len(issues),'plans':{k:{x:v for x,v in z.items() if x!='truck_rows'} for k,z in plan_result.items()}},ensure_ascii=False))
