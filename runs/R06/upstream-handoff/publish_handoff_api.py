"""One-off authorized unfinished-work handoff; preserves the strict acceptance verdict."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('existing_git_api', ROOT/'runs/cloud/publish_git_api.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
api, git = helper.api, helper.git

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    if a.receipt.exists():
        raise SystemExit('Receipt already exists; reconcile it rather than repeat publication')
    auth = json.loads((ROOT/'state/upstream-handoff.json').read_text())
    if not (auth['publication_authorized'] is True and auth['destination']=='waw1w1/A111:dev'
            and auth['full_acceptance_passed'] is False
            and auth['user_instruction']=='那就不用了，直接提pr过去，让上游完成剩下的工作，注明剩下的内容'):
        raise SystemExit('Specific unfinished-work handoff authorization absent')
    for row in json.loads((ROOT/'runs/R06/final/source-candidate.json').read_text())['files']:
        if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise SystemExit('Original tested candidate changed: '+row['path'])
    if git('diff','--name-only','HEAD').strip():
        raise SystemExit('Tracked working files differ from the committed handoff')
    payload = json.loads(subprocess.check_output([sys.executable,str(ROOT/'runs/cloud/prepare_git_payload.py'),a.base]))
    endpoint = 'repos/waw1w1/A111/git/'
    if api(endpoint+'ref/heads/dev')['object']['sha']!=payload['parent_sha']:
        raise SystemExit('Remote dev moved; do not overwrite it')
    if not payload['tree_elements']:
        raise SystemExit('No committed changes')
    blobs = {row['sha']:row for row in payload['blobs']}
    entries = []
    created_blobs = set()
    for row in payload['tree_elements']:
        entry = dict(row)
        if entry.get('sha') in blobs:
            raw = git('cat-file','blob',entry['sha'])
            try:
                entry['content']=raw.decode('utf-8');del entry['sha']
            except UnicodeDecodeError:
                if entry['sha'] not in created_blobs:
                    b=blobs[entry['sha']]
                    created=api(endpoint+'blobs',dict(content=b['content'],encoding='base64'))
                    if created['sha']!=entry['sha']:raise SystemExit('Blob hash mismatch')
                    created_blobs.add(entry['sha'])
                    print(json.dumps(dict(stage='binary_blob',count=len(created_blobs))),flush=True)
        entries.append(entry)
    batches=[];batch=[];size=0
    for entry in entries:
        item_size=len(json.dumps(entry,ensure_ascii=False).encode())
        if batch and size+item_size>1500000:batches.append(batch);batch=[];size=0
        batch.append(entry);size+=item_size
    if batch:batches.append(batch)
    tree=payload['base_tree_sha']
    for i,batch in enumerate(batches,1):
        tree=api(endpoint+'trees',dict(base_tree=tree,tree=batch))['sha']
        print(json.dumps(dict(stage='tree',batch=i,total=len(batches))),flush=True)
    if tree!=payload['tree_sha']:raise SystemExit('Remote tree mismatch; ref unchanged')
    meta=git('log','-1','--format=%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI').decode().rstrip('\n').split('\0')
    message=git('cat-file','commit','HEAD').decode().split('\n\n',1)[1]
    commit=api(endpoint+'commits',dict(message=message,tree=tree,parents=[payload['parent_sha']],
        author=dict(name=meta[0],email=meta[1],date=meta[2]),
        committer=dict(name=meta[3],email=meta[4],date=meta[5])))
    record=dict(schema='forge-authorized-upstream-publication/1',repository='waw1w1/A111',branch='dev',
        local_commit=payload['local_commit'],commit_sha=commit['sha'],parent_sha=payload['parent_sha'],tree_sha=tree,
        tree_matches_local=True,commit_matches_local=commit['sha']==payload['local_commit'],
        changed_files=len(entries),state='commit_created_ref_pending',recorded_at=datetime.now(timezone.utc).isoformat(),
        authority='state/upstream-handoff.json',full_acceptance_passed=False)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    with a.receipt.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
    if api(endpoint+'ref/heads/dev')['object']['sha']!=payload['parent_sha']:
        raise SystemExit('Concurrent dev change; commit receipt saved; ref untouched')
    updated=api(endpoint+'refs/heads/dev',dict(sha=commit['sha'],force=False),method='PATCH')
    if updated['object']['sha']!=commit['sha']:raise SystemExit('Unexpected update result; reconcile receipt')
    record.update(state='published',ref=updated,recorded_at=datetime.now(timezone.utc).isoformat())
    a.receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
