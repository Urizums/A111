import json,hashlib,shutil,re,sys,time,platform,os
from pathlib import Path
from datetime import datetime,timezone
import fitz,docx,openpyxl,psutil
H=Path(__file__).resolve().parent; R=H.parents[5]; E=R/'runs/R19/levels/L3/execution'; P=H.parent/'preparation'
t=time.perf_counter(); raw=R/'runs/R19/inputs/raw'
source_hashes=[{'path':str(p.relative_to(R)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in raw.iterdir() if p.is_file()]
pdf=[]
with fitz.open(next(raw.glob('*.pdf'))) as d:
 for i,p in enumerate(d): pdf.append({'page':i+1,'text':p.get_text()})
d=docx.Document(raw/'附件1.docx'); paragraphs=[{'paragraph':i+1,'text':p.text} for i,p in enumerate(d.paragraphs)]
tables=[{'table':i+1,'rows':[[c.text for c in r.cells] for r in tab.rows]} for i,tab in enumerate(d.tables)]
w=openpyxl.load_workbook(raw/'附件2：验证数据集.xlsx',data_only=False)
xlsx=[{'sheet':s.title,'merged_ranges':[str(x) for x in s.merged_cells.ranges],'cells':[{'address':c.coordinate,'value':c.value,'data_type':c.data_type} for row in s for c in row if c.value is not None]} for s in w]
audit={'pdf':pdf,'docx':{'paragraphs':paragraphs,'tables':tables},'xlsx':xlsx,'source_hashes':source_hashes}
(H/'independent-source-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
data={'cargo':[],'vehicles':[]}; kinds={'标准件':'standard','易碎件':'fragile','定向件':'directional'}
for i,row in enumerate(tables[0]['rows'][1:],2):
 dims=[float(v) for v in row[2].split('×')]
 data['cargo'].append(dict(cargo_type=row[0],category=kinds[row[1]],l_cm=dims[0],w_cm=dims[1],h_cm=dims[2],weight_kg=float(row[3]),quantity=int(row[4]),source=f'附件1 表1 R{i}',origin='official'))
ps={a['paragraph']:a['text'] for a in paragraphs}
for typ,pi in [('T1',4),('T2',8)]:
 dims=[float(v) for v in re.findall(r'(\d+)cm',ps[pi])]
 data['vehicles'].append(dict(vehicle_type=typ,l_cm=dims[0],w_cm=dims[1],h_cm=dims[2],capacity_kg=float(re.search(r'(\d+)kg',ps[pi+1])[1]),cost_yuan=float(re.search(r'(\d+)\s*元',ps[pi+2])[1]),source=f'附件1 P{pi}-P{pi+2}',origin='official'))
official=json.loads((E/'data/instance.json').read_text(encoding='utf-8'));assert data==official
clone=H/'sandbox';clone.mkdir();shutil.copytree(E/'src',clone/'src');shutil.copytree(E/'data',clone/'data')
(clone/'data/instance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for task in ['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']:
 shutil.copytree(E/f'plans/{task}/selected',clone/f'plans/{task}/selected')
shutil.copy2(P/'independent_checker.py',H/'independent_checker.py')
adapt={'method_source':'frozen preparation/independent_checker.py copied byte-for-byte; initial source_catalog reads independent-source-audit.json generated directly from original raw',
       'schema_mapping':{'x/y/z':'x_cm/y_cm/z_cm float','dx/dy/dz':'dx_cm/dy_cm/dz_cm float','types':'unchanged','orientation':'separate source-axis-to-car-axis mapping verification','support_ids':'separate coordinate reconstructed parent trace verification'},
       'source_numeric_match':True,'solver_copy_modified':False,'input_rebuilt_from_raw':True,
       'copies_write_only_here':True,'resource':{'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'cpu_logical':os.cpu_count(),'memory_available_bytes':psutil.virtual_memory().available,'own_rss_MB':psutil.Process().memory_info().rss/1048576,'model':None,'token':None,'cost':None},
       'elapsed_seconds':time.perf_counter()-t}
(H/'receipt-and-adapter.json').write_text(json.dumps(adapt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(adapt,ensure_ascii=False))
