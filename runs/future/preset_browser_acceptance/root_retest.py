"""Root regression: preserved worker harness with only three location constants rebound."""
import argparse,ast,contextlib,hashlib,http.server,io,json,threading
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright

p=argparse.ArgumentParser();p.add_argument('--target',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--nav-only',action='store_true');a=p.parse_args()
a.target=a.target.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(a.target)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}/ui-presets.html'
try:
    harness=Path(__file__).parent/'independent/worker/validate_presets.py'
    if not a.nav_only:
        for name in ['attempt-1-results.json','attempt-2-results.json']:
            (a.out/name).write_bytes((harness.parent/name).read_bytes())
        tree=ast.parse(harness.read_text());locations={'ROOT':f'Path({str(a.out)!r})','TARGET':f'Path({str(a.target)!r})','URL':repr(url)}
        for node in tree.body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in locations:
                node.value=ast.parse(locations[node.targets[0].id],mode='eval').body
        ast.fix_missing_locations(tree)
        (a.out/'harness-binding.json').write_text(json.dumps({'source':str(harness),'sha256':hashlib.sha256(harness.read_bytes()).hexdigest(),'changes':locations,'scope':'Author replay, original check bodies unchanged; copied attempt-1/2 are immutable imported worker history, not Root attempts; not a new independent result'},indent=2)+'\n')
        with (a.out/'harness-stdout.txt').open('w') as output,contextlib.redirect_stdout(output):exec(compile(tree,str(harness),'exec'),{'__name__':'__main__','__file__':str(harness)})
    checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        for width in [390,320,680,1440]:
            page=browser.new_page(viewport={'width':width,'height':1000},reduced_motion='reduce')
            page.route('**/favicon.ico',lambda route:route.fulfill(status=204,body=''))
            page.goto(url)
            for _ in range(6):page.keyboard.press('Tab')
            observed=page.evaluate('''() => {const a=document.activeElement,nav=document.querySelector('.primary-nav'),r=a.getBoundingClientRect(),n=nav.getBoundingClientRect(),s=getComputedStyle(a);return {name:a.innerText,left:r.left,right:r.right,top:r.top,bottom:r.bottom,navLeft:n.left,navRight:n.right,navTop:n.top,navBottom:n.bottom,outline:s.outlineWidth,offset:s.outlineOffset,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth}}''')
            ring=float(observed['outline'].replace('px',''))+float(observed['offset'].replace('px',''))
            ok=observed['name']=='Preferences' and observed['left']-ring>=0 and observed['right']+ring<=width and observed['scrollWidth']<=width
            if width<=680:ok=ok and observed['left']-ring>=observed['navLeft']-1 and observed['right']+ring<=observed['navRight']+1
            page.screenshot(path=str(a.out/f'focus-{width}.png'),full_page=False)
            page.keyboard.press('Enter');ok=ok and page.url.endswith('#settings')
            checks.append({'width':width,'status':'pass' if ok else 'fail','observed':observed,'enter_activates':page.url.endswith('#settings')})
            page.close()
        browser.close()
    main=json.loads((a.out/'results.json').read_text()) if (a.out/'results.json').exists() else None
    report={'scope':'Root source regression, not independent acceptance','source':str(a.target),'files':[{'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in a.target.glob('ui-presets.*')],'navigation':checks,'preserved_main_harness':main,'all_nav_pass':all(c['status']=='pass' for c in checks),'all_main_pass':main is None or (bool(main['outcomes']) and all(c['status']=='passed' for c in main['outcomes']) and not main['raw_errors'])}
    (a.out/'root-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'navigation':checks,'main_harness_run':not a.nav_only},ensure_ascii=False))
    raise SystemExit(0 if report['all_nav_pass'] and report['all_main_pass'] else 1)
finally:server.shutdown();server.server_close();thread.join()
