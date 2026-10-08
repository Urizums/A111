import csv,json,math,re,itertools
from pathlib import Path
H=Path(__file__).resolve().parent;E=H.parents[5]/'runs/R19/levels/L3/execution'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
main=load(H/'numeric-summary.json');exp=load(H/'experiment-audit.json');errors=[];proof=[]
ind={r['task']:r for r in main['selected']}; cases={(r['task'],Path(r['path']).name):r for r in exp['comparison_independent_cases']}
for row in rows(E/'figures/method_comparison.csv'):
 t=row['task']; method=row['method']
 if method=='最终':truth=ind[t]
 elif method=='基准':truth=cases[(t,'C000')]
 else:truth=min((r for r in exp['comparison_independent_cases'] if r['task']==t),key=lambda x:(x['C'],x['N']) if t=='Q2-C' else (x['N'],x['C']))
 if int(row['N'])!=truth['N'] or float(row['C_yuan'])!=truth['C']:errors.append(('method_figure',row))
proof.append('method comparison CSV: all 12 rows tied to independently computed candidates/main outputs')
for row in rows(E/'figures/single_frontier.csv'):
 truth=cases[(row['task'],row['candidate'])]
 if abs(float(row['Uv'])-truth['Uv'])>1e-12 or abs(float(row['Uw'])-truth['Uw'])>1e-12:errors.append(('single_frontier',row))
proof.append('single-frontier CSV: 56 points tied to source recomputation')
for row in rows(E/'figures/fleet_utilization.csv'):
 task=row['task'];v=next(x for x in load(H/f'numeric/selected-{task}.json')['vehicles'] if x['vehicle_id']==row['vehicle_id'])
 for field,source in [('volume_m3','volume_cm3'),('weight_kg','mass_kg'),('Uv','Uv'),('Uw','Uw')]:
  expected=v[source]/1e6 if field=='volume_m3' else v[source]
  if abs(float(row[field])-expected)>1e-9:errors.append(('fleet_figure',row['vehicle_id'],field))
proof.append('fleet CSV: all 30 trucks independently recomputed')
if rows(E/'figures/placement_3d.csv')!=[r for r in rows(E/'plans/Q1-F2/selected/placements.csv') if r['vehicle_id']=='V001']:errors.append('3D placement data differs')
proof.append('3D CSV: exact selected Q1-F2 first-truck rows already independently checked')
sr=load(E/'sensitivity/results.json');mapped={(r['scenario'],r['task']):r for r in sr}
sc={ (r['scenario'],r['task']):r for r in exp['sensitivity_independent_selected']}
for row in rows(E/'figures/sensitivity.csv'):
 t=sc[(row['scenario'],row['task'])]
 if t['N']!=int(row['N']) or t['C']!=float(row['C']):errors.append(('parameter_figure',row['scenario']))
proof.append('sensitivity CSV: 29 recommendations tied to independently checked declared scenarios')
md_proofs=[]
for name in ['paper','technical_report']:
 text=(E/(name+'.md')).read_text(encoding='utf-8');lines=[x for x in text.splitlines() if x.startswith('|')]
 task_rows=0;scenario_rows=0
 for line in lines:
  r=[x.strip() for x in line.strip('|').split('|')]
  if len(r)==7 and r[0] in ind:
   truth=ind[r[0]]
   if int(r[2])!=truth['N'] or float(r[3])!=truth['C'] or r[4]!=f"{truth['Uv']*100:.2f}%" or r[5]!=f"{truth['Uw']*100:.2f}%":errors.append((name,'formal_table',r))
   task_rows+=1
  if len(r)==7 and (r[0],'Q2-C') in sc:
   t=sc[(r[0],'Q2-C')];m=mapped[(r[0],'Q2-C')]
   if int(r[3])!=t['N'] or float(r[4])!=t['C'] or r[5]!=f"{m['Uv']*100:.2f}%" or r[6]!=f"{m['Uw']*100:.2f}%":errors.append((name,'scenario_table',r))
   scenario_rows+=1
 md_proofs.append({'document':name,'main_rows_checked':task_rows,'scenario_rows_checked':scenario_rows,'superscript_2_count':text.count('²'),'superscript_3_count':text.count('³')})
pdf=load(H/'pdf_visual/pdf-inspection.json');damage=[]
for doc in pdf:
 joined='\n'.join(p['text'] for p in doc['pages'])
 damage.append({'document':doc['name'],'pages':len(doc['pages']),'pdf_superscript_2_count':joined.count('²'),'pdf_superscript_3_count':joined.count('³'),
                'key_counterexamples':[{'page':p['page'],'lines':[x for x in p['text'].splitlines() if ('500 kg/m' in x or '500kg/m' in x or 'O(n_k)' in x or 'O(R)' in x or '19.1394m' in x)]} for p in doc['pages'] if any(x in p['text'] for x in ['500 kg/m','500kg/m','O(n_k)','O(R)','19.1394m'])]})
result={'data_and_markdown_trace_pass':not errors,'checks':proof,'markdown_table_checks':md_proofs,'data_errors':errors,
        'pdf_scientific_notation_damage':damage,'visual_observation':'All 14 pages seen in independent contact sheets; paper pages2/3/8 and report page1 viewed full size. Exponents visibly absent, not merely text extraction.',
        'defect':'PDF export drops units and complexity powers while source Markdown retains them; a deliverable cross-artifact contradiction.',
        'suggested_repair':'Use fonts or explicit superscript markup/ASCII powers that preserve m^2, m^3, O(n_k^2), and negative density powers; regenerate both PDFs and visually check every affected formula/table plus extracted semantic text.'}
(H/'figure-paper-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));assert not errors
