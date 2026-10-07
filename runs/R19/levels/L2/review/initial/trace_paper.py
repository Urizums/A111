from pathlib import Path
import json,re,hashlib,datetime,csv,collections,math,difflib
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';E=B/'runs/R19/levels/L2/execution';A=json.loads((O/'independent-frozen-audit.json').read_text(encoding='utf-8'));R=json.loads((O/'reproduction-independent-audit.json').read_text(encoding='utf-8'));paper=(E/'paper/paper.md').read_text(encoding='utf-8');report=(E/'report.md').read_text(encoding='utf-8');generated=(O/'staged/paper/paper.md').read_text(encoding='utf-8')
# All manuscript table rows tied to independently recomputed metrics.
tables=[];lines=paper.splitlines();block=[]
for line in lines+['']:
 if line.startswith('|'):block.append([x.strip() for x in line.strip('|').split('|')])
 elif block:
  tables.append(block);block=[]
scenarios=['q1_all_v1','q1_all_v2','q2_vehicles','q2_cost'];scene={Path(z['folder']).name:z for z in A['layouts'] if '/selected/' in z['folder'].replace(chr(92),'/')};singles={Path(z['folder']).name:z for z in A['layouts'] if '/single/' in z['folder'].replace(chr(92),'/')};checks=[]
for rows in tables:
 head=rows[0];data=[r for r in rows[1:] if not all(re.fullmatch('[-: ]+',x or '-') for x in r)]
 if head[0]=='方案ID':
  for r in data:
   z=singles[r[0].replace('single_','')];m=z['metrics'];checks.append({'table':'single','row':r[0],'numeric_match':r[1]==','.join(str(z['counts'].get(t,0)) for t in ['G1','G2','G3','G4','G5']) and r[2]==f"{100*m['volume_utilization']:.2f}" and r[3]==f"{100*m['weight_utilization']:.2f}"})
 elif head[0]=='场景':
  for r,s in zip(data,scenarios):
   z=scene[s];m=z['metrics'];lb=z['independent_relaxation']['lower_bound'];ub=m['cost_yuan'] if s=='q2_cost' else m['vehicle_count'];checks.append({'table':'fleet','row':r[0],'numeric_match':int(r[1])==m['vehicle_count'] and float(r[2])==m['cost_yuan'] and r[3]==f"{100*m['volume_utilization']:.2f}" and r[4]==f"{100*m['weight_utilization']:.2f}" and float(r[5])==lb and r[6]==f"{100*(ub-lb)/ub:.2f}"})
 elif head[0]=='车ID':
  z=scene['q2_cost']
  for r in data:
   m=z['per_vehicle'][r[0]];checks.append({'table':'all_vehicle','row':r[0],'numeric_match':all(int(r[j+2])==m['counts'].get(t,0) for j,t in enumerate(['G1','G2','G3','G4','G5'])) and float(r[7])==m['weight'] and r[8]==f"{m['volume_utilization']*100:.1f}" and r[9]==f"{m['weight_utilization']*100:.1f}"})
 elif head[0]=='参数':
  exps={x.get('case'):x for x in A['experiments']}
  with (E/'experiments/experiments.csv').open(encoding='utf-8-sig') as f:csvrows=list(csv.DictReader(f))
  for row,c in zip(data,csvrows):checks.append({'table':'parameters','row':c['case'],'numeric_match':row[0]==c['parameter'] and row[1]==c['factor'] and row[2]==c['status'] and row[3]==(c['vehicles'] or '-') and row[4]==(c['cost_yuan'] or '-') and row[5]==f"{float(c['seconds']):.2f}"})
 elif head[0]=='item_id':
  with (E/'results/final/selected/q2_cost/placements.csv').open(encoding='utf-8-sig') as f:placement={r['item_id']:r for r in csv.DictReader(f)}
  for r in data:
   z=placement[r[0]];checks.append({'table':'precise_coordinates','row':r[0],'numeric_match':r[1]==z['cargo_type'] and all(float(r[j+2])==float(z[k]) for j,k in enumerate(['x_mm','y_mm','z_mm'])) and r[5]==z['orientation_id'] and r[6]=='×'.join(z[k] for k in ['dx_mm','dy_mm','dz_mm'])})
