from pathlib import Path
import json, hashlib, sys, zipfile, xml.etree.ElementTree as ET
from datetime import datetime, timezone
import fitz, openpyxl
root=Path.cwd()
out=root/'runs/R19/levels/L1/review/preparation'
raw=root/'runs/R19/inputs/raw'
report={'status':'source_review_prepared_artifacts_pending','generated_at':datetime.now(timezone.utc).isoformat(),'python':sys.version,'sources':[]}
for p in sorted(raw.iterdir()):
    if p.name not in ['2026年第十六届MathorCup数学应用挑战赛题目—D题.pdf','附件1.docx','附件2：验证数据集.xlsx']: continue
    entry={'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    if p.suffix=='.pdf':
        doc=fitz.open(p)
        entry['pages']=[]
        for i,page in enumerate(doc):
            img=out/f'official-pdf-page-{i+1}.png'
            page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(img)
            entry['pages'].append({'page':i+1,'text':page.get_text(),'render':img.relative_to(root).as_posix()})
    elif p.suffix=='.docx':
        with zipfile.ZipFile(p) as z:
            ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            xml=ET.fromstring(z.read('word/document.xml'))
            entry['body']=[]
            for n,el in enumerate(xml.find('w:body',ns),1):
                kind=el.tag.rsplit('}',1)[-1]
                if kind=='p': entry['body'].append({'body_element':n,'kind':'paragraph','text':''.join(t.text or '' for t in el.findall('.//w:t',ns))})
                elif kind=='tbl':
                    rows=[]
                    for r,tr in enumerate(el.findall('w:tr',ns),1):
                        rows.append({'row':r,'cells':[{'col':c,'text':'\n'.join(''.join(t.text or '' for t in pp.findall('.//w:t',ns)) for pp in tc.findall('w:p',ns))} for c,tc in enumerate(tr.findall('w:tc',ns),1)]})
                    entry['body'].append({'body_element':n,'kind':'table','rows':rows})
            entry['media_members']=[n for n in z.namelist() if n.startswith('word/media/')]
            entry['other_xml_text']={}
            for n in z.namelist():
                if n.startswith(('word/header','word/footer','word/footnotes','word/endnotes')) and n.endswith('.xml'):
                    el=ET.fromstring(z.read(n)); entry['other_xml_text'][n]=''.join(t.text or '' for t in el.findall('.//w:t',ns))
    elif p.suffix=='.xlsx':
        wb=openpyxl.load_workbook(p,data_only=False)
        entry['sheets']=[]
        for ws in wb.worksheets:
            entry['sheets'].append({'name':ws.title,'state':ws.sheet_state,'max_row':ws.max_row,'max_column':ws.max_column,'merged_ranges':[str(r) for r in ws.merged_cells.ranges],'cells':[{'coordinate':cell.coordinate,'value':cell.value,'type':cell.data_type,'number_format':cell.number_format,'comment':None if cell.comment is None else cell.comment.text} for row in ws for cell in row if cell.value is not None]})
    report['sources'].append(entry)
(out/'official-source-extraction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'python':report['python'],'source_hashes':[{k:e[k] for k in ['path','bytes','sha256']} for e in report['sources']]},ensure_ascii=False,indent=2))
