#!/usr/bin/env python3
import json
import math
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

WORKER = Path(__file__).resolve().parent
CANDIDATE = Path('/workspace/A111/runs/future/versioned_preset_catalog/candidate/v2')
LOCK_PATH = Path('/workspace/A111/runs/future/versioned_preset_catalog/candidate-v2-lock.json')
BASE = 'http://127.0.0.1:8766/'

result = {
    'browser': {'name': 'Chromium', 'executable': '/usr/bin/chromium', 'version': None},
    'url_origin': BASE,
    'checks': [],
    'observations': [],
    'console_errors': [],
    'page_errors': [],
    'requests': [],
    'layout': [],
    'controls': [],
    'focus': [],
    'contrast': [],
    'journey_errors': [],
    'screenshots': [],
    'local_storage': [],
}

def check(name, passed, details=None):
    result['checks'].append({'name': name, 'status': 'pass' if bool(passed) else 'fail', 'details': details})

def note(name, value):
    result['observations'].append({'name': name, 'value': value})

def record_storage(page, label, keys):
    vals = page.evaluate('(ks) => Object.fromEntries(ks.map(k => [k, localStorage.getItem(k)]))', keys)
    result['local_storage'].append({'label': label, 'values': vals})
    return vals

def contrast_ratio(fg, bg):
    def rgb(css):
        vals = [float(x) for x in re.findall(r'[0-9.]+', css)[:3]]
        if len(vals) != 3:
            return None
        out = []
        for v in vals:
            v /= 255.0
            out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
    a, b = rgb(fg), rgb(bg)
    if a is None or b is None:
        return None
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)

def capture_contrast(page, label):
    vals = page.evaluate('''() => {
      const selectors = ['h1','h2','.eyebrow','.muted','.hint','.pill','.small-heading','.status','.error','.queue button strong','.queue .meta','.queue .state','button','label','.contents a','.reading-column p','.annotation','footer','.local-note'];
      const out=[];
      function visible(e){return !!(e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden');}
      function opaque(s){const m=s.match(/rgba?\\(([^)]+)\\)/); if(!m)return false; const parts=m[1].split(',').map(x=>x.trim()); return parts.length < 4 || parseFloat(parts[3]) > .95;}
      function bg(e){for(let n=e;n;n=n.parentElement){const c=getComputedStyle(n).backgroundColor;if(opaque(c))return c;}return getComputedStyle(document.body).backgroundColor;}
      const seen=new Set();
      for(const sel of selectors){for(const e of document.querySelectorAll(sel)){if(!visible(e))continue; const t=(e.innerText||e.value||'').trim().replace(/\\s+/g,' ');if(!t)continue; const fg=getComputedStyle(e).color, back=bg(e), key=fg+'|'+back; if(seen.has(key))continue;seen.add(key);out.push({selector:sel,text:t.slice(0,100),foreground:fg,background:back});}}
      return out;
    }''')
    rows=[]
    for v in vals:
        ratio=contrast_ratio(v['foreground'],v['background'])
        rows.append({**v,'ratio':round(ratio,3) if ratio is not None else None})
    result['contrast'].append({'label':label,'samples':rows,'below_4_5':[x for x in rows if x['ratio'] is not None and x['ratio'] < 4.5]})

def switch_view(page, view):
    page.locator(f'.views button[data-view="{view}"]').click()
    page.locator(f'main > section#{view}').wait_for(state='visible')

def visible_text(page, selector):
    return page.locator(selector).inner_text().strip()

