from pathlib import Path
import json,csv,sys,re,datetime,hashlib,importlib.metadata,platform
from openpyxl import load_workbook
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';E=B/'runs/R19/levels/L2/execution';P=B/'runs/R19/levels/L2/review/preparation';sys.path.insert(0,str(O));from audit_frozen import CAT
wb=load_workbook(B/'runs/R19/inputs/raw/附件2：验证数据集.xlsx',data_only=False);raw={s.title:{c.coordinate:c.value for r in s for c in r if c.value is not None} for s in wb};author=json.loads((E/'data/attachment2_audit.json').read_text(encoding='utf-8'));xlsx={'all_original_sheets_cells_preserved':raw==author['sheets'],'sheets':{k:len(v) for k,v in raw.items()},'missing_fields_conclusion':'quantity/weight/category/payload absent; audit-only correctly qualified','optional_full_extension_not_required':True}
paper=(E/'paper/paper.md').read_text(encoding='utf-8');table=paper.split('| 货物 | 类别 |')[1].split('\n\n')[0];rows=[r for r in table.splitlines() if r.startswith('| G')];checks=[]
for line in rows:
 r=[v.strip() for v in line.strip('|').split('|')];a=CAT[r[0]];wantcat={'standard':'标准件','fragile':'易碎件','directional':'定向件'}[a['category']];checks.append({'cargo':r[0],'match':r[1]==wantcat and [int(v) for v in r[2].split('×')]==list(a['dims']) and float(r[3])==a['weight'] and int(r[4])==a['count'] and r[5]==f"{a['weight']/(a['dims'][0]*a['dims'][1]*a['dims'][2]/1e9):.2f}"})
d=json.loads((O/'paper-figures-audit.json').read_text(encoding='utf-8'));d['raw_cargo_table']=checks;d['all_source_rows_match']=all(c['match'] for c in checks);d['all_numeric_rows_checked']=d['table_rows_checked']+len(checks);d['attachment2_direct_source_check']=xlsx
(O/'paper-figures-audit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
env={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'packages':{k:importlib.metadata.version(k) for k in ['numpy','scipy','matplotlib','PyMuPDF','python-docx','openpyxl','reportlab']},'model':None,'tokens':None,'cost':None,'network_used':False,'installs':False,'raw_hashes_after_review':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (B/'runs/R19/inputs/raw').iterdir()]}
(O/'environment-and-raw-final.json').write_text(json.dumps(env,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'attachment2_source_cells_match':xlsx['all_original_sheets_cells_preserved'],'all5_cargo_rows_match':d['all_source_rows_match'],'all_numeric_rows':d['all_numeric_rows_checked']},ensure_ascii=False))
