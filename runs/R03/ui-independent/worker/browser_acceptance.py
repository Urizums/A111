#!/usr/bin/env python3
"""Real-browser acceptance run for the local ticket desk; writes only beside this script."""
import argparse
import asyncio
import json
import math
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parent


def http_json(base, path, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return {"status": response.status, "body": json.loads(response.read())}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "body": json.loads(exc.read())}


async def wait_ticket_count(page, expected, timeout_seconds=5):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        count = await page.locator(".ticket").count()
        if count == expected:
            return count
        await asyncio.sleep(0.05)
    actual = await page.locator(".ticket").count()
    raise TimeoutError(f"Expected {expected} rendered tickets; found {actual}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--run-label", default="run")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    out = {
        "browser": {}, "runtime": {"python": sys.version, "playwright": None},
        "database": args.database, "base_url": base,
        "controlled_loading_delay_ms": 800,
        "controlled_loading_delay_method": "Playwright intercepted only the initial GET /api/tickets, fetched the actual local server response, held it for 800 ms, then fulfilled with that same response.",
        "actions": [], "checks": [], "screenshots": [], "network_hosts": [],
        "console_errors": [], "page_errors": [], "fatal_error": None,
    }

    def record(name, facts):
        out["actions"].append({"action": name, "facts": facts})

    def check(name, passed, facts):
        out["checks"].append({"check": name, "passed": bool(passed), "facts": facts})

    async with async_playwright() as p:
        out["runtime"]["playwright"] = p.chromium.name
        browser = await p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
        out["browser"] = {"name": "Chromium", "version": browser.version, "executable": "/usr/bin/chromium", "headless": True}
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        page = await context.new_page()
        page.on("console", lambda msg: out["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: out["page_errors"].append(str(exc)))
        page.on("request", lambda req: out["network_hosts"].append(urllib.parse.urlsplit(req.url).netloc))
        delayed = {"used": False}

        async def delay_actual_response(route):
            url = urllib.parse.urlsplit(route.request.url)
            if not delayed["used"] and route.request.method == "GET" and url.path == "/api/tickets":
                delayed["used"] = True
                response = await route.fetch()
                await asyncio.sleep(0.8)
                await route.fulfill(response=response)
            else:
                await route.continue_()

        await page.route(re.compile(r".*/api/tickets(?:\?.*)?$"), delay_actual_response)

        try:
            await page.goto(base, wait_until="domcontentloaded")
            await page.locator("#loading").wait_for(state="visible", timeout=5000)
            loading_shot = ROOT / (args.run_label + "-desktop-loading.png")
            await page.screenshot(path=str(loading_shot), full_page=True)
            out["screenshots"].append({"path": str(loading_shot), "state": "initial loading feedback", "viewport": {"width": 1440, "height": 1000}})
            await page.locator("#loading").wait_for(state="hidden", timeout=10000)
            await page.locator("#empty").wait_for(state="visible")
            initial_counts = {key: await page.locator("#count-" + key).inner_text() for key in ["all", "open", "in_progress", "resolved"]}
            check("loading feedback", delayed["used"], {"observed": True, "controlled_delay_ms": 800, "response_source": "actual backend"})
            check("initial empty feedback", await page.locator("#empty").is_visible(), {"counts": initial_counts, "empty_text": await page.locator("#empty").inner_text()})
            empty_shot = ROOT / (args.run_label + "-desktop-empty.png")
            await page.screenshot(path=str(empty_shot), full_page=True)
            out["screenshots"].append({"path": str(empty_shot), "state": "initial empty queue", "viewport": {"width": 1440, "height": 1000}})

            title = page.get_by_label("问题标题")
            description = page.get_by_label("问题说明")
            priority = page.get_by_label("优先级")
            semantic_controls = {
                "title_label": await title.count() == 1,
                "description_label": await description.count() == 1,
                "priority_label": await priority.count() == 1,
                "search_label": await page.get_by_label("搜索工单").count() == 1,
            }
            check("semantic form labels", all(semantic_controls.values()), semantic_controls)

            await title.fill("保留输入验证草稿")
            await priority.select_option("urgent")
            await page.locator("#create button[type=submit]").click()
            await page.locator("#form-error").wait_for(state="visible")
            validation_facts = {
                "message": await page.locator("#form-error").inner_text(),
                "title_retained": await title.input_value(),
                "description_retained": await description.input_value(),
                "priority_retained": await priority.input_value(),
                "invalid_field": await page.evaluate("document.activeElement.id"),
                "invalid_attribute": await description.get_attribute("aria-invalid"),
            }
            check("validation feedback and draft retention", validation_facts["title_retained"] == "保留输入验证草稿" and validation_facts["priority_retained"] == "urgent" and validation_facts["invalid_field"] == "description" and validation_facts["invalid_attribute"] == "true" and "请填写问题说明" in validation_facts["message"], validation_facts)
            record("submit incomplete draft", validation_facts)

            fixture1 = {"title": "打印队列卡住", "description": "二楼共享打印机无法继续", "priority": "normal"}
            await title.fill(fixture1["title"])
            await description.fill(fixture1["description"])
            await priority.select_option(fixture1["priority"])
            await page.locator("#create button[type=submit]").click()
            await page.locator(".ticket").first.wait_for()
            await page.get_by_text(fixture1["title"], exact=True).wait_for()
            id1 = await page.locator(".ticket").first.get_attribute("data-id")
            record("create fixture 1", {**fixture1, "ticket_id": id1, "status": "open", "backend": "real HTTP + SQLite"})

            fixture2 = {"title": "会议室视频无声", "description": "音频输出设备丢失", "priority": "urgent"}
            await title.fill(fixture2["title"])
            await description.fill(fixture2["description"])
            await priority.select_option(fixture2["priority"])
            await page.locator("#create button[type=submit]").click()
            await page.locator(".ticket").first.wait_for()
            await page.get_by_text(fixture2["title"], exact=True).wait_for()
            await wait_ticket_count(page, 2)
            id2 = await page.locator(".ticket").first.get_attribute("data-id")
            counts_after_create = {key: await page.locator("#count-" + key).inner_text() for key in ["all", "open", "in_progress", "resolved"]}
            check("create both supplied fixtures", await page.locator(".ticket").count() == 2 and counts_after_create == {"all": "2", "open": "2", "in_progress": "0", "resolved": "0"}, {"first": {**fixture1, "id": id1}, "second": {**fixture2, "id": id2}, "counts": counts_after_create})
            record("create fixture 2", {**fixture2, "ticket_id": id2, "status": "open", "backend": "real HTTP + SQLite"})
            desktop_shot = ROOT / (args.run_label + "-desktop-two-tickets.png")
            await page.screenshot(path=str(desktop_shot), full_page=True)
            out["screenshots"].append({"path": str(desktop_shot), "state": "two created tickets", "viewport": {"width": 1440, "height": 1000}})

            await page.locator('button[data-status="open"]').click()
            await wait_ticket_count(page, 2)
            status_filtered = await page.locator(".ticket").count()
            await page.locator("#search").fill("打印队列卡住")
            await page.locator("#search-form button[type=submit]").click()
            await page.get_by_text(fixture1["title"], exact=True).wait_for()
            await wait_ticket_count(page, 1)
            search_count = await page.locator(".ticket").count()
            search_results = [await item.locator("h3").inner_text() for item in await page.locator(".ticket").all()]
            check("status filter and persisted-ticket search", status_filtered == 2 and search_count == 1 and search_results == [fixture1["title"]], {"open_filter_count": status_filtered, "search_term": "打印队列卡住", "results": search_results})
            record("filter open and search fixture 1", {"open_filter_count": status_filtered, "search_term": "打印队列卡住", "results": search_results})
            await page.locator("#search").fill("")
            await page.locator("#search-form button[type=submit]").click()
            await page.locator(".ticket").first.wait_for()
            await wait_ticket_count(page, 2)

            card1 = page.locator('.ticket[data-id="' + id1 + '"]')
            flow = []
            for button_name, expected in [
                ("开始处理：" + fixture1["title"], "处理中"),
                ("标记解决：" + fixture1["title"], "已解决"),
                ("重新打开：" + fixture1["title"], "待处理"),
            ]:
                await card1.get_by_role("button", name=button_name).click()
                await card1.locator(".state").get_by_text(expected, exact=True).wait_for()
                flow.append({"button": button_name, "resulting_status": expected})
            await card1.locator("summary").click()
            await card1.locator("ol li").first.wait_for()
            history = await card1.locator("ol li").all_inner_texts()
            history_ok = len(history) == 4 and "创建 → 待处理" in history[0] and "待处理 → 处理中" in history[1] and "处理中 → 已解决" in history[2] and "已解决 → 待处理" in history[3]
            check("open, progress, resolve, reopen, and retained history", history_ok, {"ticket_id": id1, "status_actions": flow, "history": history})
            record("status progression, reopen, and history", {"ticket_id": id1, "actions": flow, "history": history})

            api_before = http_json(base, "/api/tickets")
            current2 = next(ticket for ticket in api_before["body"]["tickets"] if str(ticket["id"]) == id2)
            stale_response = http_json(base, "/api/tickets/" + id2, "PATCH", {"status": "in_progress", "expected_version": current2["version"]})
            record("second HTTP client concurrent update", {"client": "Python urllib.request", "ticket_id": id2, "based_on_version": current2["version"], "request": {"status": "in_progress", "expected_version": current2["version"]}, "response": stale_response})
            stale_button = page.locator('.ticket[data-id="' + id2 + '"]').get_by_role("button", name="开始处理：" + fixture2["title"])
            await stale_button.click()
            await page.locator("#list-error").wait_for(state="visible")
            conflict_text = await page.locator("#list-error").inner_text()
            card2 = page.locator('.ticket[data-id="' + id2 + '"]')
            await card2.locator(".state").get_by_text("处理中", exact=True).wait_for()
            version2 = await card2.locator(".meta").inner_text()
            conflict_ok = stale_response["status"] == 200 and "其他操作更新" in conflict_text and "版本 2" in version2 and await card2.locator(".state").inner_text() == "处理中"
            check("stale browser version returns conflict without overwrite", conflict_ok, {"competing_client_status": stale_response["status"], "browser_error": conflict_text, "rendered_version": version2, "rendered_status": await card2.locator(".state").inner_text()})

            invalid = http_json(base, "/api/tickets/" + id2, "PATCH", {"status": "open", "expected_version": 2})
            after_invalid = http_json(base, "/api/tickets")
            unchanged2 = next(ticket for ticket in after_invalid["body"]["tickets"] if str(ticket["id"]) == id2)
            invalid_ok = invalid["status"] == 400 and unchanged2["status"] == "in_progress" and unchanged2["version"] == 2
            check("invalid transition rejected without state change", invalid_ok, {"request": {"status": "open", "expected_version": 2}, "response": invalid, "state_after": {"status": unchanged2["status"], "version": unchanged2["version"]}})
            record("invalid transition through second HTTP client", {"ticket_id": id2, "response": invalid, "state_after": {"status": unchanged2["status"], "version": unchanged2["version"]}})

            await page.locator('button[data-status="in_progress"]').click()
            await wait_ticket_count(page, 1)
            progress_results = [await item.locator("h3").inner_text() for item in await page.locator(".ticket").all()]
            progress_counts = {key: await page.locator("#count-" + key).inner_text() for key in ["all", "open", "in_progress", "resolved"]}
            check("in-progress status filter and queue counts", progress_results == [fixture2["title"]] and progress_counts == {"all": "2", "open": "1", "in_progress": "1", "resolved": "0"}, {"results": progress_results, "counts": progress_counts})
            await page.locator('button[data-status=""]').click()
            await page.locator("#search").fill("no-matching-ticket-73621")
            await page.locator("#search-form button[type=submit]").click()
            await page.locator("#empty").wait_for(state="visible")
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.wait_for_timeout(100)
            empty_mobile_shot = ROOT / (args.run_label + "-mobile-empty.png")
            await page.screenshot(path=str(empty_mobile_shot), full_page=True)
            out["screenshots"].append({"path": str(empty_mobile_shot), "state": "mobile empty search result", "viewport": {"width": 390, "height": 844}})
            await page.locator("#search").fill("")
            await page.locator("#search-form button[type=submit]").click()
            await page.locator(".ticket").first.wait_for()
            await wait_ticket_count(page, 2)
            await page.wait_for_timeout(100)
            mobile_dimensions = await page.evaluate("({innerWidth, documentWidth:document.documentElement.scrollWidth, bodyWidth:document.body.scrollWidth})")
            mobile_shot = ROOT / (args.run_label + "-mobile-two-tickets.png")
            await page.screenshot(path=str(mobile_shot), full_page=True)
            out["screenshots"].append({"path": str(mobile_shot), "state": "mobile readable ticket cards", "viewport": {"width": 390, "height": 844}})
            check("390px layout has no horizontal overflow", mobile_dimensions["innerWidth"] == 390 and mobile_dimensions["documentWidth"] <= 390 and mobile_dimensions["bodyWidth"] <= 390, mobile_dimensions)

            await page.set_viewport_size({"width": 1440, "height": 1000})
            await page.reload(wait_until="domcontentloaded")
            await page.locator("#loading").wait_for(state="hidden", timeout=10000)
            await page.keyboard.press("Tab")
            focus_facts = await page.evaluate("""() => { const e=document.activeElement, s=getComputedStyle(e), r=e.getBoundingClientRect(); return {tag:e.tagName,text:e.innerText||e.textContent, href:e.getAttribute('href'),outlineStyle:s.outlineStyle,outlineWidth:s.outlineWidth,outlineColor:s.outlineColor,rect:{x:r.x,y:r.y,width:r.width,height:r.height}}; }""")
            focus_ok = focus_facts["href"] == "#queue" and focus_facts["outlineStyle"] != "none" and float(focus_facts["outlineWidth"].replace("px", "")) >= 2 and focus_facts["rect"]["x"] >= 0
            check("keyboard focus is visible on first Tab", focus_ok, focus_facts)
            focus_shot = ROOT / (args.run_label + "-keyboard-focus.png")
            await page.screenshot(path=str(focus_shot), full_page=False)
            out["screenshots"].append({"path": str(focus_shot), "state": "first Tab reveals skip link and focus outline", "viewport": {"width": 1440, "height": 1000}})

            contrast = await page.evaluate("""() => {
              const parse = c => { const m=c.match(/[\\d.]+/g).map(Number); return m.length===4 ? [m[0],m[1],m[2],m[3]] : [m[0],m[1],m[2],1]; };
              const bg = e => { for(let n=e;n;n=n.parentElement){ const c=getComputedStyle(n).backgroundColor, v=parse(c); if(v[3]>.99) return c; } return 'rgb(255,255,255)'; };
              const lum = c => { const a=parse(c).slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4); return .2126*a[0]+.7152*a[1]+.0722*a[2]; };
              const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
              const el=(selector,label)=>{const e=document.querySelector(selector); const fg=getComputedStyle(e).color, back=bg(e); return {label,foreground:fg,background:back,ratio:Number(ratio(fg,back).toFixed(2))};};
              const placeholder=getComputedStyle(document.querySelector('#search'),'::placeholder').color;
              const placeholderBg=getComputedStyle(document.querySelector('#search')).backgroundColor;
              return [el('body','body text'),el('header p','header supporting text'),el('.primary','primary button'),el('.badge.urgent','urgent priority badge'),{label:'search placeholder',foreground:placeholder,background:placeholderBg,ratio:Number(ratio(placeholder,placeholderBg).toFixed(2))}];
            }""")
            # The urgent badge is present on fixture 2; the search field also has placeholder text.
            contrast_pass = all(item["ratio"] >= 4.5 for item in contrast)
            check("key text contrast sampled against rendered backgrounds", contrast_pass, {"samples": contrast, "threshold": 4.5, "scope": "selected normal-size text only; not a full contrast audit"})

            await page.emulate_media(reduced_motion="reduce")
            motion = await page.evaluate("""() => ({matches:matchMedia('(prefers-reduced-motion: reduce)').matches, scrollBehavior:getComputedStyle(document.documentElement).scrollBehavior, animationDuration:getComputedStyle(document.querySelector('button')).animationDuration, transitionDuration:getComputedStyle(document.querySelector('button')).transitionDuration})""")
            motion_ok = motion["matches"] and motion["scrollBehavior"] == "auto" and all(part.strip() in {"0s", "0ms"} for part in motion["animationDuration"].split(",")) and all(part.strip() in {"0s", "0ms"} for part in motion["transitionDuration"].split(","))
            check("reduced-motion preference is honored", motion_ok, motion)
            check("all browser requests stayed on local loopback", all(host.startswith("127.0.0.1:") for host in out["network_hosts"]), sorted(set(out["network_hosts"])))
            record("browser runtime console and network review", {"console_errors": out["console_errors"], "page_errors": out["page_errors"], "network_hosts": sorted(set(out["network_hosts"]))})
        except Exception as exc:
            out["fatal_error"] = {"type": type(exc).__name__, "message": str(exc)}
        finally:
            await context.close()
            await browser.close()

    out["summary"] = {
        "checks_passed": sum(1 for item in out["checks"] if item["passed"]),
        "checks_total": len(out["checks"]),
        "all_checks_passed": bool(out["checks"]) and all(item["passed"] for item in out["checks"]) and out["fatal_error"] is None,
        "fatal_error": out["fatal_error"],
    }
    output = ROOT / ("browser-evidence-" + args.run_label + ".json")
    output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["fatal_error"] is None else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
