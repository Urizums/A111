from pathlib import Path
from math import prod,ceil,floor
import json,csv,re
from openpyxl import load_workbook
OUT=Path(__file__).resolve().parent;ROOT=Path(__file__).resolve().parents[6];E=ROOT/'runs/R19/levels/L4/execution'
def main():
    c=json.loads((OUT/'source-contract.json').read_text(encoding='utf-8'));vol=sum(prod(g['dims_cm'])*g['quantity'] for g in c['cargo']);mass=sum(g['mass_kg']*g['quantity'] for g in c['cargo'])
    singles=[max(ceil(vol/prod(v['dims_cm'])),ceil(mass/v['capacity_kg'])) for v in c['vehicles']]
    upper=singles[0]*c['vehicles'][0]['cost_per_trip_yuan'];maxn=floor(upper/min(v['cost_per_trip_yuan'] for v in c['vehicles']))+1
    combos=[(a+b,a*c['vehicles'][0]['cost_per_trip_yuan']+b*c['vehicles'][1]['cost_per_trip_yuan'],a,b)
        for a in range(maxn+1) for b in range(maxn+1) if a*prod(c['vehicles'][0]['dims_cm'])+b*prod(c['vehicles'][1]['dims_cm'])>=vol and a*c['vehicles'][0]['capacity_kg']+b*c['vehicles'][1]['capacity_kg']>=mass]
    density=max(g['mass_kg']/(prod(g['dims_cm'])/1e6) for g in c['cargo'])
    bound={'physical_volume_m3':vol/1e6,'mass_kg':mass,'single_vehicle_count_lower_bounds':singles,
           'mixed_vehicle_count_lower_bound':min(x[0] for x in combos),'mixed_cost_lower_bound':min(x[1] for x in combos),
           'enumeration_scope':'all candidate relaxed combos that could improve known relaxed all-T1 feasible cost upper bound; not packing',
           'density_kg_m3':density,'UW_upper_bounds':[density*(v['dims_cm'][0]*v['dims_cm'][1]*(v['dims_cm'][2]-3)/1e6)/v['capacity_kg'] for v in c['vehicles']]}
    w=load_workbook(ROOT/'runs/R19/inputs/raw/附件2：验证数据集.xlsx',data_only=False);s=w['车型尺寸'];expected={}
    for p in c['attachment2_products']:
        dimensions=[p['measurements'][f'{col}{p["row"]}']['interval_cm'] for col in 'CEG']
        for r in range(4,12):
            vehicle=s[f'A{r}'].value;dv=[]
            for col in 'BCD':
                nums=[float(x)*100 for x in re.findall(r'\d+(?:\.\d+)?',str(s[f'{col}{r}'].value))];dv.append([min(nums),max(nums)])
            conservative=[floor((d[0]-(3 if i==2 else 0))/dimensions[i][1]) for i,d in enumerate(dv)]
            optimistic=[floor((d[1]-(3 if i==2 else 0))/dimensions[i][0]) for i,d in enumerate(dv)]
            expected[(p['product'],vehicle)]={'conservative':prod(conservative),'optimistic':prod(optimistic),'axes_min':conservative,'axes_max':optimistic}
    w.close();actual=list(csv.DictReader((E/'results/attachment2_geometry.csv').open(encoding='utf-8-sig',newline='')));geometry=[]
    for r in actual:
        x=expected[(r['product'],r['vehicle'])]
        geometry.append({'product':r['product'],'vehicle':r['vehicle'],'independent':x,'reported':r,
            'match':int(r['conservative_grid_count'])==x['conservative'] and int(r['optimistic_grid_count'])==x['optimistic'] and json.loads(r['conservative_nx_ny_nz'])==x['axes_min'] and json.loads(r['optimistic_nx_ny_nz'])==x['axes_max']})
    coordinates=json.loads((OUT/'coordinate-review.json').read_text(encoding='utf-8'));byroot={r['path'].replace('\\','/'):r for r in coordinates['results']}
    paper=(E/'paper/paper.md').read_text(encoding='utf-8');report=(E/'paper/enterprise_report.md').read_text(encoding='utf-8')
    trace=[]
    selected=json.loads((E/'results/selected.json').read_text(encoding='utf-8'))
    for key,entry in selected['scenarios'].items():
        root='runs/R19/levels/L4/execution/'+entry['root'];m=byroot[root]['metrics'];ns=CounterLike(byroot[root]['trucks'])
        line=f"| {key} | {ns.get('T1',0)} | {ns.get('T2',0)} | {m['truck_count']} | {int(m['cost'])} | {100*m['UV']:.3f}% | {100*m['UW']:.3f}% |"
        trace.append({'claim':key,'expected_paper_row_from_independent':line,'match':line in paper})
    costr=byroot['runs/R19/levels/L4/execution/results/classic_refined/Q2_min_cost']
    for t in costr['trucks']:
        line=f"| {t['truck_id']} | {t['vehicle_type']} | {t['items']} | {int(t['mass_kg'])} | {t['volume_cm3']/1e6:.5f} | {100*t['UV']:.3f}% | {100*t['UW']:.3f}% |"
        trace.append({'claim':'paper+report truck '+t['truck_id'],'expected_row':line,'match':line in paper and line in report})
    for r in coordinates['results']:
        if '/selected_single/' in r['path']:
            vt=r['trucks'][0]['vehicle_type'];name=r['path'].split('/')[-1];m=r['metrics'];cnt=','.join(str(r['inventory'].get('G'+str(n),0)) for n in range(1,6))
            line=f"| {vt} | {name} | {100*m['UV']:.3f}% | {100*m['UW']:.3f}% | {cnt} |"
            trace.append({'claim':'single '+name,'expected_row':line,'match':line in paper})
    params=list(csv.DictReader((E/'results/parameter_results.csv').open(encoding='utf-8-sig',newline='')))
    for p in params:
        r=byroot['runs/R19/levels/L4/execution/results/experiments/'+p['scenario']];m=r['metrics']
        line=f"| {p['scenario']} | {m['truck_count']} | {int(m['cost'])} | {100*m['UV']:.3f}% | {100*m['UW']:.3f}% | {float(p['elapsed_seconds']):.3f} |"
        trace.append({'claim':'parameter '+p['scenario'],'expected_row':line,'match':line in paper})
    for row in geometry:
        if row['vehicle']=='6.8米箱货':
            x=row['independent'];line=f"| {row['product']} | {row['vehicle']} | {x['conservative']} | {x['optimistic']} |"
            trace.append({'claim':'attachment2 '+row['product'],'expected_row':line,'match':line in paper})
    out={'independent_bounds':bound,'attachment2_pairs':len(geometry),'all_geometry_match':all(r['match'] for r in geometry),'geometry':geometry,
         'paper_trace_rows':len(trace),'all_paper_numeric_rows_match':all(r['match'] for r in trace),'trace':trace,
         'historical_runtime_limit':'Historical perf_counter values traced to run records and implementation; not independently recoverable as identical wall time',
         'scientific_quality_decision':'made by actual full reading, not this row-matching program'}
    (OUT/'numerical-trace.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ['geometry','trace']},ensure_ascii=False,indent=2))
def CounterLike(trucks):
    d={}
    for t in trucks:d[t['vehicle_type']]=d.get(t['vehicle_type'],0)+1
    return d
if __name__=='__main__':main()
