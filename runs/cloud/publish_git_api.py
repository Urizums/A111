"""Publish this task's committed tree through gh's authorized Git Data API.

Git HTTPS transport in this cloud session rejects push authentication. The API
uses the existing gh credential provider without reading or printing its token.
Only a fast-forward of the explicitly supplied branch is permitted.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def api(path, body=None, method='POST'):
    command = ['gh', 'api', path]
    if body is None:
        return json.loads(subprocess.check_output(command))
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as payload:
        json.dump(body, payload, ensure_ascii=False)
        payload.flush()
        return json.loads(subprocess.check_output(command + ['--method', method,
                                                              '--input', payload.name]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repository', required=True)
    p.add_argument('--branch', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--message', required=True)
    p.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    if args.receipt.exists():
        p.error('Receipt already exists; inspect it before attempting another publication')
    payload = json.loads(subprocess.check_output(
        ['python3', str(ROOT/'runs/cloud/prepare_git_payload.py'), args.base]))
    endpoint = 'repos/' + args.repository + '/git/'
    ref = api(endpoint + 'ref/heads/' + args.branch)
    if ref['object']['sha'] != payload['parent_sha']:
        raise SystemExit('Branch moved from expected base; integrate it before publication')
    if not payload['tree_elements']:
        raise SystemExit('No committed changes to publish')
    blobs = {row['sha']: row for row in payload['blobs']}
    entries = []
    for row in payload['tree_elements']:
        entry = dict(row)
        if entry.get('sha') in blobs:
            raw = git('cat-file', 'blob', entry['sha'])
            try:
                entry['content'] = raw.decode('utf-8')
                del entry['sha']
            except UnicodeDecodeError:
                blob = blobs[entry['sha']]
                created = api(endpoint + 'blobs', dict(content=blob['content'], encoding='base64'))
                assert created['sha'] == entry['sha']
        entries.append(entry)
    tree = payload['base_tree_sha']
    batches, batch, size = [], [], 0
    for entry in entries:
        item_size = len(json.dumps(entry, ensure_ascii=False).encode())
        if batch and size + item_size > 1_500_000:
            batches.append(batch)
            batch, size = [], 0
        batch.append(entry)
        size += item_size
    if batch:
        batches.append(batch)
    for i, batch in enumerate(batches, 1):
        tree = api(endpoint + 'trees', dict(base_tree=tree, tree=batch))['sha']
        print(json.dumps(dict(stage='tree', batch=i, total=len(batches))), flush=True)
    if tree != payload['tree_sha']:
        raise SystemExit('Remote tree differs from committed local bytes; branch unchanged')
    commit = api(endpoint + 'commits', dict(message=args.message, tree=tree,
                                           parents=[payload['parent_sha']]))
    record = dict(schema='forge-github-publication/1', repository=args.repository,
                  branch=args.branch, local_commit=payload['local_commit'],
                  parent_sha=payload['parent_sha'], tree_sha=tree,
                  commit_sha=commit['sha'], tree_matches_local=True,
                  changed_files=len(entries), state='commit_created_ref_pending',
                  recorded_at=datetime.now(timezone.utc).isoformat())
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(record, indent=2) + '\n')
    # A concurrent branch update is never silently overwritten.
    if api(endpoint + 'ref/heads/' + args.branch)['object']['sha'] != payload['parent_sha']:
        raise SystemExit('Concurrent branch update; receipt retained and ref left unchanged')
    updated = api(endpoint + 'refs/heads/' + args.branch,
                  dict(sha=commit['sha'], force=False), method='PATCH')
    assert updated['object']['sha'] == commit['sha']
    record.update(state='published', ref=updated,
                  recorded_at=datetime.now(timezone.utc).isoformat())
    args.receipt.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
