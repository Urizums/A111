from zipfile import ZipFile
from pathlib import Path
from xml.etree import ElementTree as ET
p=Path('runs/R16/source/official_extracted/D_corrected/附件1.docx')
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(p) as z:
    root=ET.fromstring(z.read('word/document.xml'))
    for para in root.findall('.//w:p',ns):
        t=''.join(x.text or '' for x in para.findall('.//w:t',ns))
        if t.strip(): print(t)
    for ti,table in enumerate(root.findall('.//w:tbl',ns),1):
        print(f'[TABLE {ti}]')
        for row in table.findall('w:tr',ns):
            print(' | '.join(''.join(t.text or '' for t in c.findall('.//w:t',ns)) for c in row.findall('w:tc',ns)))
