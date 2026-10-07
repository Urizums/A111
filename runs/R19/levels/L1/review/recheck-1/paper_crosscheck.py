from independent_audit import OUT,EXEC,raw_config
import json,math,csv,ast,re
md=(EXEC/'paper/paper.md').read_text(encoding='utf-8'); lines=md.splitlines(); tables=[];buf=[]
for n,line in enumerate(lines+[''],1):
    if line.startswith('|'):buf.append((n,[x.strip() for x in line.strip('|').split('|')]))
    elif buf:
        tables.append({'line':buf[0][0],'header':buf[0][1],'rows':[x[1] for x in buf[2:]]});buf=[]
audit=json.loads((OUT/'frozen-final-independent-audit.json').read_text(encoding='utf-8')); own={r['task']:r for r in audit['reports']}; cfg=raw_config();checks=[]
def table(header):return next(t for t in tables if t['header']==header)
def compare(label,actual,expected,line):
    checks.append({'check':label,'paper_line':line,'matches':actual==expected,'actual':actual if actual!=expected else None,'expected':expected if actual!=expected else None})
def pct(n):return f'{100*n:.2f}%'
labels=['问题1：仅车型1','问题1：仅车型2','问题2：最少车','问题2：最低成本'];names=['fixed_T1','fixed_T2','mixed_count','mixed_cost']
t=table(['任务','车型1/辆','车型2/辆','总车数','成本/元','满容率','满载率']);expected=[]
for lab,name in zip(labels,names):
    m=own[name]['metrics'];expected.append([lab,str(m['vehicle_counts'].get('T1',0)),str(m['vehicle_counts'].get('T2',0)),str(m['vehicles']),f'{m["cost"]:g}',pct(m['volume_rate']),pct(m['load_rate'])])
compare('all4 primary fleet answers',t['rows'],expected,t['line'])
fleettables=[t for t in tables if t['header']==['车号','G1','G2','G3','G4','G5','满容率','满载率']]
for name,t in zip(['fixed_T1','fixed_T2'],fleettables):
    expected=[[r['truck_id'],*[str(r['counts'].get('G'+str(k),0)) for k in range(1,6)],pct(r['volume_rate']),pct(r['load_rate'])] for r in own[name]['trucks']]
    compare(name+' every truck counts/rates',t['rows'],expected,t['line'])
t=table(['车型','候选','G1','G2','G3','G4','G5','质量/kg','满容率','满载率']);expected=[]
for name,vid,pid in [('single_T1_0','T1','P1'),('single_T1_1','T1','P2'),('single_T2_0','T2','P1')]:
    r=own[name];m=r['metrics'];expected.append([vid,pid,*[str(r['counts'].get('G'+str(k),0)) for k in range(1,6)],f'{m["weight_kg"]:g}',pct(m['volume_rate']),pct(m['load_rate'])])
compare('all single candidates counts/weights/two objectives',t['rows'],expected,t['line'])
t=table(['情景','最少车/辆','该方案成本/元','成本候选车数','成本/元','满容率','满载率','秒']); exps=json.loads((OUT/'independent-experiment-audit.json').read_text(encoding='utf-8'))['reports'];expected=[]
for r in exps:
    name=r['scenario']; ownrows={x['task']:x['metrics'] for x in r['layout_reports']};n=ownrows[name+'-count'];c=ownrows[name+'-cost'];reported=json.loads((EXEC/f'results/sensitivity/{name}.json').read_text(encoding='utf-8'))
    expected.append([name,str(n['vehicles']),f'{n["cost"]:g}',str(c['vehicles']),f'{c["cost"]:g}',pct(c['volume_rate']),pct(c['load_rate']),f'{reported["seconds"]:.2f}'])
compare('all32 scenario numerical rows; historical time sourced not independently timed',t['rows'],expected,t['line'])
t=table(['车型','货物ID','x','y','z','dx','dy','dz','轴置换']);expected=[]
for vid in ['T1','T2']:
    d=json.loads((EXEC/f'results/final/fixed_{vid}.json').read_text(encoding='utf-8'))
    for i in d['fleet'][0]['items'][:5]:expected.append([vid,i['item_id'],*[str(i[k]) for k in ['x','y','z','dx','dy','dz']],str(i['orientation'])])
