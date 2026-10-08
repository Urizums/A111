"""Refresh the mutable release catalog; preserve previous bytes and immutable locks."""
import hashlib,json,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
def row(path):
    data=path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
with ctl.locked(ROOT):
    old=json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    state=ctl.load(ROOT)
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    manifest_path=ROOT/'artifact-manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    changed=[]
    for entry in manifest['entries']:
        actual=row(ROOT/entry['path'])
        if entry!=actual:
            assert entry['path'] in {'START_HERE.md','CODEX_HANDOFF.md'},entry['path']
            changed.append(dict(previous=entry,current=actual))
            entry.update(actual)
    if changed:
        directory=ROOT/'runs/R19/integrity-history';directory.mkdir(exist_ok=True)
        serial=1
        while (directory/f'release-before-{serial}.json').exists():serial+=1
        (directory/f'release-before-{serial}.json').write_bytes(manifest_path.read_bytes())
        ctl.write_json(directory/f'release-refresh-{serial}.json',dict(at=ctl.stamp(),changed=changed,
            scope='Mutable release entry catalog only; historical skill/task/source locks unchanged.'))
        manifest['created_at']=ctl.stamp()
        ctl.write_json(manifest_path,manifest)
    lock_path='runs/R19/frozen-release-lock.json'
    if not (ROOT/lock_path).exists():
        paths={}
        source_locks=['runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/evaluation-lock.json']
        source_locks += [f'runs/R19/levels/L{k}/design-lock.json' for k in range(1,5)]
        for source in source_locks:
            for entry in json.loads((ROOT/source).read_text(encoding='utf-8'))['files']:
                actual=row(ROOT/entry['path'])
                assert actual['sha256']==entry['sha256'],entry['path']
                paths[actual['path']]=actual
        for path in [*(f'runs/R19/inputs/L{k}.md' for k in range(1,5)),
                     'runs/R19/package/Forge-C11-meta-workflow-candidate.zip',
                     'runs/R19/PLAN.md','runs/R19/PREPARATION_ADDENDUM.md']:
            paths[path]=row(ROOT/path)
        ctl.write_json(ROOT/lock_path,dict(schema='forge-revision-lock/1',revision='R19-source-and-designs',
            frozen_at=ctl.stamp(),files=sorted(paths.values(),key=lambda x:x['path']),
            claim='Identity of actual frozen source/design/package bytes only; paper behavior not accepted.'))
    index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
    if lock_path not in index['locks']:
        index['locks'].append(lock_path)
        ctl.write_json(ROOT/'state/revision-locks.json',index)
    for level in range(1,5):
        for scope in ['execution','execution-v2','review/preparation','review/initial','review/recheck-1','review/recheck-final-1','review/recheck-preparation']:
            relative=f'runs/R19/levels/L{level}/{scope}-lock.json'
            if (ROOT/relative).exists() and relative not in index['locks']:
                for entry in json.loads((ROOT/relative).read_text(encoding='utf-8'))['files']:
                    assert row(ROOT/entry['path'])==entry,entry['path']
                index['locks'].append(relative)
    extra='runs/R19/design-contract-audit-lock.json'
    if (ROOT/extra).exists() and extra not in index['locks']:
        for entry in json.loads((ROOT/extra).read_text(encoding='utf-8'))['files']:
            assert row(ROOT/entry['path'])==entry,entry['path']
        index['locks'].append(extra)
    ctl.write_json(ROOT/'state/revision-locks.json',index)
    # These catalogs previously used CRLF. Keep their existing Git style so
    # a two-entry update does not introduce thousands of unrelated line changes.
    for relative in ['artifact-manifest.json','state/revision-locks.json']:
        previous_bytes=subprocess.check_output(['git','show','HEAD:'+relative],cwd=ROOT)
        if b'\r\n' in previous_bytes:
            path=ROOT/relative
            path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
print(json.dumps(dict(release_entries_refreshed=len(changed),old_tasks_unchanged=len(old),revision_lock=lock_path,behavior_accepted=False)))
