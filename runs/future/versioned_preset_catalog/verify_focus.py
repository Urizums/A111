"""Author observation of full Tab cycles; not a replacement independent verdict."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--target',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(a.target.resolve())))
threading.Thread(target=server.serve_forever,daemon=True).start();rows=[]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  for width in [1280,390,320]:
   for view in ['review','stock','reader']:
    page=browser.new_page(viewport={'width':width,'height':900})
    page.goto(f'http://127.0.0.1:{server.server_port}/')
    page.evaluate('(view)=>{document.querySelector(`[data-view="${view}"]`).click();document.querySelectorAll("details").forEach(e=>e.open=true)}',view)
    expected=page.evaluate('''() => [...document.querySelectorAll('a,button,input,textarea,select,summary,[tabindex]')].filter(e=>e.tabIndex>=0&&!e.disabled&&e.getClientRects().length>0&&getComputedStyle(e).visibility==='visible').map((e,i)=>{e.dataset.focusProbe=String(i);return String(i)})''')
    observed=[]
    for _ in range(len(expected)*2+4):
     page.keyboard.press('Tab')
     observed.append(page.evaluate('''()=>{const e=document.activeElement,s=getComputedStyle(e);return {tag:e.tagName,id:e.id,key:e.dataset.focusProbe??null,outline:s.outlineStyle,width:parseFloat(s.outlineWidth)}}'''))
    controls=[r for r in observed if r['key'] is not None]
    row={'width':width,'view':view,'expected':expected,'observed':observed,'all_reached':set(expected)<={r['key'] for r in controls},'all_control_focus_visible':bool(controls) and all(r['outline']!='none' and r['width']>=2.5 for r in controls),'document_exit_samples':sum(r['tag']=='BODY' for r in observed)}
    rows.append(row);page.close()
  browser.close()
finally:server.shutdown();server.server_close()
report={'scope':'Author observation, same v2 candidate; raw independent 74/2 remains unchanged and budget exhausted','checks':rows,'pass':all(r['all_reached'] and r['all_control_focus_visible'] for r in rows),'interpretation':'BODY at document exit is recorded separately; eligible controls must all be reached by actual Tab and have visible outline.'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'pass':report['pass'],'views':len(rows),'body_samples':sum(r['document_exit_samples'] for r in rows)}));raise SystemExit(0 if report['pass'] else 1)
