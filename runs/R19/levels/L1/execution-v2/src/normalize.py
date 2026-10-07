from pathlib import Path
import json,re,hashlib,csv,sys
from docx import Document
from openpyxl import load_workbook
from solve import DEFAULT,ROOT

def normalize():
    raw=ROOT.parents[2]/'inputs/raw'
    expected={'2026年第十六届MathorCup数学应用挑战赛题目—D题.pdf':'33a0cabb68a4318cb77006f72053a57c4c3805a812905d4ee8125abb8c67094d','附件1.docx':'c5043af544588fe5183a1785364b5c69dfda4d9d7706444d0375263f631115d0','附件2：验证数据集.xlsx':'0fc33382d59919993c8ce4ed8a91c6e35e770db6a82bcd02e2e9e680493b8eda'}
    for name,sha in expected.items():
      if hashlib.sha256((raw/name).read_bytes()).hexdigest()!=sha:raise ValueError('Official source version changed: '+name)
    doc=Document(raw/'附件1.docx');p=[x.text for x in doc.paragraphs];cfg=json.loads(json.dumps(DEFAULT));sources=[]
    groups=[p[3:6],p[7:10]]
    for v,lines in zip(cfg['vehicles'],groups):
      v['dims']=[int(x) for x in re.findall(r'(\d+)\s*cm',lines[0])];v['payload']=int(re.search(r'(\d+)kg',lines[1]).group(1));v['cost']=int(re.search(r'(\d+)\s*元',lines[2]).group(1))
      sources.append({'object':v['id'],'location':f'附件1正文 {3 if v["id"]=="T1" else 7} 至 {6 if v["id"]=="T1" else 10}','original':lines})
    for c,row in zip(cfg['cargo'],doc.tables[0].rows[1:]):
      vals=[x.text for x in row.cells];c.update(id=vals[0],category={'标准件':'standard','易碎件':'fragile','定向件':'directional'}[vals[1].strip()],dims=[int(x) for x in vals[2].split('×')],weight=float(vals[3]),quantity=int(vals[4]));sources.append({'object':c['id'],'location':f'附件1表1第{len(sources)}行（按货号识别）','original':vals})
    cfg.update(directional_center_each=True,version='3.1-informed-F1',fragile_floor_only=False)
    from contracts import validate_config
    validate_config(cfg)
    (ROOT/'configs/base.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'inputs/normalized.json').write_text(json.dumps({'config':cfg,'sources':sources,'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.iterdir()}},ensure_ascii=False,indent=2),encoding='utf8')
    for name,items in [('vehicles',cfg['vehicles']),('cargo_types',cfg['cargo'])]:
      with (ROOT/f'inputs/{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=items[0].keys());w.writeheader();w.writerows(items)
    with (ROOT/'inputs/item_ids.csv').open('w',encoding='utf-8-sig',newline='') as f:
      w=csv.writer(f);w.writerow(['item_id','type_id'])
      for c in cfg['cargo']:
        for k in range(1,c['quantity']+1):w.writerow([f'{c["id"]}-{k:04d}',c['id']])
    w=load_workbook(next(raw.glob('*.xlsx')),data_only=True);s=w['箱装产品尺寸'];products=[]
    def endpoints(x):
      nums=[float(v) for v in re.findall(r'\d+(?:\.\d+)?',str(x))];return [min(nums),max(nums)] if nums else [None,None]
    for r in range(3,11):
      ds=[endpoints(s.cell(r,c).value) for c in [3,5,7]]
      products.append({'name':s.cell(r,1).value,'source_cells':[f'{s.title}!{s.cell(r,c).coordinate}' for c in [3,5,7]],'warehouse_raw':[s.cell(r,c).value for c in [3,5,7]],'dims_cm_upper':[x[1]/10 for x in ds],'dims_cm_lower':[x[0]/10 for x in ds],'weight_kg':None,'quantity':None,'category':None})
    vs=w['车型尺寸'];vehicles=[]
    for r in range(4,12):
      ds=[endpoints(vs.cell(r,c).value) for c in [2,3,4]];vehicles.append({'name':vs.cell(r,1).value,'dims_cm_lower':[x[0]*100 for x in ds],'source_row':r,'payload_kg':None,'trip_cost_yuan':None,'road_rate_raw':vs.cell(r,5).value})
    fits=[]
    for c in products:
      for v in vehicles:
        fits.append({'product':c['name'],'vehicle':v['name'],'fits_single_geometry':all(c['dims_cm_upper'][k]<=v['dims_cm_lower'][k]-(3 if k==2 else 0) for k in range(3)),'interpretation':'仅固定原姿态单件、仓测尺寸上端/车厢下端、顶部3cm；非业务求解'})
    (ROOT/'inputs/attachment2_geometry.json').write_text(json.dumps({'products':products,'closed_rectangular_vehicles':vehicles,'fits':fits,'excluded_rows':[12,13,14,15,16,17,18,19,20],'missing_business_fields':['mass','quantity','category/orientation','payload','distance and cost basis'],'full_business_solve':'not executable from supplied fields'},ensure_ascii=False,indent=2),encoding='utf8')
    return cfg

if __name__=='__main__':normalize();print('Normalized original DOCX; optional XLSX geometry audited.')
