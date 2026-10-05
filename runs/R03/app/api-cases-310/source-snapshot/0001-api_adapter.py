"""Black-box program adapter: HTTP requests and process restarts, raw traces retained."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
case=json.load(sys.stdin);assert case['case_id']=='api_journey'
fixture=json.loads((root/case['inputs']['fixture']).read_text())['fixtures'];db=a.out/'tickets.sqlite3';trace=[];starts=[];proc=None;stderr=None

def start():
 global proc,base,stderr
 stderr=(a.out/('server-'+str(len(starts))+'.log')).open('w')
 proc=subprocess.Popen([sys.executable,str(root/'challenges/ticket-desk/app.py'),'--database',str(db),'--port','0'],stdout=subprocess.PIPE,stderr=stderr,text=True)
 raw=proc.stdout.readline();info=json.loads(raw);starts.append(dict(argv=proc.args,pid=proc.pid,listening=info));base='http://127.0.0.1:'+str(info['listening'][1])
def stop():
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 if starts:starts[-1]['exit_code']=proc.returncode
 if stderr:stderr.close()
def request(method,path,data=None,expected=200):
 req=Request(base+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json'})
 try:
  with urlopen(req,timeout=8) as r:status=r.status;body=json.load(r)
 except HTTPError as e:status=e.code;body=json.load(e)
 trace.append(dict(method=method,path=path,input=data,status=status,body=body))
 assert status==expected,(status,body,expected)
 return body
def digest():return hashlib.sha256(db.read_bytes()).hexdigest()
checks=[]
try:
 start();tickets=[request('POST','/api/tickets',f,201)['ticket'] for f in fixture];assert [t['title'] for t in tickets]==[f['title'] for f in fixture];checks.append('create_two')
 before=digest();request('POST','/api/tickets',dict(title='',description='keep draft',priority='normal'),400);assert digest()==before;checks.append('validation_unchanged')
 found=request('GET','/api/tickets?q=%E6%89%93%E5%8D%B0&status=open');assert [t['id'] for t in found['tickets']]==[1];assert found['counts']==dict(open=2,in_progress=0,resolved=0);checks.append('search_filter')
 t=request('PATCH','/api/tickets/1',dict(status='in_progress',expected_version=1))['ticket'];assert t['status']=='in_progress' and t['version']==2;checks.append('transition')
 before=digest();r=request('PATCH','/api/tickets/1',dict(status='resolved',expected_version=1),409);assert r['ticket']==t and digest()==before;checks.append('stale_unchanged')
 request('PATCH','/api/tickets/1',dict(status='open',expected_version=2),400);assert digest()==before;checks.append('invalid_transition_unchanged')
 t=request('PATCH','/api/tickets/1',dict(status='resolved',expected_version=2))['ticket'];assert t['status']=='resolved'
 t=request('PATCH','/api/tickets/1',dict(status='open',expected_version=3))['ticket'];assert t['status']=='open' and t['version']==4;checks.append('resolve_reopen')
 history=request('GET','/api/tickets/1/history')['history'];assert [h['to_status'] for h in history]==['open','in_progress','resolved','open'];assert [h['version'] for h in history]==[1,2,3,4];checks.append('history')
 before_list=request('GET','/api/tickets');stop();start();after=request('GET','/api/tickets');assert before_list==after;assert request('GET','/api/tickets/1/history')['history']==history;checks.append('restart_persistence')
 result=dict(status='completed',output=dict(passed=True,checks=checks))
except BaseException as exc:
 result=dict(status='failed',output=dict(passed=False,checks=checks,error=str(exc)));raise
finally:
 stop();(a.out/'requests.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2)+'\n');(a.out/'processes.json').write_text(json.dumps(starts,indent=2)+'\n');(a.out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