def do_review(page):
    try:
        page.goto(BASE, wait_until='networkidle')
        page.locator('#review-list button[data-record]').first.wait_for(state='visible')
        initial = page.locator('#review-list button[data-record]').count()
        check('review: three original rows load', initial == 3, {'count': initial})
        page.locator('#review-search').fill('no-such-record')
        page.locator('#review-empty').wait_for(state='visible')
        empty = page.locator('#review-list button[data-record]').count()
        check('review: unmatched filter has empty state', empty == 0 and page.locator('#review-empty').is_visible(), {'rows': empty, 'empty_text': visible_text(page, '#review-empty')})
        page.locator('#review-clear').click()
        restored = page.locator('#review-list button[data-record]').count()
        check('review: clear restores records', restored == 3 and page.locator('#review-search').input_value() == '', {'count': restored})
        page.locator('#review-search').fill('北侧')
        filtered = page.locator('#review-list button[data-record]').count()
        check('review: title filter returns original R-041', filtered == 1 and page.locator('#review-list button[data-record="R-041"]').is_visible(), {'count': filtered})
        page.locator('#review-clear').click()
        page.locator('#review-list button[data-record="R-041"]').click()
        check('review: original R-041 selected', visible_text(page, '#record-title') == '北侧展厅照明调整', {'title': visible_text(page, '#record-title'), 'active': page.evaluate('document.activeElement.id')})
        trigger = page.locator('#review-approve')
        trigger.focus()
        page.keyboard.press('Enter')
        page.locator('#confirm').wait_for(state='visible')
        check('review: keyboard opens confirmation with cancel focused', page.evaluate("document.querySelector('#confirm').open") and page.evaluate("document.activeElement.id") == 'confirm-cancel', {'active': page.evaluate('document.activeElement.id')})
        page.keyboard.press('Escape')
        page.wait_for_function("!document.querySelector('#confirm').open")
        check('review: Escape cancels and returns focus', page.evaluate('document.activeElement.id') == 'review-approve', {'active': page.evaluate('document.activeElement.id')})
        trigger.focus()
        page.keyboard.press('Enter')
        page.locator('#confirm').wait_for(state='visible')
        page.locator('#confirm-cancel').click()
        page.wait_for_function("!document.querySelector('#confirm').open")
        check('review: cancel button leaves state unchanged and returns focus', page.evaluate('document.activeElement.id') == 'review-approve' and '待审阅' in visible_text(page, '#record-state'), {'active': page.evaluate('document.activeElement.id'), 'state': visible_text(page, '#record-state')})
        trigger.focus()
        page.keyboard.press('Enter')
        page.locator('#confirm').wait_for(state='visible')
        page.keyboard.press('Tab')
        active = page.evaluate('document.activeElement.id')
        page.keyboard.press('Enter')
        page.wait_for_function("!document.querySelector('#confirm').open")
        page.wait_for_function("document.querySelector('#review-status').textContent.includes('已通过示例')")
        states = page.locator('#review-list button[data-record]').evaluate_all("els => els.map(e => ({id:e.dataset.record,text:e.innerText}))")
        check('review: Tab reaches confirm and confirmation approves R-041', active == 'confirm-ok' and '已通过示例' in visible_text(page, '#record-state'), {'tab_active': active, 'state': visible_text(page, '#record-state')})
        unrelated = [x for x in states if x['id'] in ('R-042','R-043')]
        check('review: unrelated rows retained pending', len(unrelated) == 2 and all('待审阅' in x['text'] for x in unrelated), {'unrelated': unrelated})
        capture_contrast(page, 'review approved status')
        page.locator('section#review details.state-examples summary').click()
        page.locator('#review-error').click()
        retryable = visible_text(page, '#review-status')
        page.locator('#review-retry').click()
        check('review: retryable read error retains rows and recovers', '读取失败' in retryable and page.locator('#review-list button[data-record]').count() == 3 and page.locator('#review-retry').is_hidden(), {'error': retryable, 'rows': page.locator('#review-list button[data-record]').count()})
        page.set_viewport_size({'width':1280,'height':900})
        path=WORKER/'screenshots/review-1280.png'
        page.screenshot(path=str(path),full_page=True)
        result['screenshots'].append({'path':str(path),'view':'review','width':1280,'height':900})
    except Exception as exc:
        result['journey_errors'].append({'journey':'review','error':repr(exc)})

