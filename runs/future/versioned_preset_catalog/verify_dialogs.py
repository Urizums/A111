"""Root regression of original rapid cancel/reopen/confirm journeys."""
import argparse,http.server,json,threading
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--target',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),partial(H,directory=str(a.target.resolve())));t=threading.Thread(target=s.serve_forever,daemon=True);t.start();report={'target':str(a.target),'cases':[],'errors':[]}
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(f'http://127.0.0.1:{s.server_port}/');page.locator('[data-record="R-041"]').click();page.locator('#review-approve').focus()
  for action in ['Escape','cancel','confirm']:
   page.keyboard.press('Enter');page.locator('#confirm').wait_for(state='visible')
   if action=='Escape':page.keyboard.press('Escape')
   elif action=='cancel':page.locator('#confirm-cancel').click()
   else:page.keyboard.press('Tab');page.keyboard.press('Enter')
   page.wait_for_function("!document.querySelector('#confirm').open")
  page.wait_for_function("document.querySelector('#record-state').textContent.includes('已通过示例')",timeout=2000);report['cases'].append({'id':'review-rapid-cancel-confirm','status':'pass','state':page.locator('#record-state').inner_text()})
  page.locator('.views [data-view="stock"]').click();page.locator('#quantity').fill('14');page.locator('#stock-form').evaluate('e=>e.requestSubmit()');page.wait_for_function("!document.querySelector('#stock-save').disabled");page.locator('#stock details summary').click();page.locator('#stock-incoming').click();page.locator('#quantity').fill('22');page.locator('#stock-note').fill('保留的草稿')
  for action in ['Escape','confirm']:
   page.locator('#stock-form').evaluate('e=>e.requestSubmit()');page.locator('#confirm').wait_for(state='visible')
   if action=='Escape':page.keyboard.press('Escape')
   else:page.locator('#confirm-ok').click()
   page.wait_for_function("!document.querySelector('#confirm').open")
  page.wait_for_function("!document.querySelector('#stock-save').disabled");stock=json.loads(page.evaluate("localStorage.getItem('forge-preset-stock-v1')"));assert stock['quantity']==22 and stock['note']=='保留的草稿';report['cases'].append({'id':'stock-cancel-resolve','status':'pass','record':stock})
  page.locator('.views [data-view="reader"]').click();page.locator('#annotation-open').click();page.locator('#annotation-input').fill('原始批注');page.locator('#annotation-save').click()
  for action in ['cancel','confirm']:
   page.locator('#annotation-delete').click();page.locator('#confirm').wait_for(state='visible')
   if action=='cancel':page.locator('#confirm-cancel').click()
   else:page.keyboard.press('Tab');page.keyboard.press('Enter')
   page.wait_for_function("!document.querySelector('#confirm').open")
  assert page.evaluate("localStorage.getItem('forge-preset-annotation-v1')") is None;assert page.locator('#annotation-saved').is_hidden();report['cases'].append({'id':'reader-cancel-keyboard-delete','status':'pass'});page.screenshot(path=str(a.out/'reader-after.png'));b.close()
except Exception as exc:report['errors'].append(repr(exc))
finally:s.shutdown();s.server_close();t.join();(a.out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if len(report['cases'])==3 and not report['errors'] else 1)
