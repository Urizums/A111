"""Two real-client races against unchanged HTTP/SQLite application."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent / 'validation-repair-1'
OUT.mkdir(exist_ok=False)
DB = OUT / 'tickets.sqlite3'
fixture = json.loads((OUT.parent/'input.json').read_text())
record = dict(scope='Two-client correctness, not a load benchmark', checks=[], http=[],
              browser=[], processes=[], errors=[], source_hashes={}, timings={})
for name in ['app.py', 'app.js', 'index.html', 'style.css']:
    record['source_hashes'][name] = hashlib.sha256((ROOT/'challenges/ticket-desk'/name).read_bytes()).hexdigest()
proc = None
log = None


def start():
    global proc, log, url
    log = (OUT/('server-'+str(len(record['processes']))+'.log')).open('w')
    proc = subprocess.Popen([sys.executable, str(ROOT/'challenges/ticket-desk/app.py'),
                             '--database', str(DB), '--port', '0'], stdout=subprocess.PIPE,
                            stderr=log, text=True)
    endpoint = json.loads(proc.stdout.readline())
    url = 'http://127.0.0.1:' + str(endpoint['listening'][1])
    record['processes'].append(dict(argv=proc.args, pid=proc.pid, listening=endpoint))


def stop():
    if proc is not None and proc.poll() is None:
        proc.terminate(); proc.wait(timeout=10)
    if proc is not None: record['processes'][-1]['exit_code'] = proc.returncode
    if log: log.close()


def request(method, path, data=None, client=None):
    req = Request(url+path, method=method, headers={'Content-Type':'application/json'},
                  data=json.dumps(data).encode() if data is not None else None)
    begin = time.monotonic_ns()
    try:
        with urlopen(req, timeout=10) as response:
            status, body = response.status, json.load(response)
    except HTTPError as response:
        status, body = response.code, json.load(response)
    row = dict(method=method, path=path, input=data, client=client,
               status=status, body=body, begin_ns=begin, end_ns=time.monotonic_ns())
    record['http'].append(row)
    return row


async def browser_race():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/usr/bin/chromium', headless=True,
                                         args=['--no-sandbox'])
        record['browser_version'] = browser.version
        contexts = [await browser.new_context(viewport={'width':1280,'height':900}) for _ in range(2)]
        pages = [await c.new_page() for c in contexts]
        arrived = []
        barrier = asyncio.Event()
        async def gate(route, client):
            req = route.request
            if req.method != 'PATCH':
                await route.continue_(); return
            payload = req.post_data_json
            assert payload == dict(status='in_progress', expected_version=1)
            row = dict(client=client, original_request=payload, arrived_ns=time.monotonic_ns())
            arrived.append(row)
            if len(arrived) == 2: barrier.set()
            await asyncio.wait_for(barrier.wait(), timeout=10)
            row['released_ns'] = time.monotonic_ns()
            # Real response from real backend; only request release time is gated.
            response = await route.fetch()
            row['http_status'] = response.status
            row['actual_response'] = await response.json()
            await route.fulfill(response=response)
        def handler_for(client):
            async def handle(route, _request):
                await gate(route, client)
            return handle
        record['browser'] = arrived
        for i, page in enumerate(pages):
            await page.route('**/api/tickets/2', handler_for(i))
            page.on('pageerror', lambda error: record['errors'].append(str(error)))
            await page.goto(url)
            await expect(page.locator('article[data-id="2"] .state')).to_have_text('待处理')
        await asyncio.gather(*(page.locator('article[data-id="2"] button').click() for page in pages))
        for page in pages:
            await expect(page.locator('article[data-id="2"] .state')).to_have_text('处理中')
        assert sorted(r['http_status'] for r in arrived) == [200,409], arrived
        loser = next(r['client'] for r in arrived if r['http_status'] == 409)
        await expect(pages[loser].locator('#list-error')).to_contain_text('工单已被其他操作更新')
        await pages[loser].set_viewport_size({'width':390,'height':844})
        await pages[loser].screenshot(path=str(OUT/'loser-conflict-390.png'), full_page=True)
        await pages[1-loser].screenshot(path=str(OUT/'winner-1280.png'), full_page=True)
        record['browser'] = arrived
        record['checks'].append('two_browser_clients_one_success_one_visible_conflict')
        for context in contexts: await context.close()
        await browser.close()


try:
    start()
    assert request('POST', '/api/tickets', fixture)['status'] == 201
    before = [request('GET','/api/tickets',client=i)['body']['tickets'][0] for i in range(2)]
    assert before[0] == before[1] and before[0]['version'] == 1
    barrier = threading.Barrier(2)
    def update(client):
        barrier.wait(timeout=10)
        return request('PATCH','/api/tickets/1',dict(status='in_progress',expected_version=1),client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(update, i) for i in range(2)]
        result = [f.result(timeout=15) for f in futures]
    assert sorted(r['status'] for r in result) == [200,409]
    current = request('GET','/api/tickets')['body']['tickets'][0]
    assert all(r['body']['ticket'] == current for r in result)
    history = request('GET','/api/tickets/1/history')['body']['history']
    assert current['version'] == 2 and [h['version'] for h in history] == [1,2]
    record['checks'].append('two_http_clients_one_success_one_conflict_one_history')
    stop(); start()
    assert request('GET','/api/tickets')['body']['tickets'][0] == current
    assert request('GET','/api/tickets/1/history')['body']['history'] == history
    record['checks'].append('restart_preserves_race_result_and_history')
    assert request('POST','/api/tickets',fixture)['body']['ticket']['id'] == 2
    asyncio.run(browser_race())
    final = request('GET','/api/tickets')['body']['tickets']
    assert all(t['version']==2 and t['status']=='in_progress' for t in final)
    assert [h['version'] for h in request('GET','/api/tickets/2/history')['body']['history']] == [1,2]
    assert not record['errors']
    record['passed'] = True
except BaseException as exc:
    record['passed'] = False; record['failure'] = repr(exc)
    raise
finally:
    stop()
    record['database_sha256'] = hashlib.sha256(DB.read_bytes()).hexdigest() if DB.exists() else None
    (OUT/'report.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=record['passed'], checks=record['checks']),ensure_ascii=False))
