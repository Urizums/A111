"""Prospective local single-child registry with append-only per-attempt outputs.

This is collaboration/process discipline, not OS isolation. No historical receipt recovery.
"""
from pathlib import Path
import datetime,json,hashlib,subprocess,time,uuid,os
import psutil
V2=Path(__file__).resolve().parents[1]
OLD=V2.parent/'execution'
def now():return datetime.datetime.now(datetime.UTC).isoformat()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inside(p):
    p=Path(p).resolve()
    if not p.is_relative_to(V2):raise ValueError('All mutable outputs must be inside execution-v2')
    return p
class Busy(RuntimeError):pass
class Registry:
    def __init__(self):self.active=V2/'logs/active_child.json';self.guard=V2/'logs/launch_guard';self.children={}
    def inspect(self):
        if not self.active.exists():return {'state':'idle'}
        r=json.loads(self.active.read_text(encoding='utf-8'))
        try:
            p=psutil.Process(r['pid']);same=abs(p.create_time()-r['process_create_time'])<.01
            running=same and p.is_running() and p.status()!=psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:same=False;running=False
        except psutil.AccessDenied:return {'state':'identity_unavailable_block','record':r}
        return {'state':'live_block' if running else 'requires_terminal_reconciliation','identity_matches':same,'running':running,'record':r}
    def blocked(self,reason):
        d=V2/'attempts'/('blocked-'+uuid.uuid4().hex);d.mkdir()
        save(d/'receipt.json',{'utc':now(),'status':'blocked_before_child_start','reason':reason,'pid':None,'stdout':None,'numerical_solver_started':False})
        raise Busy(reason)
    def start(self,argv,label,limit=120):
        if not 0<limit<=120:raise ValueError('Declared child limit must be in (0,120]')
        try:fd=os.open(self.guard,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:self.blocked('Launch guard present; inspect owner and pending receipt before retry')
        try:
            os.write(fd,str(os.getpid()).encode())
            state=self.inspect()
            if state['state']!='idle':self.blocked(state)
            d=V2/'attempts'/(label+'-'+uuid.uuid4().hex);d.mkdir()
            # argv may specify output placeholders only resolved into this fresh attempt.
            argv=[str(x).replace('{ATTEMPT}',str(d)) for x in argv]
            stdout=(d/'stdout.log').open('xb');stderr=(d/'stderr.log').open('xb')
            r={'attempt':str(d),'label':label,'argv':argv,'cwd':str(V2),'started_utc':now(),'started_monotonic':time.perf_counter(),'timeout_seconds':limit,'status':'launching','source_files':{s:sha(s) for s in argv if Path(s).is_file()},'parent_pid':os.getpid(),'pid':None,'process_create_time':None,'returncode':None,'stdout_path':str(d/'stdout.log'),'stderr_path':str(d/'stderr.log'),'sampled_peak_RSS_bytes':None}
            save(d/'receipt.json',r)
            p=None
            try:
                p=subprocess.Popen(argv,cwd=V2,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
                r.update(pid=p.pid,process_create_time=psutil.Process(p.pid).create_time(),status='running')
                save(d/'receipt.json',r);save(self.active,r)
                self.children[p.pid]=(p,r,stdout,stderr)
                return p.pid
            except Exception as e:
                if p is not None:
                    if p.poll() is None:p.kill()
                    r['returncode']=p.wait(timeout=5)
                    r['pid']=p.pid
                stdout.close();stderr.close();r.update(status='launch_failed',error=repr(e),ended_utc=now());save(d/'receipt.json',r);raise
        finally:os.close(fd);self.guard.unlink()
    def finish(self,pid):
        p,r,stdout,stderr=self.children[pid];peak=0;timedout=False
        try:
            while p.poll() is None:
                if time.perf_counter()-r['started_monotonic']>r['timeout_seconds']:
                    timedout=True
                    try:
                        for child in psutil.Process(pid).children(recursive=True):child.kill()
                    except psutil.NoSuchProcess:pass
                    p.kill();break
                try:
                    proc=psutil.Process(pid);rss=proc.memory_info().rss
                    for child in proc.children(recursive=True):rss+=child.memory_info().rss
                    peak=max(peak,rss)
                except psutil.NoSuchProcess:pass
                time.sleep(.02)
            rc=p.wait(timeout=5)
        finally:stdout.close();stderr.close()
        r.update(status='timed_out' if timedout else ('complete' if rc==0 else 'failed'),returncode=rc,ended_utc=now(),elapsed_seconds=time.perf_counter()-r['started_monotonic'],sampled_peak_RSS_bytes=peak or None,stdout_sha256=sha(r['stdout_path']),stderr_sha256=sha(r['stderr_path']))
        d=Path(r['attempt']);save(d/'receipt.json',r)
        active=json.loads(self.active.read_text(encoding='utf-8'));assert active['pid']==pid and active['attempt']==str(d)
        self.active.unlink();del self.children[pid];return r
    def reconcile_terminal(self):
        state=self.inspect()
        if state['state']=='idle':return state
        if state['state']!='requires_terminal_reconciliation':raise Busy(state)
        r=state['record'];d=inside(r['attempt'])
        # Restarted monitor cannot obtain a return code for a reaped process. Preserve null.
        if r['pid'] in self.children:return self.finish(r['pid'])
        r.update(status='terminal_unobserved_after_monitor_restart',returncode=None,ended_observed_utc=now(),identity_snapshot=state)
        r['stdout_sha256']=sha(r['stdout_path']);r['stderr_sha256']=sha(r['stderr_path']);save(d/'receipt.json',r);self.active.unlink();return r
