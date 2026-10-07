"""Read official DOCX bytes directly for reviewer recomputation; no producer parser."""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile,re,json,itertools,hashlib
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def text(node):return ''.join(n.text or '' for n in node.findall('.//w:t',NS))
def official(path):
 b=Path(path).read_bytes()
 with zipfile.ZipFile(path) as z:root=ET.fromstring(z.read('word/document.xml'))
 ps=[text(p) for p in root.findall('.//w:body/w:p',NS)]
 rows=[[text(c) for c in r.findall('w:tc',NS)] for r in root.findall('.//w:tbl/w:tr',NS)]
 catalog={}
 for ridx,row in enumerate(rows[1:],2):
  if len(row)!=5:raise ValueError('Unexpected official cargo table shape')
  name,cat,dimension,weight,count=row
  cm=tuple(int(x) for x in re.findall(r'\d+',dimension)); mm=tuple(x*10 for x in cm)
  category={'标准件':'standard','易碎件':'fragile','定向件':'directional'}[cat]
  catalog[name]={'cargo':name,'category':category,'dims':mm,'weight':float(weight),'count':int(count),'source':f'附件1.docx table1 row{ridx}','original_dims_cm':cm}
 vehicles={}
 for pidx,p in enumerate(ps):
  m=re.search(r'车型([12])（',p)
  if not m:continue
  k=m.group(1);d=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',ps[pidx+1])]
  payload=float(re.search(r'([\d.]+)kg',ps[pidx+2]).group(1));cost=float(re.search(r'([\d.]+)\s*元',ps[pidx+3]).group(1))
  vehicles[k]={'dims':[x*10 for x in d],'payload':payload,'cost':cost,'clearance':30,'source':f'附件1.docx paragraphs {pidx+1}-{pidx+4}'}
 if len(catalog)!=5 or set(vehicles)!={'1','2'}:raise ValueError('Official field coverage mismatch')
 return {'catalog':catalog,'vehicle_types':vehicles,'raw_sha256':hashlib.sha256(b).hexdigest(),'units':{'length':'mm','weight':'kg','cost':'yuan/trip','pressure':'kg/m2'},'clearance_source':'paragraph19','pressure_source':'paragraph18','pressure_limit':500}
if __name__=='__main__':
 out=Path(__file__).parent
 data=official(Path.cwd()/'runs/R19/inputs/raw/附件1.docx')
 (out/'official-data-binding.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'catalog_count':len(data['catalog']),'vehicle_types':list(data['vehicle_types']),'raw_sha256':data['raw_sha256'],'units':data['units']},ensure_ascii=False))
