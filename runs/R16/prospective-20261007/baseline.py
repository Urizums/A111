"""Raw Attachment 1 floor-only shelf baseline and separate coordinate audit."""
from pathlib import Path
from itertools import permutations
from collections import Counter
import csv, json, time
from docx import Document

T0 = time.perf_counter()
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[0] / 'source' / 'official_extracted' / 'D_corrected'
ATT1 = SRC / '附件1.docx'
TRUCKS = {
    1: {'L':420, 'W':210, 'H':220, 'capacity_kg':6000, 'cost_yuan_trip':450},
    2: {'L':680, 'W':245, 'H':250, 'capacity_kg':10000, 'cost_yuan_trip':700},
}

doc = Document(ATT1)
products=[]
for row in doc.tables[0].rows[1:]:
    code, category, dims_text, mass_text, qty_text = [c.text.strip() for c in row.cells]
    dims=tuple(int(v) for v in dims_text.split('×'))
    products.append({'code':code,'category':category,'dims_cm':dims,
                     'unit_kg':float(mass_text),'qty':int(qty_text)})

def allowed_poses(prod, truck):
    dims=prod['dims_cm']
    # Attachment 1 defines directional items as exactly one posture; retain its L/W/H.
    options={dims} if prod['code'] in ('G4','G5') else set(permutations(dims))
    return sorted((q for q in options if q[2] <= truck['H']-3),
                  key=lambda q:(q[1],-q[0],q[2]))

def build_fleet(type_id):
    tr=TRUCKS[type_id]
    pieces=[(p,serial) for p in products for serial in range(1,p['qty']+1)]
    # Deterministic first-fit decreasing by maximum possible footprint.
    pieces.sort(key=lambda q:(-max(a*b for a,b,h in allowed_poses(q[0],tr)),q[0]['code'],q[1]))
    bins=[]
    for prod,serial in pieces:
        poses=allowed_poses(prod,tr)
        inserted=False
        for bin_ in bins:
            if bin_['mass_kg']+prod['unit_kg'] > tr['capacity_kg']:
                continue
            # A shelf fixes its y-depth; boxes can occupy only its remaining x-length.
            for shelf in bin_['shelves']:
                for a,b,h in poses:
                    if b<=shelf['depth'] and shelf['next_x']+a<=tr['L']:
                        x,y=shelf['next_x'],shelf['y']
                        shelf['next_x']+=a
                        bin_['pieces'].append({'item_id':f"{prod['code']}-{serial}",'code':prod['code'],
                            'category':prod['category'],'x_cm':x,'y_cm':y,'z_cm':0,
                            'pose_L_cm':a,'pose_W_cm':b,'pose_H_cm':h,'unit_kg':prod['unit_kg']})
                        bin_['mass_kg']+=prod['unit_kg']; inserted=True; break
                if inserted: break
            if inserted: break
            used_y=sum(s['depth'] for s in bin_['shelves'])
            for a,b,h in poses:
                if a<=tr['L'] and used_y+b<=tr['W']:
                    bin_['shelves'].append({'y':used_y,'depth':b,'next_x':a})
                    bin_['pieces'].append({'item_id':f"{prod['code']}-{serial}",'code':prod['code'],
                        'category':prod['category'],'x_cm':0,'y_cm':used_y,'z_cm':0,
                        'pose_L_cm':a,'pose_W_cm':b,'pose_H_cm':h,'unit_kg':prod['unit_kg']})
                    bin_['mass_kg']+=prod['unit_kg']; inserted=True; break
            if inserted: break
        if not inserted:
            new={'shelves':[],'pieces':[],'mass_kg':0.0}
            for a,b,h in poses:
                if a<=tr['L'] and b<=tr['W'] and prod['unit_kg']<=tr['capacity_kg']:
                    new['shelves']=[{'y':0,'depth':b,'next_x':a}]
                    new['pieces']=[{'item_id':f"{prod['code']}-{serial}",'code':prod['code'],
                        'category':prod['category'],'x_cm':0,'y_cm':0,'z_cm':0,
                        'pose_L_cm':a,'pose_W_cm':b,'pose_H_cm':h,'unit_kg':prod['unit_kg']}]
                    new['mass_kg']=prod['unit_kg']; inserted=True; break
            if inserted: bins.append(new)
            else: raise RuntimeError(f"No floor pose fits {prod['code']} in truck {type_id}")
    return bins

