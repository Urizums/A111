"""Start the original preset target; this is a capability/render probe, not full UI acceptance."""
import functools,hashlib,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[3];out=Path(__file__).parent
assets=root/'skills/design-product-experience/assets'
record={'scope':'Original preset initial rendering and palette switch only; full original journeys remain in progress','sources':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [assets/'ui-presets.html',assets/'ui-presets.css']],'historical_capability':'evidence/history/forge-design-upgrade/browser-capability.json','current_capability':'runs/R04/capability-probe/environment-status.json','external_effects':False,'errors':[]}
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(assets)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.on('pageerror',lambda e:record['errors'].append(str(e)))
  record['browser']=browser.version;record['url']='http://127.0.0.1:'+str(server.server_port)+'/ui-presets.html';page.goto(record['url']);expect(page.get_by_role('heading',name='Run workspace')).to_be_visible();expect(page.locator('#run-list tr')).to_have_count(3);page.screenshot(path=str(out/'original-light.png'),full_page=True)
  page.locator('#palette-choice').select_option('night');expect(page.locator('html')).to_have_attribute('data-palette','night');page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'original-night-390.png'),full_page=True);record['layout']=page.evaluate('()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth})');record['checks']=['original page rendered','three original rows present','night palette selected'];record['passed']=not record['errors'];browser.close()
finally:server.shutdown();server.server_close();(out/'first-step-result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False))