def do_stock(page):
    try:
        switch_view(page,'stock')
        page.locator('#quantity').fill('12x')
        page.locator('#stock-save').click()
        invalid_text=visible_text(page,'#quantity-error')
        check('stock: invalid integer rejected with input preserved', page.locator('#quantity').input_value()=='12x' and page.locator('#quantity').get_attribute('aria-invalid')=='true' and '请输入' in invalid_text, {'input':page.locator('#quantity').input_value(),'error':invalid_text})
        capture_contrast(page,'stock invalid count')
        page.locator('#quantity').fill('14')
        page.locator('#stock-note').fill('首次实盘记录')
        page.locator('#quantity').focus()
        page.keyboard.press('Enter')
        busy=page.locator('#stock-save').is_disabled() and page.locator('#stock-form').get_attribute('aria-busy')=='true'
        page.evaluate("document.querySelector('#stock-form').requestSubmit()")
        page.wait_for_function("!document.querySelector('#stock-save').disabled")
        raw=page.evaluate("localStorage.getItem('forge-preset-stock-v1')")
        data=json.loads(raw) if raw else None
        check('stock: busy state blocks duplicate submission', busy and data and data['version']==1 and data['quantity']==14, {'busy_seen':busy,'stored':data})
        record_storage(page,'stock after save',['forge-preset-stock-v1'])
        page.reload(wait_until='networkidle')
        switch_view(page,'stock')
        restored={'quantity':page.locator('#quantity').input_value(),'note':page.locator('#stock-note').input_value(),'status':visible_text(page,'#stock-status')}
        check('stock: actual localStorage value restores after reload', restored['quantity']=='14' and restored['note']=='首次实盘记录' and '恢复' in restored['status'], restored)
        page.locator('#stock-save').wait_for(state='visible')
        page.locator('section#stock details.state-examples summary').click()
        page.locator('#stock-incoming').click()
        page.locator('#quantity').fill('22')
        page.locator('#stock-note').fill('保留的草稿')
        page.locator('#stock-form').evaluate("e => e.requestSubmit()")
        page.locator('#confirm').wait_for(state='visible')
        check('stock: conflict sample opens confirmation and retains draft', page.locator('#quantity').input_value()=='22' and page.locator('#stock-note').input_value()=='保留的草稿' and '另一份' in visible_text(page,'#confirm-body'), {'quantity':page.locator('#quantity').input_value(),'note':page.locator('#stock-note').input_value(),'dialog':visible_text(page,'#confirm-body')})
        page.keyboard.press('Escape')
        page.wait_for_function("!document.querySelector('#confirm').open")
        check('stock: cancel conflict preserves draft', page.locator('#quantity').input_value()=='22' and page.locator('#stock-note').input_value()=='保留的草稿' and page.evaluate('document.activeElement.id') in ('quantity','stock-note'), {'quantity':page.locator('#quantity').input_value(),'note':page.locator('#stock-note').input_value(),'active':page.evaluate('document.activeElement.id')})
        page.locator('#stock-form').evaluate("e => e.requestSubmit()")
        page.locator('#confirm').wait_for(state='visible')
        page.locator('#confirm-ok').click()
        page.wait_for_function("!document.querySelector('#stock-save').disabled")
        raw=page.evaluate("localStorage.getItem('forge-preset-stock-v1')")
        data=json.loads(raw) if raw else None
        check('stock: conflict resolution saves draft over local sample', data and data['quantity']==22 and data['note']=='保留的草稿' and data['version']==3, {'stored':data,'status':visible_text(page,'#stock-status')})
        capture_contrast(page,'stock conflict resolution')
        record_storage(page,'stock after conflict resolution',['forge-preset-stock-v1'])
        page.set_viewport_size({'width':390,'height':844})
        path=WORKER/'screenshots/stock-390.png'
        page.screenshot(path=str(path),full_page=True)
        result['screenshots'].append({'path':str(path),'view':'stock','width':390,'height':844})
    except Exception as exc:
        result['journey_errors'].append({'journey':'stock','error':repr(exc)})

