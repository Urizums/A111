"""Durable local validation budget. Not provider-global enforcement or semantic grading."""
import argparse,contextlib,fcntl,hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import snapshot

def stamp():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(snapshot.read_source(Path('/'),str(p.absolute()).lstrip('/'))).hexdigest()
def write(p,obj):
    temp=p.with_suffix('.tmp')
    with temp.open('w') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,p)
def bind(paths):
    return [{'path':str(p.absolute()),'sha256':sha(p)} for p in paths]
def unchanged(refs):return all(sha(Path(r['path']))==r['sha256'] for r in refs)
def capture(state,label,paths):
    bundle=state/label
    snapshot.capture(Path('/'),bundle,[str(p.absolute()).lstrip('/') for p in paths])
    return {'path':label,'manifest_sha256':sha(bundle/'manifest.json')}

@contextlib.contextmanager
def locked(state):
    with (state/'lock').open('a') as lock:
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another execution owns this journal')
        j=json.loads((state/'ledger.json').read_text())
        if j.get('schema')!='forge-bounded-run/1' or j['limit']!=2 or len(j['repairs'])>2:raise ValueError('Invalid journal')
        for r in j['snapshots']:
            p=state/r['path']
            if sha(p/'manifest.json')!=r['manifest_sha256']:raise ValueError('Snapshot manifest changed')
            snapshot.verify(p)
        for r in j['records']:
            if sha(state/r['path'])!=r['sha256']:raise ValueError('Attempt evidence changed')
        if not unchanged(j['inputs']):raise ValueError('Frozen inputs changed')
        yield j

def initialize(a):
    if not a.actor.strip():raise ValueError('Actor required')
    refs=bind(a.candidate);inputs=bind(a.input)
    a.state.mkdir(parents=True,exist_ok=False)
    allpaths=list(dict.fromkeys([*a.candidate,*a.input]));snap=capture(a.state,'snapshot-0',allpaths)
    j=dict(schema='forge-bounded-run/1',actor=a.actor,created_at=stamp(),limit=2,phase='ready',candidate=refs,
           inputs=inputs,snapshots=[snap],repairs=[],attempts=[],records=[])
    write(a.state/'ledger.json',j);return dict(initialized=True,repair_limit=2)

def repair(a):
    with locked(a.state) as j:
        if j['phase']!='failed':raise ValueError('Repair requires the preceding failed run')
        if len(j['repairs'])>=2:raise ValueError('Repair budget exhausted')
        if not a.reason.strip():raise ValueError('Actual failure and correction reason required')
        paths=[Path(r['path']) for r in j['candidate']];refs=bind(paths)
        if refs==j['candidate']:raise ValueError('No candidate change; do not invent a repair')
        number=len(j['repairs'])+1;snap=capture(a.state,f'snapshot-{number}',[*paths,*[Path(r['path']) for r in j['inputs']]])
        j['snapshots'].append(snap);j['repairs'].append(dict(number=number,at=stamp(),reason=a.reason,after_attempt=j['attempts'][-1]['id'],before=j['candidate'],after=refs));j['candidate']=refs;j['phase']='ready'
        write(a.state/'ledger.json',j);return dict(repair=number,remaining=2-number)

def run(a):
    command=a.argv[1:] if a.argv[:1]==['--'] else a.argv
    if not command:raise ValueError('Command required')
    with locked(a.state) as j:
        if j['phase'] not in {'ready','passed'}:raise ValueError('Journal is failed, exhausted or has an unknown in-flight run; do not retry')
        if not unchanged(j['candidate']):raise ValueError('Source changed without a recorded repair')
        number=len(j['attempts'])+1;attempt=dict(id=number,argv=command,cwd=str(Path.cwd()),started_at=stamp(),status='running',repair_count=len(j['repairs']))
        j['attempts'].append(attempt);j['phase']='running';write(a.state/'ledger.json',j)
        try:
            result=subprocess.run(command,capture_output=True,timeout=a.timeout)
            code=result.returncode;stdout=result.stdout;stderr=result.stderr;kind='exited'
        except subprocess.TimeoutExpired as exc:
            code=124;stdout=exc.stdout or b'';stderr=exc.stderr or b'';kind='timeout_direct_child_reaped'
        except OSError as exc:
            code=127;stdout=b'';stderr=str(exc).encode();kind='launch_failed'
        import base64
        record=dict(**attempt,ended_at=stamp(),exit_code=code,termination=kind,stdout_base64=base64.b64encode(stdout).decode(),stderr_base64=base64.b64encode(stderr).decode(),stdout=stdout.decode(errors='replace'),stderr=stderr.decode(errors='replace'),scope='Direct local child process; no descendant/provider termination or semantic acceptance claim')
        record['status']='passed' if code==0 else 'failed'
        path=a.state/f'attempt-{number}.json'
        with path.open('x') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
        j['records'].append(dict(path=path.name,sha256=sha(path)));attempt.update(status=record['status'],ended_at=record['ended_at'],exit_code=code)
        integrity=unchanged(j['candidate']) and unchanged(j['inputs'])
        j['phase']='unknown' if kind=='timeout_direct_child_reaped' else 'blocked_drift' if not integrity else 'passed' if code==0 else 'exhausted' if len(j['repairs'])>=2 else 'failed';write(a.state/'ledger.json',j)
        return dict(attempt=number,exit_code=code,phase=j['phase'],repairs_used=len(j['repairs']),record=str(path)),(2 if not integrity else code)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    i=sub.add_parser('init');i.add_argument('--state',type=Path,required=True);i.add_argument('--actor',required=True);i.add_argument('--candidate',type=Path,action='append',required=True);i.add_argument('--input',type=Path,action='append',required=True)
    r=sub.add_parser('repair');r.add_argument('--state',type=Path,required=True);r.add_argument('--reason',required=True)
    x=sub.add_parser('run');x.add_argument('--state',type=Path,required=True);x.add_argument('--timeout',type=float,default=60);x.add_argument('argv',nargs=argparse.REMAINDER)
    v=sub.add_parser('status');v.add_argument('--state',type=Path,required=True)
    a=p.parse_args()
    try:
        code=0
        if a.action=='init':result=initialize(a)
        elif a.action=='repair':result=repair(a)
        elif a.action=='run':
            if not 0<a.timeout<=60:raise ValueError('Local direct-child timeout must be in (0,60]')
            result,code=run(a)
        else:
            with locked(a.state) as j:result=j
        print(json.dumps(result,ensure_ascii=False));return code
    except (ValueError,OSError,KeyError,TypeError) as exc:print(json.dumps({'error':str(exc)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
