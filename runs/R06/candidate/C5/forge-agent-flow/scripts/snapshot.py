"""Retain original handoff bytes before dispatch; never replay effects."""
import argparse,hashlib,json,os,stat,sys
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath

def safe_name(name):
    if not isinstance(name,str) or not name or '\\' in name or '\x00' in name:
        raise ValueError('Invalid relative path')
    p=PurePosixPath(name)
    if p.is_absolute() or p.as_posix()!=name or any(x in {'','..','.'} for x in name.split('/')):
        raise ValueError('Path must be canonical and contained')
    return p

def read_source(root,name):
    parts=safe_name(name).parts
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child
        filefd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        with os.fdopen(filefd,'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):raise ValueError('Not a regular file')
            return f.read()
    finally:os.close(fd)

def capture(root,out,names):
    if not names or len(set(names))!=len(names):raise ValueError('Nonempty unique inputs required')
    values=[(name,read_source(root,name)) for name in names]
    out.mkdir(parents=True,exist_ok=False);(out/'objects').mkdir()
    rows=[]
    for name,data in values:
        digest=hashlib.sha256(data).hexdigest();obj=out/'objects'/digest
        if not obj.exists():obj.write_bytes(data)
        rows.append(dict(path=name,sha256=digest,size_bytes=len(data)))
    manifest=dict(schema='forge-byte-snapshot/1',captured_at=datetime.now(timezone.utc).isoformat(),files=rows,
                  limits='Byte identity only; capture must precede dispatch; not authenticated timestamps or effect replay')
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return dict(manifest=str(out/'manifest.json'),sha256=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest(),files=len(rows))

def verify(bundle):
    manifest=json.loads(read_source(bundle,'manifest.json'))
    if manifest.get('schema')!='forge-byte-snapshot/1' or not isinstance(manifest.get('files'),list) or not manifest['files']:
        raise ValueError('Invalid snapshot manifest')
    names=set();objects=set();values=[]
    for row in manifest['files']:
        name=row['path'];safe_name(name)
        if name in names:raise ValueError('Duplicate snapshot path')
        names.add(name);digest=row['sha256']
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid digest')
        if type(row['size_bytes']) is not int or row['size_bytes']<0:raise ValueError('Invalid size')
        data=read_source(bundle,'objects/'+digest)
        if len(data)!=row['size_bytes'] or hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Snapshot byte mismatch')
        objects.add(digest);values.append((name,data))
    if {p.name for p in (bundle/'objects').iterdir()}!=objects:raise ValueError('Unexpected snapshot object')
    if {p.name for p in bundle.iterdir()}!={'objects','manifest.json'}:raise ValueError('Unexpected snapshot entry')
    return values

def restore(bundle,out):
    values=verify(bundle);out.mkdir(parents=True,exist_ok=False)
    for name,data in values:
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(data)
    return dict(restored=len(values),destination=str(out),effects_replayed=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('capture');c.add_argument('--root',type=Path,required=True);c.add_argument('--out',type=Path,required=True);c.add_argument('--path',action='append',required=True)
    v=sub.add_parser('verify');v.add_argument('bundle',type=Path)
    r=sub.add_parser('restore');r.add_argument('bundle',type=Path);r.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:
        result=capture(a.root,a.out,a.path) if a.command=='capture' else restore(a.bundle,a.out) if a.command=='restore' else dict(valid=True,files=len(verify(a.bundle)),effects_replayed=False)
        print(json.dumps(result));return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:print(json.dumps({'error':str(exc)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
