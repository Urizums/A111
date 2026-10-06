"""Conservative floor-only orthogonal packing heuristic for official R16 D inputs."""
from pathlib import Path
from itertools import permutations
from collections import Counter
import csv, json, time
from docx import Document

T0 = time.perf_counter()
HERE = Path(__file__).resolve().parent
R16 = HERE.parent
DOC = R16 / 'source/official_extracted/D_corrected/附件1.docx'
TRUCKS = {
    1: {'L':420, 'W':210, 'H':220, 'kg':6000, 'cost':450},
    2: {'L':680, 'W':245, 'H':250, 'kg':10000, 'cost':700},
}

doc = Document(DOC)
items=[]
for row in doc.tables[0].rows[1:]:
    code, kind, dims, mass, qty = [c.text.strip() for c in row.cells]
    a,b,c=map(int,dims.split('×'))
    items.append({'code':code,'kind':kind,'dims':[a,b,c],'kg':float(mass),'qty':int(qty)})

def poses(item, truck):
    a,b,c=item['dims']
    # Conservative interpretation: oriented pieces preserve the printed L/W/H.
    if item['code'] in ('G4','G5'):
        opts=[(a,b,c)]
    else:
        opts=list(set(permutations((a,b,c),3)))
    return sorted((p for p in opts if p[2] <= truck['H']-3), key=lambda p:(p[2],p[0]*p[1],p[0]))

def pack(kind, max_trucks=None):
    """Shelf floor packing. Every piece sits on floor: no unsupported stacking claim."""
    remaining=[]
    # FFD by minimum feasible footprint; deterministic tie break by code.
    for it in items:
        for j in range(it['qty']): remaining.append((it,j))
    remaining.sort(key=lambda z:(-max(p[0]*p[1] for p in poses(z[0],TRUCKS[kind])),z[0]['code'],z[1]))
    trucks=[]
    unplaced=[]
    for it,j in remaining:
        choices=poses(it,TRUCKS[kind]); placed=False
        for bi,bin_ in enumerate(trucks):
            # Existing shelves: shelf is (y,height,next_x). Each shelf has fixed height.
            for si,(y,sh,nextx) in enumerate(bin_['shelves']):
                for a,b,h in choices:
                    if h<=sh and nextx+a<=TRUCKS[kind]['L'] and y+b<=TRUCKS[kind]['W']:
                        bin_['shelves'][si]=(y,sh,nextx+a)
                        bin_['placements'].append((it,j,nextx,y,0,a,b,h))
                        bin_['kg']+=it['kg']; bin_['vol']+=a*b*h
                        placed=True; break
                if placed: break
            if placed: break
            # New shelf along width; choose the best feasible pose for this shelf.
            y=sum(s[1] for s in bin_['shelves'])
            for a,b,h in choices:
                if a<=TRUCKS[kind]['L'] and y+b<=TRUCKS[kind]['W']:
                    bin_['shelves'].append((y,b,a))
                    bin_['placements'].append((it,j,0,y,0,a,b,h))
                    bin_['kg']+=it['kg']; bin_['vol']+=a*b*h
                    placed=True; break
            if placed: break
        if not placed:
            if max_trucks is not None and len(trucks)>=max_trucks:
                unplaced.append((it,j)); continue
            bin_={'shelves':[],'placements':[],'kg':0.,'vol':0.}
            # first item must fit in a new truck
            for a,b,h in choices:
                if a<=TRUCKS[kind]['L'] and b<=TRUCKS[kind]['W']:
                    bin_['shelves']=[(0,b,a)]; bin_['placements']=[(it,j,0,0,0,a,b,h)]
                    bin_['kg']=it['kg']; bin_['vol']=a*b*h; placed=True; break
            if placed: trucks.append(bin_)
            else: unplaced.append((it,j))
    return trucks,unplaced

def summarize(bins,k):
    t=TRUCKS[k]
    return {'truck_type':k,'trucks':len(bins),'cost_yuan':len(bins)*t['cost'],
            'space_rate_pct':round(sum(b['vol'] for b in bins)/(len(bins)*t['L']*t['W']*t['H'])*100,4) if bins else 0,
            'payload_rate_pct':round(sum(b['kg'] for b in bins)/(len(bins)*t['kg'])*100,4) if bins else 0,
            'item_count':sum(len(b['placements']) for b in bins),
            'unplaced':0}

