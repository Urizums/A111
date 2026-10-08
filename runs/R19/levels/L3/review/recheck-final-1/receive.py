from pathlib import Path
import json,hashlib,time,datetime,shutil,difflib
import fitz
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[5]
L3=HERE.parents[1]
assert BASE.name=='A111' and L3.name=='L3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def check_lock(lock,scope):
    d=json.loads(lock.read_text(encoding='utf-8-sig'));files=d['files'];bad=[]
    for f in files:
        p=BASE/f['path']
        if not p.is_file() or sha(p)!=f['sha256'] or p.stat().st_size!=f.get('size_bytes',p.stat().st_size):bad.append(f['path'])
    listed={f['path'] for f in files}
    actual={p.relative_to(BASE).as_posix() for p in scope.rglob('*') if p.is_file()}
    return {'lock':str(lock),'lock_sha256':sha(lock),'count':len(files),'hash_or_size_errors':bad,'extra':sorted(actual-listed),'missing':sorted(listed-actual),'match':not bad and actual==listed}
t=time.perf_counter()
locks=[]
for name,scope in [('execution',L3/'execution'),('execution-v2',L3/'execution-v2'),('review/initial',L3/'review/initial'),('review/recheck-1',L3/'review/recheck-1')]:
    locks.append(check_lock(L3/(name+'-lock.json'),scope))
assert all(x['match'] for x in locks),locks
save('lock-start.json',{'utc':datetime.datetime.now(datetime.UTC).isoformat(),'locks':locks,'elapsed_seconds':time.perf_counter()-t})
copy=HERE/'consumer'
copy.mkdir()
for name in ['execution','execution-v2']:shutil.copytree(L3/name,copy/name)
bindings=[]
for p in sorted((L3/'execution-v2/figures').iterdir()):
    old=L3/'execution/figures'/p.name
    bindings.append({'path':p.name,'new_sha256':sha(p),'old_sha256':sha(old),'same_bytes':sha(p)==sha(old)})
assert all(x['same_bytes'] for x in bindings)
save('numeric-identity.json',{'original_execution_whole_lock_match':True,'original_count':locks[0]['count'],'initial_review_whole_lock_match':True,'old_numeric_study_reused':True,'figures':bindings,'limits':['Original numerical research is identity-bound and independently checked in initial review; not rerun entirely in this recheck.']})
visual=HERE/'pdf_visual';visual.mkdir()
pdfinfo={}
for name in ['paper','technical_report']:
    new=L3/'execution-v2'/f'{name}.md';old=L3/'execution'/f'{name}.md'
    (HERE/f'{name}.diff').write_text(''.join(difflib.unified_diff(old.read_text(encoding='utf-8-sig').splitlines(True),new.read_text(encoding='utf-8-sig').splitlines(True),fromfile='frozen_initial',tofile='frozen_revision')),encoding='utf-8')
    doc=fitz.open(L3/'execution-v2'/f'{name}.pdf');pages=[]
    thumbs=[]
    for i,page in enumerate(doc):
        text=page.get_text()
        (visual/f'{name}-{i+1:02}.txt').write_text(text,encoding='utf-8')
        pix=page.get_pixmap(matrix=fitz.Matrix(1.6,1.6));png=visual/f'{name}-{i+1:02}.png';pix.save(png)
        im=Image.open(png).convert('RGB');im.thumbnail((360,510))
        thumb=Image.new('RGB',(380,540),'#dddddd');thumb.paste(im,((380-im.width)//2,20));ImageDraw.Draw(thumb).text((10,522),f'{name} p{i+1}',fill='black');thumbs.append(thumb)
        pages.append({'page':i+1,'text_file':str(visual/f'{name}-{i+1:02}.txt'),'png':str(png),'chars':len(text),'fonts':page.get_fonts(full=True)})
    for start in range(0,len(thumbs),6):
        subset=thumbs[start:start+6];sheet=Image.new('RGB',(1140,540*((len(subset)+2)//3)),'white')
        for j,im in enumerate(subset):sheet.paste(im,((j%3)*380,(j//3)*540))
        sheet.save(visual/f'{name}-contact-{start//6+1}.png')
    pdfinfo[name]={'pages':len(doc),'sha256':sha(L3/'execution-v2'/f'{name}.pdf'),'pages_detail':pages}
save('pdf_visual/inspection.json',pdfinfo)
print(json.dumps({'locks':[(x['count'],x['match']) for x in locks],'copy_completed':True,'pdf_pages':{k:v['pages'] for k,v in pdfinfo.items()},'elapsed_seconds':time.perf_counter()-t}))