def do_reader(page):
    try:
        switch_view(page,'reader')
        page.locator('.contents a[href="#record"]').click()
        check('reader: contents navigation targets and focuses section', page.evaluate('location.hash')=='#record' and page.evaluate('document.activeElement.id')=='record', {'hash':page.evaluate('location.hash'),'active':page.evaluate('document.activeElement.id')})
        page.locator('.contents a[href="#observe"]').click()
        page.locator('#annotation-open').click()
        page.locator('#annotation-input').fill('第一版批注')
        page.locator('#annotation-form').evaluate("e => e.requestSubmit()")
        saved=page.evaluate("localStorage.getItem('forge-preset-annotation-v1')")
        check('reader: create annotation saves locally', saved=='第一版批注' and page.locator('#annotation-saved').is_visible() and visible_text(page,'#annotation-text')=='第一版批注', {'stored':saved,'visible':visible_text(page,'#annotation-text')})
        record_storage(page,'reader after annotation save',['forge-preset-annotation-v1'])
        page.reload(wait_until='networkidle')
        switch_view(page,'reader')
        check('reader: annotation restores after reload', page.locator('#annotation-saved').is_visible() and visible_text(page,'#annotation-text')=='第一版批注' and page.evaluate("localStorage.getItem('forge-preset-annotation-v1')")=='第一版批注', {'visible':page.locator('#annotation-saved').is_visible(),'text':visible_text(page,'#annotation-text')})
        page.locator('section#reader details.state-examples summary').click()
        page.locator('#annotation-error').click()
        page.locator('#annotation-input').fill('重试后的第二版批注')
        page.locator('#annotation-form').evaluate("e => e.requestSubmit()")
        failed_value=page.locator('#annotation-input').input_value()
        failed_status=visible_text(page,'#annotation-status')
        previous=page.evaluate("localStorage.getItem('forge-preset-annotation-v1')")
        check('reader: retryable simulated failure preserves draft', failed_value=='重试后的第二版批注' and '草稿已保留' in failed_status and previous=='第一版批注', {'draft':failed_value,'status':failed_status,'stored_before_retry':previous})
        page.locator('#annotation-form').evaluate("e => e.requestSubmit()")
        latest=page.evaluate("localStorage.getItem('forge-preset-annotation-v1')")
        check('reader: retry persists preserved draft', latest=='重试后的第二版批注' and visible_text(page,'#annotation-text')=='重试后的第二版批注', {'stored':latest,'visible':visible_text(page,'#annotation-text')})
        capture_contrast(page,'reader saved annotation')
        page.locator('#annotation-edit').click()
        page.locator('#annotation-input').fill('取消编辑的临时草稿')
        page.locator('#annotation-cancel').click()
        check('reader: cancel edit leaves saved annotation unchanged', page.locator('#annotation-form').is_hidden() and page.evaluate("localStorage.getItem('forge-preset-annotation-v1')")=='重试后的第二版批注', {'saved':page.evaluate("localStorage.getItem('forge-preset-annotation-v1')"),'form_hidden':page.locator('#annotation-form').is_hidden()})
        page.set_viewport_size({'width':320,'height':800})
        path=WORKER/'screenshots/reader-320.png'
        page.screenshot(path=str(path),full_page=True)
        result['screenshots'].append({'path':str(path),'view':'reader','width':320,'height':800})
        page.locator('#annotation-delete').click()
        page.locator('#confirm').wait_for(state='visible')
        page.locator('#confirm-cancel').click()
        page.wait_for_function("!document.querySelector('#confirm').open")
        check('reader: delete cancellation preserves annotation and restores focus', page.locator('#annotation-saved').is_visible() and page.evaluate("localStorage.getItem('forge-preset-annotation-v1')")=='重试后的第二版批注' and page.evaluate('document.activeElement.id')=='annotation-delete', {'saved_visible':page.locator('#annotation-saved').is_visible(),'active':page.evaluate('document.activeElement.id')})
        page.locator('#annotation-delete').click()
        page.locator('#confirm').wait_for(state='visible')
        page.keyboard.press('Tab')
        tab_active=page.evaluate('document.activeElement.id')
        page.keyboard.press('Enter')
        page.wait_for_function("!document.querySelector('#confirm').open")
        check('reader: keyboard confirms deletion', tab_active=='confirm-ok' and page.evaluate("localStorage.getItem('forge-preset-annotation-v1')") is None and page.locator('#annotation-saved').is_hidden(), {'tab_active':tab_active,'storage':page.evaluate("localStorage.getItem('forge-preset-annotation-v1')"),'saved_hidden':page.locator('#annotation-saved').is_hidden()})
    except Exception as exc:
        result['journey_errors'].append({'journey':'reader','error':repr(exc)})

