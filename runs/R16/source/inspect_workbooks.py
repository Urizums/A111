from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import re
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','p':'http://schemas.openxmlformats.org/package/2006/relationships'}
base=Path('runs/R16/source/official_extracted')
for path in [*base.glob('**/*.xlsx')]:
    print(f'[{path.relative_to(base)}]')
    with ZipFile(path) as z:
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets={x.attrib['Id']:x.attrib['Target'] for x in rel}
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(t.text or '' for t in si.findall('.//m:t',ns)) for si in root.findall('m:si',ns)]
        for sh in wb.findall('m:sheets/m:sheet',ns):
            tgt=targets[sh.attrib['{'+ns['r']+'}id']].lstrip('/')
            if not tgt.startswith('xl/'): tgt='xl/'+tgt
            sheet=ET.fromstring(z.read(tgt))
            rows=sheet.findall('.//m:sheetData/m:row',ns)
            def val(c):
                v=c.find('m:v',ns)
                if v is None: return ''
                x=v.text or ''
                if c.attrib.get('t')=='s': x=shared[int(x)]
                return x
            print('sheet',sh.attrib['name'],'rows',len(rows),'dimension',sheet.find('m:dimension',ns).attrib.get('ref') if sheet.find('m:dimension',ns) is not None else None)
            for row in rows[:3]:
                print(' | '.join(f"{c.attrib.get('r')}={val(c)}" for c in row.findall('m:c',ns)))
