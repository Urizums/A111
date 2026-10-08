"""Recompute every manuscript table row from source data and actual outputs."""
import csv,json,math,re,fitz
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def rd(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
s=json.loads((R/'results/final/summary.json').read_text());sel=[a for a in s['runs'] if a['method']=='column_patterns_MILP'];vs=json.loads((R/'data/vehicles.json').read_text());types=json.loads((R/'data/types.json').read_text());valid=json.loads((R/'results/final/selected/q2_cost/validation.json').read_text());ss=valid['vehicles'];pp=rd(R/'results/final/selected/q2_cost/placements.csv');rep=max(ss,key=lambda a:(sum(a.get(t,0)>0 for t in ['G1','G2','G3','G4','G5']),-a['item_count']));p=[a for a in pp if a['vehicle_id']==rep['vehicle_id']]
names={'q1_all_v1':'仅车型1','q1_all_v2':'仅车型2','q2_vehicles':'混合最少车','q2_cost':'混合最低成本'}
expected=[]
expected.append([[t['cargo_type'],t['category'],'×'.join(map(str,t['dims'])),str(t['weight']),str(t['count']),f"{t['weight']/(math.prod(t['dims'])/1e9):.2f}"] for t in types])
expected.append([[a['scenario'],','.join(map(str,a['counts'])),f"{a['volume_utilization']*100:.2f}",f"{a['weight_utilization']*100:.2f}",str(a['validation_status'])] for a in s['singles']])
expected.append([[names[a['scenario']],str(a['vehicle_count']),str(a['cost_yuan']),f"{a['volume_utilization']*100:.2f}",f"{a['weight_utilization']*100:.2f}",str(a['bounds']['lower_bound']),f"{((a['cost_yuan'] if a['objective']=='cost' else a['vehicle_count'])-a['bounds']['lower_bound'])/(a['cost_yuan'] if a['objective']=='cost' else a['vehicle_count'])*100:.2f}"] for a in sel])
expected.append([[a['vehicle_id'],a['vehicle_type'],str(a['item_count']),*[str(a.get(t,0)) for t in ['G1','G2','G3','G4','G5']],f"{a['volume_utilization']*100:.1f}",f"{a['weight_utilization']*100:.1f}"] for a in ss])
cc=json.loads((R/'research/comparison/guarded_summary.json').read_text());expected.append([[a['method'],str(a['seed']),str(a['library_size']),str(a['q1_all_v1_vehicles']),str(a['q1_all_v2_vehicles']),str(a['q2_vehicles_vehicles']),str(a['q2_cost_vehicles']),str(a['q2_cost_cost']),f"{a['total_outer_seconds']:.2f}"] for a in cc])
ee=rd(R/'experiments/experiments.csv');expected.append([[a['parameter'],a['factor'],a['status'],a['vehicles'] or '-',a['cost_yuan'] or '-',f"{float(a['seconds']):.2f}"] for a in ee])
expected.append([[a['item_id'],a['cargo_type'],a['x_mm'],a['y_mm'],a['z_mm'],a['orientation_id'],'×'.join(a[k] for k in ['dx_mm','dy_mm','dz_mm'])] for a in p[:12]])
text=(R/'paper/paper.md').read_text(encoding='utf8');tables=[];group=[]
for line in text.splitlines()+['']:
 if line.startswith('|'):group.append([a.strip() for a in line.strip('|').split('|')])
 elif group:tables.append(group[2:]);group=[]
assert len(tables)==len(expected)==7
for j,(a,b) in enumerate(zip(tables,expected)):assert a==b,('table mismatch',j)
report=(R/'report.md').read_text(encoding='utf8');assert '12辆、8400元' in report and '13辆、7850元' in report
qa=json.loads((R/'checks/pdf_render_manifest.json').read_text());assert len(qa)==14 and not any(a['outside_blocks'] for a in qa)
for path in [R/'paper/paper.pdf',R/'report.pdf']:
 d=fitz.open(path);alltext=''.join(p.get_text() for p in d);assert '7850' in alltext and '5350' in alltext
claims=rd(R/'claim_evidence.csv');q=next(a for a in claims if a['requirement']=='Q3-A');assert '36 actual current' in q['claim'] and 'prior36' in q['claim'] and '32 actual' not in q['claim']
images=re.findall(r'!\[.*?\]\((.*?)\)',text);assert len(images)==7 and all((R/'paper'/x).resolve().exists() for x in images)
out={'tables':7,'rows_recomputed':sum(len(a) for a in expected),'all_rows_match':True,'pdf_pages':len(qa),'pdf_outside_blocks':0,'q3_trace_current36_prior36':True,'all7_figures_bound_and_present':True,'objective_pairs_distinct_and_correct':True,'visual_review':'all14 rendered pages inspected by author in3 contact sheets; representative graph/table pages additionally inspected; independent informed rereview pending'}
(R/'checks/manuscript_consistency.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(out)