def do_responsive_and_access(page):
    sizes=[(1280,900),(390,844),(320,800)]
    for view in ('review','stock','reader'):
        switch_view(page,view)
        for width,height in sizes:
            page.set_viewport_size({'width':width,'height':height})
            page.wait_for_timeout(80)
            metrics=page.evaluate('''() => ({innerWidth:innerWidth,documentWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth,clientWidth:document.documentElement.clientWidth})''')
            metrics.update({'view':view,'target_width':width})
            result['layout'].append(metrics)
            check(f'access: {view} at {width}px has no horizontal overflow', metrics['documentWidth']<=width and metrics['bodyWidth']<=width, metrics)
            control_data=page.locator(f'main > section#{view}').evaluate('''root => Array.from(root.querySelectorAll('button,input,textarea,select,a')).filter(e=>e.getClientRects().length>0).map(e=>({tag:e.tagName.toLowerCase(),id:e.id,text:(e.innerText||'').trim(),aria:e.getAttribute('aria-label'),placeholder:e.getAttribute('placeholder'),labels:e.labels?Array.from(e.labels).map(x=>x.innerText.trim()):[],href:e.getAttribute('href')}))''')
            unnamed=[]
            unlabeled=[]
            for c in control_data:
                result['controls'].append({'view':view,'width':width,**c})
                if c['tag'] in ('button','a') and not (c['text'] or c['aria']): unnamed.append(c)
                if c['tag'] in ('input','textarea','select') and not (c['labels'] or c['aria'] or c['placeholder']): unlabeled.append(c)
            check(f'access: {view} at {width}px has named visible controls', not unnamed and not unlabeled, {'unnamed':unnamed,'unlabeled':unlabeled})
            page.evaluate('document.activeElement && document.activeElement.blur && document.activeElement.blur()')
            page.keyboard.press('Tab')
            focus=page.evaluate('''() => {const e=document.activeElement,s=getComputedStyle(e);return {tag:e.tagName,id:e.id,className:e.className,text:(e.innerText||'').trim().slice(0,60),outlineStyle:s.outlineStyle,outlineWidth:s.outlineWidth,outlineColor:s.outlineColor}}''')
            focus.update({'view':view,'width':width})
            result['focus'].append(focus)
            width_px=float(focus['outlineWidth'].replace('px','')) if focus['outlineWidth'].endswith('px') else 0
            check(f'access: {view} at {width}px shows keyboard focus', focus['outlineStyle']!='none' and width_px>=2.5, focus)
    # Contrast samples from the live UI for the three currently designed role sets.
    for view in ('review','stock','reader'):
        switch_view(page,view)
        page.set_viewport_size({'width':1280,'height':900})
        capture_contrast(page,view+' base rendered text')
    # Reduced motion only removes optional transitions/scroll animation; all view text remains.
    page.emulate_media(reduced_motion='no-preference')
    baselines={}
    for view in ('review','stock','reader'):
        switch_view(page,view)
        baselines[view]=page.locator(f'main > section#{view}').inner_text()
    page.emulate_media(reduced_motion='reduce')
    for view in ('review','stock','reader'):
        switch_view(page,view)
        text_now=page.locator(f'main > section#{view}').inner_text()
        durations=page.locator(f'main > section#{view}').evaluate("e => getComputedStyle(e).transitionDuration")
        scroll=page.evaluate("getComputedStyle(document.documentElement).scrollBehavior")
        same=text_now==baselines[view]
        check(f'access: reduced motion retains {view} information',same,{'text_length_before':len(baselines[view]),'text_length_after':len(text_now),'transition_duration':durations,'scroll_behavior':scroll})
        check(f'access: reduced motion disables {view} transition', all(float(x.strip().replace('s',''))==0 for x in durations.split(',')), {'transition_duration':durations})
        check(f'access: reduced motion avoids smooth scrolling for {view}',scroll!='smooth',{'scroll_behavior':scroll})

