"""Root observes remaining UI states from retained data; no repair of old harness."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from urllib.request import Request,urlopen
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[3];out=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);a=p.parse_args()
seed=a.database;db=out/'continued.sqlite3';assert not db.exists();shutil.copy2(seed,db)
record=dict(source_database=str(seed),source_sha256=hashlib.sha256(seed.read_bytes()).hexdigest(),grader='Root, not independent',checks=[],requests=[],screenshots=[],errors=[])
assert hashlib.sha256(db.read_bytes()).hexdigest()==record['source_sha256']
log=(out/'server.log').open('w');proc=subprocess.Popen([sys.executable,str(root/'challenges/ticket-desk/app.py'),'--database',str(db),'--port','0'],stdout=subprocess.PIPE,stderr=log,text=True)
try:
 info=json.loads(proc.stdout.readline());url='http://127.0.0.1:'+str(info['listening'][1]);record['server']=info
 def api(method,path,data=None):
  req=Request(url+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  with urlopen(req,timeout=10) as response:body=json.load(response)
  record['requests'].append(dict(method=method,path=path,input=data,output=body));return body
 labels={'open':'待处理','in_progress':'处理中','resolved':'已解决'};next_status={'open':'in_progress','in_progress':'resolved','resolved':'open'}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  record['browser']=browser.version;context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda e:record['errors'].append(str(e)))
  page.goto(url);expect(page.locator('.ticket')).to_have_count(2)
  base=api('GET','/api/tickets')['tickets'];ticket=next(t for t in base if t['id']==1);row=page.locator('article[data-id="1"]')
  expect(row.locator('.state')).to_have_text(labels[ticket['status']])
  changed=api('PATCH','/api/tickets/1',dict(status=next_status[ticket['status']],expected_version=ticket['version']))['ticket']
  row.locator('button').click();expect(page.locator('#list-error')).to_contain_text('工单已被其他操作更新');expect(row.locator('.state')).to_have_text(labels[changed['status']]);current=next(t for t in api('GET','/api/tickets')['tickets'] if t['id']==1);assert current==changed
  page.screenshot(path=str(out/'desktop-conflict.png'),full_page=True);record['screenshots'].append('desktop-conflict.png');record['checks'].append('conflict_shown_and_newer_state_preserved')
  for i in range(3):
   expected=next_status[current['status']];row.locator('button').click();expect(row.locator('.state')).to_have_text(labels[expected]);updated=next(t for t in api('GET','/api/tickets')['tickets'] if t['id']==1);assert updated['status']==expected and updated['version']==current['version']+1;current=updated
  record['checks'].append('browser_status_cycle_resolve_and_reopen')
  row.locator('summary').click();expect(row.locator('ol li')).to_have_count(current['version']);record['checks'].append('visible_durable_history')
  page.locator('#title').focus();page.keyboard.press('Tab');assert page.locator('#description').evaluate('(e)=>e===document.activeElement');focus=page.locator('#description').evaluate('(e)=>({style:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth})');assert focus['style']!='none' and focus['width']!='0px';record['focus']=focus;record['checks'].append('keyboard_focus_visible')
  assert page.evaluate('()=>matchMedia("(prefers-reduced-motion: reduce)").matches');record['checks'].append('reduced_motion_active_and_operable')
  page.screenshot(path=str(out/'desktop-complete.png'),full_page=True);record['screenshots'].append('desktop-complete.png')
  page.set_viewport_size({'width':390,'height':844});page.locator('#queue').scroll_into_view_if_needed();expect(row.locator('button')).to_be_visible();sizes=page.evaluate('()=>({scroll:document.documentElement.scrollWidth,width:innerWidth})');assert sizes['scroll']<=sizes['width'];record['mobile']=sizes;record['checks'].append('390px_no_horizontal_overflow')
  page.screenshot(path=str(out/'mobile-complete.png'),full_page=True);record['screenshots'].append('mobile-complete.png')
  page.locator('#search').fill('没有这张工单');page.get_by_role('button',name='搜索',exact=True).click();expect(page.locator('#empty')).to_be_visible();record['checks'].append('mobile_empty_feedback')
  page.locator('#search').fill('打印队列卡住');page.get_by_role('button',name='搜索',exact=True).click();expect(page.locator('.ticket')).to_have_count(1);record['checks'].append('mobile_search_recovery')
  record['final_tickets']=api('GET','/api/tickets');assert not record['errors'];context.close();browser.close()
 record['passed']=True
except BaseException as e:
 record['passed']=False;record['failure']=repr(e);raise
finally:
 proc.terminate();proc.wait(timeout=10);log.close();record['server_exit_code']=proc.returncode
 record['product_sources']=[dict(path=str(f.relative_to(root)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted((root/'challenges/ticket-desk').glob('*')) if f.suffix in ['.py','.js','.html','.css']]
 (out/'observations.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=record['passed'],checks=record['checks'],browser=record.get('browser')),ensure_ascii=False))