def audit_coordinates(type_id,bins):
    tr=TRUCKS[type_id]; issues=[]; totals=Counter(); seen=Counter(); truck_rows=[]
    for n,bin_ in enumerate(bins,1):
        ps=bin_['pieces']; mass=sum(p['unit_kg'] for p in ps)
        if mass>tr['capacity_kg']+1e-9: issues.append({'truck':n,'issue':'payload'})
        for i,p in enumerate(ps):
            totals[p['code']]+=p['pose_L_cm']*p['pose_W_cm']*p['pose_H_cm']
            seen[p['code']]+=1
            if p['x_cm']<0 or p['y_cm']<0 or p['z_cm']<0 or p['x_cm']+p['pose_L_cm']>tr['L'] or p['y_cm']+p['pose_W_cm']>tr['W'] or p['z_cm']+p['pose_H_cm']>tr['H']-3:
                issues.append({'truck':n,'item':p['item_id'],'issue':'boundary_or_3cm_clearance'})
            if p['z_cm']!=0:
                issues.append({'truck':n,'item':p['item_id'],'issue':'baseline_requires_floor_only'})
            if p['code'] in ('G4','G5') and (p['pose_L_cm'],p['pose_W_cm'],p['pose_H_cm']) != next(x['dims_cm'] for x in products if x['code']==p['code']):
                issues.append({'truck':n,'item':p['item_id'],'issue':'directional_pose'})
            for q in ps[:i]:
                ox=p['x_cm']<q['x_cm']+q['pose_L_cm'] and q['x_cm']<p['x_cm']+p['pose_L_cm']
                oy=p['y_cm']<q['y_cm']+q['pose_W_cm'] and q['y_cm']<p['y_cm']+p['pose_W_cm']
                oz=p['z_cm']<q['z_cm']+q['pose_H_cm'] and q['z_cm']<p['z_cm']+p['pose_H_cm']
                if ox and oy and oz:
                    issues.append({'truck':n,'items':[p['item_id'],q['item_id']],'issue':'overlap'}); break
        truck_rows.append({'truck':n,'pieces':len(ps),'mass_kg':mass,
            'space_utilization_pct':100*sum(p['pose_L_cm']*p['pose_W_cm']*p['pose_H_cm'] for p in ps)/(tr['L']*tr['W']*tr['H']),
            'payload_utilization_pct':100*mass/tr['capacity_kg']})
    expected={p['code']:p['qty'] for p in products}
    for code,n in expected.items():
        if seen[code]!=n: issues.append({'item_type':code,'expected':n,'actual':seen[code],'issue':'count'})
    return {'truck_rows':truck_rows,'issues':issues,'items_seen':dict(seen),'expected_items':expected}

all_results={}; placements=[]; all_audits={}
for type_id in (1,2):
    fleet=build_fleet(type_id); audit=audit_coordinates(type_id,fleet); all_audits[str(type_id)]=audit
    tr=TRUCKS[type_id]; total_vol=sum(sum(p['pose_L_cm']*p['pose_W_cm']*p['pose_H_cm'] for p in b['pieces']) for b in fleet)
    total_mass=sum(b['mass_kg'] for b in fleet)
    all_results[str(type_id)]={'truck_type':type_id,'truck_count':len(fleet),'cost_yuan':len(fleet)*tr['cost_yuan_trip'],
        'pieces':sum(len(b['pieces']) for b in fleet),'cargo_volume_cm3':total_vol,'cargo_mass_kg':total_mass,
        'aggregate_space_utilization_pct':100*total_vol/(len(fleet)*tr['L']*tr['W']*tr['H']),
        'aggregate_payload_utilization_pct':100*total_mass/(len(fleet)*tr['capacity_kg']),
        'checker_issues':len(audit['issues'])}
    for no,b in enumerate(fleet,1):
        for p in b['pieces']:
            placements.append({'plan':f'all_type_{type_id}','truck_no':no,**p})

with (HERE/'placements.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['plan','truck_no','item_id','code','category','x_cm','y_cm','z_cm','pose_L_cm','pose_W_cm','pose_H_cm','unit_kg']
    writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(placements)
(HERE/'results.json').write_text(json.dumps({'schema':'R16-02-floor-baseline/1','source':'official corrected Attachment 1.docx','units':{'length':'cm','mass':'kg','cost':'yuan/trip'},'assumptions':['all items remain at z=0; no stacking','G4 and G5 stay in printed L/W/H posture','other rigid boxes may use any axis permutation','shelf rows are fixed-depth; packing is a heuristic, not an optimum'], 'plans':all_results},ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'constraint-audit.json').write_text(json.dumps(all_audits,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'elapsed_s':round(time.perf_counter()-T0,3),'plans':all_results,'audit_issue_counts':{k:len(v['issues']) for k,v in all_audits.items()}},ensure_ascii=False))