compare('representative coordinate rows',t['rows'],expected,t['line'])
t=table(['车型','内尺寸/cm','有效高度/cm','载重/kg','趟费用/元','原容积/m³','可用容积/m³']);expected=[]
for v in cfg['vehicles']:expected.append([v['id'],'×'.join(f'{x:g}' for x in v['dims']),f'{v["dims"][2]-3:g}',f'{v["payload"]:g}',f'{v["cost"]:g}',f'{math.prod(v["dims"])/1e6:.4f}',f'{v["dims"][0]*v["dims"][1]*(v["dims"][2]-3)/1e6:.4f}'])
compare('raw vehicle dimensions/capacities/costs',t['rows'],expected,t['line'])
t=table(['货号','类别','长×宽×高/cm','单重/kg','数量/件','总体积/m³','密度/kg·m⁻³']);expected=[]
for c in cfg['cargo']:expected.append([c['id'],{'standard':'标准','fragile':'易碎','directional':'定向'}[c['category']],'×'.join(f'{x:g}' for x in c['dims']),f'{c["weight"]:g}',str(c['quantity']),f'{math.prod(c["dims"])*c["quantity"]/1e6:.2f}',f'{c["weight"]/(math.prod(c["dims"])/1e6):.2f}'])
compare('raw5 cargo fields/volumes/densities',t['rows'],expected,t['line'])
# Actual CSV/JSON interfaces for all3000 placements in each full task.
for name in names:
    d=json.loads((EXEC/f'results/final/{name}.json').read_text(encoding='utf-8'));expected=[{**i,'vehicle_type':tr['vehicle_type']} for tr in d['fleet'] for i in tr['items']]
    with (EXEC/f'results/final/{name}_placements.csv').open(encoding='utf-8-sig',newline='') as f:actual=list(csv.DictReader(f))
    match=len(actual)==len(expected)
    for a,e in zip(actual,expected):
        for k in a:
            val=ast.literal_eval(a[k]) if k=='orientation' else float(a[k]) if k in ['x','y','z','dx','dy','dz','weight'] else a[k]
            if val!=e[k]:match=False
    checks.append({'check':name+' actual CSV equals audited JSON','matches':match,'row_count':len(actual)})
# Figure source pressure distribution and Pareto values compared to own computation.
author=json.loads((EXEC/'review/full_check.json').read_text(encoding='utf-8'));pressure_checks=[]
for name in names:
    by={r['truck_id']:r for r in own[name]['trucks']}
    for tr in author[name]['trucks']:
        pressure_checks.append(abs(tr['max_local_pressure_kg_m2']-by[tr['truck_id']]['max_local_pressure_kg_m2'])<1e-8 and abs(tr['min_top_clearance_cm']-by[tr['truck_id']]['minimum_top_clearance_cm'])<1e-8)
checks.append({'check':'bearing figure source all vehicle pressures independently match','matches':all(pressure_checks)})
with (EXEC/'figures/pareto_source.csv').open(encoding='utf-8-sig',newline='') as f:pts=list(csv.DictReader(f))
for name,pt in zip(['single_T1_0','single_T1_1','single_T2_0'],pts):
    checks.append({'check':'pareto source '+name,'matches':all(abs(float(pt[k])-own[name]['metrics'][k])<1e-9 for k in ['volume_rate','load_rate','weight_kg','volume_cm3'])})
eps=json.loads((EXEC/'results/final/epsilon_scan.json').read_text(encoding='utf-8'));epschecks=[]
for row in eps:
    candidates=[r['metrics'] for k,r in own.items() if k.startswith('single_'+row['vehicle'])];eligible=[m for m in candidates if m['volume_rate']>=row['epsilon_volume_rate']-1e-9]
    best=max(eligible,key=lambda m:(m['load_rate'],m['volume_rate'])) if eligible else None
    epschecks.append(row['searched_pool_feasible']==bool(best) and (best is None or (abs(row['chosen_volume_rate']-best['volume_rate'])<1e-9 and abs(row['chosen_load_rate']-best['load_rate'])<1e-9)))
checks.append({'check':'epsilon finite candidate scan','matches':all(epschecks),'rows':len(epschecks)})
report={'all_checks_match':all(r['matches'] for r in checks),'checks':checks,'pdf_pages_visually_reviewed':16,'pdf_visual_scope':'own full-page rendering plus all16-page contact layouts; key formula/table/figure pages further viewed individually','text_scope':'paper.md complete read; numeric summary/primary/scenario/truck/coordinate/raw tables checked above','limits':['historical elapsed times sourced to output records and code timing range, not exact independent repetition','figure visuals inspected and source arrays checked; no image pixel comparison required for semantic fidelity','original global optimum remains unknown; finite pool proof verified separately']}
(OUT/'paper-crosscheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'all_checks_match':report['all_checks_match'],'check_count':len(checks),'mismatches':[r for r in checks if not r['matches']]},ensure_ascii=False,indent=2))
