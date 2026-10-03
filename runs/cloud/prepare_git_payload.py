"""Prepare local tree data for the authorized GitHub Git Data API (no credentials)."""
import base64,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
def git(*argv):return subprocess.check_output(['git','-C',str(root),*argv])
base=sys.argv[1]
known={line.split()[0] for line in git('rev-list','--objects',base).decode().splitlines()}
changes=git('diff','--no-renames','--name-status','-z',base,'HEAD').decode().split('\0')
index={}
for entry in git('ls-tree','-r','-z','HEAD').decode().split('\0'):
 if not entry:continue
 metadata,path=entry.split('\t',1);mode,kind,sha=metadata.split();index[path]=(mode,sha)
entries=[];blobs={};i=0
while i<len(changes)-1:
 status=changes[i];path=changes[i+1];i+=2
 if status.startswith(('R','C')):raise SystemExit('Use --no-renames input before preparing renamed paths')
 if status=='D':entries.append({'path':path,'mode':'100644','type':'blob','sha':None});continue
 mode,sha=index[path];entries.append({'path':path,'mode':mode,'type':'blob','sha':sha})
 if sha not in known and sha not in blobs:
  raw=git('cat-file','blob',sha);blobs[sha]={'sha':sha,'encoding':'base64','content':base64.b64encode(raw).decode(),'size_bytes':len(raw)}
print(json.dumps({'parent_sha':git('rev-parse',base).decode().strip(),'local_commit':git('rev-parse','HEAD').decode().strip(),'tree_sha':git('rev-parse','HEAD^{tree}').decode().strip(),'base_tree_sha':git('rev-parse',base+'^{tree}').decode().strip(),'tree_elements':entries,'blobs':list(blobs.values())}))