figs=[]
for name in ['single_frontier.png','fleet_compare.png','representative_3d.png','representative_views.png','sensitivity.png','cost_and_performance.png']:
 p=E/'figures'/name;q=O/'staged/figures'/name;figs.append({'file':name,'source_hash':hashlib.sha256(p.read_bytes()).hexdigest(),'regenerated_hash':hashlib.sha256(q.read_bytes()).hexdigest(),'bytes_equal':p.read_bytes()==q.read_bytes(),'visually_inspected':True,'data_independently_checked':'independent-frozen-audit.json; plotting code inspected; raw-bound fresh results for first4, all35 independently audited experiment CSV points for last2'})
visual=json.loads((O/'pdf-render-audit.json').read_text(encoding='utf-8'));visual['visual_inspection']='all 11 paper and2 report page images actually inspected at original resolution; coherent text, tables, figures, no clipping/overlap, repeat headers on split tables; last appendix/report pages sparse but readable';visual['all_pages_visually_inspected']=True;(O/'pdf-render-audit.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2),encoding='utf-8')
semantic_diff=list(difflib.unified_diff(paper.splitlines(),generated.splitlines(),n=0));(O/'paper-regeneration.diff.txt').write_text('\n'.join(semantic_diff),encoding='utf-8')
controller=json.loads((O/'producer-checker-controls.json').read_text(encoding='utf-8'));failure=next(r for r in controller['analytical_cases'] if not r['passed']);disposition={'case':failure['case'],'observation':'source-wide analytical partial support accepted by permissive review model, rejected as incomplete support by producer','source_vs_assumption':'DOCX explicitly requires full support for fragile; nonfragile full support is author declared conservative model, so this is expected restriction, not an undeclared source claim','mandatory_defect':False,'scope_limit':'target not a complete permissive original-feasibility checker; preserved failed control result without relabeling pass'}
summary={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'paper_tables':checks,'all_tables_match':all(c['numeric_match'] for c in checks),'table_rows_checked':len(checks),'figures':figs,'all_figures_regenerated_equal':all(f['bytes_equal'] for f in figs),'paper_regeneration_difference':'only fresh measured total and4 solver times (see diff); results/tables unchanged; hardcoded main-scene explanatory constants inspected against independent original arithmetic, not treated as dynamic general-template capability','prose_claims':{'inventory_volume_weight':{'independent_volume_m3':A['layouts'][0]['independent_relaxation']['volume_mm3']/1e9,'independent_mass_kg':A['layouts'][0]['independent_relaxation']['mass_kg'],'paper_present':'287.35' in paper and '41100' in paper},'density':A['density_bound'],'contact_pressure_clearance':{'max_pressure':scene['q2_cost']['max_pressure'],'min_clearance_mm':scene['q2_cost']['min_clearance_mm'],'paper_present':'384.00' in paper and '50mm' in paper},'parameter_claim_scope':'all36 source variations/35 valid layouts independently checked, 9critical fresh successful + necessary-height fail; no physical truth/general population claim'},'scientific_read':{'complete_paper':True,'complete_technical_report':True,'original_question_chain':True,'model_method_result_validation_interpretation':True,'no_global_optimality_claim':True,'references':'only the 3 actually read official original files; no invented external bibliography','restrained_conclusions':True,'remaining_quality_gaps':['restricted column/platform search and loose global necessary bounds leave original-optimality unresolved, explicitly limited','floor/fragile-fixed branches bound major ambiguities; wider partial-support/material dynamics not modeled','method comparison bundles platform patterns/randomized priorities/pattern-MILP: no isolated causal attribution to platform alone','runtime scatter combines heterogeneous perturbations; supports measured cases only, not asymptotic scaling estimation']},'controlled_partial_support_disposition':disposition,'traceability_metadata_note':'claim_evidence.csv Q3 row still labels original32, whereas actual experiment/paper/report contain36; original32 retained as real subset. Update tracking scope to36, no numerical main-claim contradiction.'}
(O/'paper-figures-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'table_rows':len(checks),'all_tables_match':summary['all_tables_match'],'all6_figures_equal':summary['all_figures_regenerated_equal'],'controlled_source_scope_case':disposition,'diff_line_count':len(semantic_diff)},ensure_ascii=False))