# Static catalog and paired color-token analysis.
catalog=json.loads((CANDIDATE/'catalog.json').read_text())
expected={'review','stock','reader'}
variants=catalog.get('variants',[])
variant_ids={v.get('id') for v in variants}
check('catalog: schema and version are explicit',catalog.get('schema')=='forge-preset-catalog/1' and catalog.get('version')=='1.0.1',{'schema':catalog.get('schema'),'version':catalog.get('version'),'source_revision':catalog.get('source_revision')})
candidate_lock=json.loads(LOCK_PATH.read_text())
lock_match=all(__import__('hashlib').sha256((Path('/workspace/A111')/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in candidate_lock.get('files',[]))
check('catalog: v2 candidate lock matches every frozen source',candidate_lock.get('candidate')=='v2' and len(candidate_lock.get('files',[]))==4 and lock_match,{'candidate':candidate_lock.get('candidate'),'files':candidate_lock.get('files'),'lock_match':lock_match})
check('catalog: all three original task/platform variants exist',variant_ids==expected,{'variant_ids':sorted(variant_ids),'variants':variants})
check('catalog: sources have hashes and observation-only reuse scope',bool(catalog.get('sources')) and all(re.fullmatch(r'[0-9a-f]{64}',s.get('snapshot_sha256','')) and s.get('reuse')=='observation_only_no_assets_or_code_reused' for s in catalog.get('sources',[])),{'source_count':len(catalog.get('sources',[])),'sources':catalog.get('sources',[])})
check('catalog: reuse scope is stated',bool(catalog.get('reuse')) and 'Original authored code/tokens' in catalog.get('reuse',''),{'reuse':catalog.get('reuse')})
check('catalog: paired semantic tokens are provided',bool(catalog.get('semantic_pairs')) and all({'foreground','background'}<=set(x) for x in catalog.get('semantic_pairs',{}).values()),{'pairs':catalog.get('semantic_pairs')})

def hex_rgb(s):
    return tuple(int(s[i:i+2],16)/255 for i in (1,3,5))
def hex_lum(s):
    vals=[]
    for v in hex_rgb(s): vals.append(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)
    return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]
semantic_ratios={}
for name,pair in catalog.get('semantic_pairs',{}).items():
    a,b=hex_lum(pair['foreground']),hex_lum(pair['background'])
    semantic_ratios[name]=round((max(a,b)+.05)/(min(a,b)+.05),3)
check('catalog: all paired token colors meet 4.5:1',bool(semantic_ratios) and min(semantic_ratios.values())>=4.5,semantic_ratios)
check('catalog: each variant names layout and states',len(variants)==3 and all(v.get('layout') and v.get('states') for v in variants),{'states':{v.get('id'):v.get('states') for v in variants}})
check('catalog: responsive browser scope is explicit and Android is unverified',all('web' in v.get('platform','') for v in variants) and 'unverified' in next(v['platform'] for v in variants if v['id']=='stock'),{'platforms':{v.get('id'):v.get('platform') for v in variants}})
check('catalog: default and reduced motion are defined',bool(catalog.get('motion',{}).get('default')) and bool(catalog.get('motion',{}).get('reduced')),catalog.get('motion'))
check('catalog: limitations deny unsupported authority/certification claims',bool(catalog.get('limitations')) and any('physical Android' in x for x in catalog.get('limitations',[])),catalog.get('limitations'))

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    result['browser']['version']=browser.version
    context=browser.new_context(viewport={'width':1280,'height':900},device_scale_factor=1)
    page=context.new_page()
    page.on('console',lambda msg: result['console_errors'].append({'type':msg.type,'text':msg.text}) if msg.type=='error' else None)
    page.on('pageerror',lambda exc: result['page_errors'].append(str(exc)))
    page.on('request',lambda req: result['requests'].append(req.url))
    do_review(page)
    do_stock(page)
    do_reader(page)
    do_responsive_and_access(page)
    check('browser: only loopback requests were issued',all(u.startswith(BASE) for u in result['requests']),{'requests':result['requests']})
    check('browser: no console errors or uncaught page errors',not result['console_errors'] and not result['page_errors'],{'console_errors':result['console_errors'],'page_errors':result['page_errors']})
    context.close()
    browser.close()

result['summary']={
    'passed':sum(c['status']=='pass' for c in result['checks']),
    'failed':sum(c['status']=='fail' for c in result['checks']),
    'journey_errors':len(result['journey_errors']),
    'console_errors':len(result['console_errors']),
    'page_errors':len(result['page_errors']),
    'requests':result['requests'],
}
(WORKER/'browser-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
print('result:',WORKER/'browser-results.json')
