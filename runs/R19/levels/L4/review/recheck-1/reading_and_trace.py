from pathlib import Path
import json,difflib,hashlib,csv,fitz,importlib.util
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;ROOT=O.parents[5];NEW=ROOT/'runs/R19/levels/L4/execution-v2';OLD=ROOT/'runs/R19/levels/L4/execution'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
diffs=[]
for rel in ['code/solve.py','code/validator.py','code/paper.py','paper/paper.md','paper/enterprise_report.md','README.md']:
    a=(OLD/rel).read_text(encoding='utf8');b=(NEW/rel).read_text(encoding='utf8');diffs.append({'file':rel,'diff':'\n'.join(difflib.unified_diff(a.splitlines(),b.splitlines(),fromfile='old/'+rel,tofile='v2/'+rel))})
save(O/'affected-diffs.json',diffs)
renders=[];RD=O/'reading';RD.mkdir(exist_ok=True)
for name in ['paper','enterprise_report']:
    doc=fitz.open(NEW/'paper'/f'{name}.pdf');texts=[];pages=[]
    for i,page in enumerate(doc):
        p=RD/f'{name}-{i+1:02d}.png';page.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(p);texts.append(page.get_text());pages.append(p)
    (RD/f'{name}-fulltext.txt').write_text('\n\n'.join(texts),encoding='utf8')
    for j in range(0,len(pages),3):
        tiles=[]
        for p in pages[j:j+3]:
            im=Image.open(p).convert('RGB');im.thumbnail((400,600));tiles.append(im)
        sheet=Image.new('RGB',(400*len(tiles),620),'#dddddd');draw=ImageDraw.Draw(sheet)
        for k,im in enumerate(tiles):sheet.paste(im,(400*k,20));draw.text((400*k+5,3),str(j+k+1),fill='black')
        sheet.save(RD/f'{name}-contact-{j//3+1}.png')
    renders.append({'file':str((NEW/'paper'/f'{name}.pdf').relative_to(ROOT)),'page_count':len(doc),'pages':[str(p.relative_to(ROOT)) for p in pages],'all_pages_rendered':True});doc.close()
save(O/'reading-render.json',renders)
# Reuse independent old parameter calculations only where exact input, config, coordinates and loads remain identical.
old=json.loads((O.parent/'initial/coordinate-review.json').read_text(encoding='utf8'));fresh=json.loads((O/'critical-coordinate-review.json').read_text(encoding='utf8'));reuse=[];results=[r for r in fresh['results'] if r['origin'] in ['new_frozen_selected','new_frozen_single']]
for r in old['results']:
    loc=r['path'].replace('\\','/');prefix='runs/R19/levels/L4/execution/'
    if '/results/experiments/' not in loc:continue
    rel=loc.split(prefix)[1];checks=[]
    for name in ['input.json','summary.json','placements.csv','support_loads.csv']:
        a=OLD/rel/name;b=NEW/rel/name
        checks.append({'file':rel+'/'+name,'old_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'new_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'same_bytes':a.read_bytes()==b.read_bytes()})
    assert all(x['same_bytes'] for x in checks)
    cp=dict(r);cp['path']=loc.replace(prefix,'runs/R19/levels/L4/execution-v2/');cp['reuse_from']='initial/coordinate-review.json';results.append(cp);reuse.append({'independent_old_result_path':loc,'dependencies':checks})
save(O/'reuse-parameter-evidence.json',{'scope':'17 historical independent calculations reused by byte identity; no new optimization or claim of new parameter rerun','records':reuse})
save(O/'coordinate-review.json',{'results':results,'scope':'8 current independent selected calculations plus17 old immutable parameter calculations explicitly reused'})
code=(O.parent/'initial/numerical_trace.py').read_text(encoding='utf8').replace("E=ROOT/'runs/R19/levels/L4/execution'","E=ROOT/'runs/R19/levels/L4/execution-v2'").replace("root='runs/R19/levels/L4/execution/'","root='runs/R19/levels/L4/execution-v2/'").replace("byroot['runs/R19/levels/L4/execution/results/","byroot['runs/R19/levels/L4/execution-v2/results/")
(O/'numerical_trace.py').write_text(code,encoding='utf8')
spec=importlib.util.spec_from_file_location('newtrace',O/'numerical_trace.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.main()
# Independent frozen checker on the original mechanism-control rows, not author flags.
from independent_checks import validate
D=json.loads((O/'consumer/data/raw_rebuilt.json').read_text(encoding='utf8'));cat={g['id']:{'dims':g['dims'],'class':'directed' if g['class']=='oriented' else g['class'],'mass':g['mass'],'quantity':g['quantity']} for g in D['cargo']};v=D['vehicles'][0];truck={'L':v['dims'][0],'W':v['dims'][1],'H':v['dims'][2],'capacity':v['capacity'],'cost':v['cost']};checks=[]
for p in sorted((O/'controls').glob('*/placements.csv')):
    if not (p.parent.name.startswith('csv_') or p.parent.name.startswith('valid_') or p.parent.name.startswith('negative_') or p.parent.name.startswith('nonpositive_') or p.parent.name in ['positive_overlap','height_gap']):continue
    rows=list(csv.DictReader(p.open(encoding='utf8',newline='')))
    try:
        its=[{'id':r['item_id'],'type':r['cargo_type'],'mass':cat[r['cargo_type']]['mass'],**{k:float(r[k]) for k in ['x','y','z','l','w','h']}} for r in rows];out=validate(truck,its,cat,pressure_basis='contact')
    except ValueError:out={'valid':False,'errors':['unparseable_real']}
    legal=p.parent.name.startswith('valid_');checks.append({'case':p.parent.name,'result':out,'assertion_passed':out['valid']==legal})
save(O/'frozen-control-review.json',{'checks':checks,'all_assertions_passed':all(x['assertion_passed'] for x in checks)})
print('RENDER',renders[0]['page_count'],renders[1]['page_count'],'REUSED',len(reuse),'FROZENCONTROLS',len(checks),flush=True)