results={}; allbins={}
for k in (1,2):
    bins,un=pack(k); allbins[k]=bins
    results[f'all_type_{k}']=summarize(bins,k)
    results[f'all_type_{k}']['unplaced']=sum(it['qty'] for it,j in un)

# Mixed fleet: compare two reproducible extremes; no global optimality claim.
# Scenario minimum-truck heuristic: use type 2 until it fits all (proved here by run).
# Scenario cost heuristic: all type 2 because its floor area per yuan exceeds type 1.
# Both are retained as candidate plans, with type-1-only as a comparison.
results['mixed_min_truck_candidate']={'truck_type_1':0,'truck_type_2':results['all_type_2']['trucks'],
    'trucks':results['all_type_2']['trucks'],'cost_yuan':results['all_type_2']['cost_yuan'],
    'status':'type-2-only feasible candidate; not a mixed-integer optimum'}
results['mixed_min_cost_candidate']=dict(results['mixed_min_truck_candidate'])
results['mixed_min_cost_candidate']['status']='all-type-2 feasible candidate; no optimality proof; cost lower bound is ceil(total cargo kg / max capacity) only and weak'

# One-truck target trade-off candidates using legal pieces from the same dataset.
single={}
for k in (1,2):
    # Rank by volume for volume candidate; by mass for payload candidate, then retain bounded feasible packing.
    single[k]={}
    for objective in ('volume','mass'):
        seq=sorted(items,key=lambda x: (-(x['dims'][0]*x['dims'][1]*x['dims'][2] if objective=='volume' else x['kg']),x['code']))
        # Greedy first-fit into exactly one bin, preserving item stock counts.
        chosen=[]
        for it in seq:
            chosen.extend([it]*it['qty'])
        chosen.sort(key=lambda x: (-(x['dims'][0]*x['dims'][1]*x['dims'][2] if objective=='volume' else x['kg']),x['code']))
        # Reuse packer's ordering/placement with target count one via temporary supply cap is not implemented;
        # the fleet result serves as the verifiable multi-trip result. Single-truck candidates are explicitly pending.
        single[k][objective]={'status':'not computed; question-1 single-vehicle multiobjective candidate remains open'}
results['question1_single_truck']=single

out=HERE/'results.json'
out.write_text(json.dumps({'schema':'R16-solution-results/1','source':'official corrected Attachment 1','units':{'length':'cm','mass':'kg','cost':'yuan/dispatch'},'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
with (HERE/'placements.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['plan','truck_no','item_id','type','x_cm','y_cm','z_cm','pose_L_cm','pose_W_cm','pose_H_cm','kg'])
    for k,bins in allbins.items():
        for ti,b in enumerate(bins,1):
            for it,j,x,y,z,a,bb,h in b['placements']:
                w.writerow([f'all_type_{k}',ti,f'{it["code"]}-{j+1}',it['kind'],x,y,z,a,bb,h,it['kg']])
# Materialize per-truck checks from reported coordinates and conservative floor-only rule.
checks=[]
for k,bins in allbins.items():
    t=TRUCKS[k]
    for ti,b in enumerate(bins,1):
        ps=b['placements']; errors=[]
        if b['kg']>t['kg']+1e-9: errors.append('payload')
        for ix,p in enumerate(ps):
            it,j,x,y,z,a,bb,h=p
            if x+a>t['L'] or y+bb>t['W'] or h>t['H']-3 or z!=0: errors.append('boundary/safety')
            for q in ps[:ix]:
                _,_,xx,yy,zz,aa,bbb,hh=q
                if x<xx+aa and xx<x+a and y<yy+bbb and yy<y+bb: errors.append('overlap'); break
        checks.append({'type':k,'truck':ti,'pieces':len(ps),'kg':b['kg'],'errors':errors})
(HERE/'truck_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'results':results,'elapsed_cpu_s':round(time.perf_counter()-T0,3),'checks':len(checks),'failed_trucks':sum(bool(c['errors']) for c in checks)},ensure_ascii=False))
