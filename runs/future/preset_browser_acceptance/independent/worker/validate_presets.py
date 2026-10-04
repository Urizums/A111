#!/usr/bin/env python3
"""Browser acceptance run for the assigned local ui-presets demo."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path("/workspace/A111/runs/future/preset_browser_acceptance/independent/worker")
TARGET = Path("/workspace/A111/skills/design-product-experience/assets")
URL = "http://127.0.0.1:8765/ui-presets.html"
CHROMIUM = "/usr/bin/chromium"
ARTIFACTS = ROOT / "screenshots"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

outcomes: list[dict] = []
actions: list[str] = []
raw_errors: list[dict] = []
browser_metadata: dict = {}
original_rows: list[dict] = []
measurements: dict = {}
started_at = datetime.now(timezone.utc).isoformat()


def record(name: str, fn) -> None:
    try:
        details = fn()
        outcomes.append({"check": name, "status": "passed", "details": details})
    except Exception as exc:  # Keep running so later independent checks still execute.
        outcomes.append({"check": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


def step(text: str) -> None:
    actions.append(text)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rows(page) -> list[dict]:
    return page.locator("#run-list > tr").evaluate_all(
        "els => els.map(e => ({id:e.dataset.runId,status:e.dataset.status,workflow:e.dataset.workflow,name:e.querySelector('.run-name')?.textContent.trim()}))"
    )


def visible_rows(page) -> list[dict]:
    return page.locator("#run-list > tr:not([hidden])").evaluate_all(
        "els => els.map(e => ({id:e.dataset.runId,status:e.dataset.status,workflow:e.dataset.workflow,name:e.querySelector('.run-name')?.textContent.trim()}))"
    )


def screenshot(page, filename: str, full_page: bool = True) -> str:
    path = ARTIFACTS / filename
    page.screenshot(path=str(path), full_page=full_page, animations="disabled")
    return str(path)


def rgb(value: str) -> tuple[float, float, float, float]:
    nums = [float(x) for x in re.findall(r"[\d.]+", value)]
    if value.startswith("rgba") and len(nums) >= 4:
        return nums[0], nums[1], nums[2], nums[3]
    if len(nums) >= 3:
        return nums[0], nums[1], nums[2], 1.0
    raise ValueError(f"Unsupported computed color: {value}")


def composite(fg: tuple[float, float, float, float], bg: tuple[float, float, float, float]):
    alpha = fg[3] + bg[3] * (1 - fg[3])
    if alpha == 0:
        return (0.0, 0.0, 0.0, 0.0)
    channels = tuple((fg[i] * fg[3] + bg[i] * bg[3] * (1 - fg[3])) / alpha for i in range(3))
    return (*channels, alpha)


def luminance(c: tuple[float, float, float, float]) -> float:
    vals = []
    for channel in c[:3]:
        x = channel / 255
        vals.append(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def contrast(foreground: tuple[float, float, float, float], background: tuple[float, float, float, float]) -> float:
    fg = composite(foreground, background)
    l1, l2 = sorted((luminance(fg), luminance(background)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def capture_contrast(page) -> list[dict]:
    return page.evaluate("""() => {
      const selectors = [
        ['page-title', '#page-title'], ['section-title', '#runs-heading'],
        ['muted-count', '#run-count'], ['run-name', '.run-name'], ['run-meta', '.run-meta'],
        ['success-status', '.status-success'], ['failed-status', '.status-failed'],
        ['queued-status', '.status-queued'], ['primary-action', '#create-run'],
        ['filter-label', 'label[for="run-search"]'], ['table-header', 'thead th:first-child'],
        ['demo-note', '.demo-note'], ['nav-current', '.primary-nav a[aria-current]']
      ];
      return selectors.map(([name, selector]) => {
        const el = document.querySelector(selector);
        if (!el) return {name, missing:true};
        const style = getComputedStyle(el);
        let bg = [0,0,0,0];
        for (let node=el; node; node=node.parentElement) {
          const s=getComputedStyle(node), m=s.backgroundColor.match(/[0-9.]+/g);
          if (m) {
            const a=m.length >= 4 ? Number(m[3]) : 1;
            const color=[Number(m[0]),Number(m[1]),Number(m[2]),a];
            const ba=color[3]+bg[3]*(1-color[3]);
            if (ba) bg=[0,1,2].map(i=>(color[i]*color[3]+bg[i]*bg[3]*(1-color[3]))/ba).concat([ba]);
            if (ba >= .999) break;
          }
        }
        const f=style.color.match(/[0-9.]+/g);
        return {name,text:(el.innerText||el.textContent||'').trim(),foreground:style.color,background:`rgba(${bg.join(',')})`,fontSize:style.fontSize,fontWeight:style.fontWeight,foregroundChannels:f?.slice(0,3).map(Number),backgroundChannels:bg.slice(0,3),ratio:null};
      });
    }""")


def contrast_ratio_from_measurement(item: dict) -> float | None:
    if item.get("missing") or not item.get("foregroundChannels") or not item.get("backgroundChannels"):
        return None
    fg = (*item["foregroundChannels"], 1.0)
    bg = (*item["backgroundChannels"], 1.0)
    return round(contrast(fg, bg), 2)


def accessible_controls(page) -> list[dict]:
    return page.evaluate("""() => {
      const nodes=[...document.querySelectorAll('a[href],button,input,select,textarea,[role="button"],[tabindex]:not([tabindex="-1"])')];
      const isVisible=el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return !el.disabled&&!el.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;};
      return nodes.filter(isVisible).map(el=>{
        const id=el.id;
        const labelled=el.getAttribute('aria-labelledby');
        const labelById=labelled ? labelled.split(/\\s+/).map(x=>document.getElementById(x)?.innerText||'').join(' ').trim() : '';
        const label=el.labels ? [...el.labels].map(x=>x.innerText).join(' ').trim() : '';
        const name=el.getAttribute('aria-label')||labelById||label||el.innerText?.trim()||el.value||el.getAttribute('title')||'';
        return {tag:el.tagName.toLowerCase(),id,name:name.trim(),tabIndex:el.tabIndex,disabled:!!el.disabled};
      });
    }""")


def main() -> None:
    global original_rows, browser_metadata, measurements
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM, headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="no-preference")
        page = context.new_page()
        page.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        page.on("console", lambda msg: raw_errors.append({"source": "console", "type": msg.type, "text": msg.text}) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: raw_errors.append({"source": "pageerror", "text": str(exc)}))
        page.on("requestfailed", lambda req: raw_errors.append({"source": "requestfailed", "url": req.url, "failure": req.failure}))
        page.on("response", lambda res: raw_errors.append({"source": "http", "status": res.status, "url": res.url}) if res.status >= 400 else None)
        response = page.goto(URL, wait_until="networkidle")
        step(f"GET {URL}; HTTP {response.status if response else 'no response'}; wait_until=networkidle")
        browser_metadata = {
            "browser": "Chromium via /usr/bin/chromium",
            "browser_version": browser.version,
            "viewport_initial": {"width": 1440, "height": 1000},
            "url": URL,
            "http_status": response.status if response else None,
            "user_agent": page.evaluate("navigator.userAgent"),
            "color_scheme": page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'")
        }
        original_rows = rows(page)
        step("Recorded original DOM rows, ids, statuses, workflows, and names before interaction.")
        screenshot(page, "desktop-initial.png")

        def baseline():
            expect(len(original_rows) == 3, f"Expected exactly 3 original rows, got {original_rows}")
            expect([r["id"] for r in original_rows] == ["r-1842", "r-1841", "r-1840"], f"Unexpected original IDs: {original_rows}")
            expect([r["status"] for r in original_rows] == ["succeeded", "failed", "succeeded"], f"Unexpected original statuses: {original_rows}")
            return {"original_rows": original_rows}
        record("original three rows and local sample identity", baseline)

        def filters():
            page.locator("#run-search").fill("r-1841")
            expect([r["id"] for r in visible_rows(page)] == ["r-1841"], "Text filter did not isolate run r-1841")
            page.locator("#status-filter").select_option("failed")
            expect([r["id"] for r in visible_rows(page)] == ["r-1841"], "Status filter did not retain only failed matching row")
            page.locator("#run-search").fill("no-such-run")
            expect(page.locator("#empty-state").is_visible(), "No-match state was not shown")
            expect("No runs match" in page.locator("#empty-title").inner_text(), "No-match feedback text was absent")
            page.locator("#clear-empty-filters").click()
            page.wait_for_function("document.querySelectorAll('#run-list > tr:not([hidden])').length === 3 && document.querySelector('#empty-state').hidden", timeout=1000)
            expect(len(visible_rows(page)) == 3, "Empty-state clear did not restore all rows")
            expect(page.locator("#empty-state").is_hidden(), "Empty state remained after clearing filters")
            page.locator("#run-search").fill("release")
            expect({r["id"] for r in visible_rows(page)} == {"r-1842", "r-1841"}, "Text workflow filter mismatch")
            page.locator("#clear-filters").click()
            page.wait_for_function("document.querySelector('#run-search').value === '' && document.querySelector('#status-filter').value === 'all' && document.querySelectorAll('#run-list > tr:not([hidden])').length === 3", timeout=1000)
            expect(len(visible_rows(page)) == 3, "Clear filters control did not restore all rows")
            step("Text and status filters, empty-state clear, and form clear exercised with pointer and input events.")
            return {"filtered_release_ids": ["r-1842", "r-1841"], "restored_rows": [r["id"] for r in visible_rows(page)]}
        record("text/status filtering, empty feedback, and clear", filters)

        def drawer_escape():
            opener = page.locator('[data-view-run="r-1842"]')
            opener.click()
            expect(page.locator("#run-drawer").is_visible(), "Drawer did not open")
            screenshot(page, "desktop-detail.png")
            page.keyboard.press("Escape")
            expect(page.locator("#run-drawer").is_hidden(), "Escape did not close drawer")
            escaped_focus = page.evaluate("({id:document.activeElement.id,view:document.activeElement.getAttribute('data-view-run')})")
            expect(escaped_focus.get("view") == "r-1842", f"Escape did not return focus to opener: {escaped_focus}")
            opener.click()
            page.locator("#close-drawer").click()
            expect(page.locator("#run-drawer").is_hidden(), "Named close did not close drawer")
            close_focus = page.evaluate("({id:document.activeElement.id,view:document.activeElement.getAttribute('data-view-run')})")
            expect(close_focus.get("view") == "r-1842", f"Named close did not return focus to opener: {close_focus}")
            step("Opened run detail, closed with Escape and named Close; checked focus return for both.")
            return {"escape_focus_return": escaped_focus, "close_focus_return": close_focus}
        record("detail open, Escape/Close, and focus return", drawer_escape)

        def run_again():
            page.locator('[data-view-run="r-1840"]').click()
            page.locator("#run-again").click()
            added = page.locator('#run-list > tr[data-run-id="r-1843"]')
            expect(added.count() == 1, "Run again did not add exactly one new row")
            expect(added.get_attribute("data-workflow") == "Dependency audit", "Run again used the wrong workflow")
            expect(added.get_attribute("data-status") == "queued", "New run was not queued")
            expect(added.locator(".run-name").inner_text() == "dependency-audit", "New run name did not match selected workflow")
            step("Opened r-1840 (Dependency audit) and activated Run again; verified r-1843 local queued row.")
            return {"rows_after_run_again": rows(page), "added_id": "r-1843"}
        record("run again adds selected matching workflow", run_again)

        def deletion():
            before = {r["id"] for r in rows(page)}
            page.locator('[data-view-run="r-1841"]').click()
            page.locator("#request-delete").click()
            expect(page.locator("#delete-dialog").is_visible(), "Delete confirmation did not open")
            page.locator("#cancel-delete").click()
            expect(page.locator("#delete-dialog").is_hidden(), "Cancel did not close confirmation")
            expect({r["id"] for r in rows(page)} == before, "Cancel changed the run list")
            page.locator("#request-delete").click()
            page.locator("#confirm-delete").click()
            after = {r["id"] for r in rows(page)}
            expect(after == before - {"r-1841"}, f"Confirmed delete changed wrong rows: before={before}, after={after}")
            expect(page.locator("#run-drawer").is_hidden(), "Drawer stayed open after confirmed delete")
            step("Canceled deletion of r-1841 and verified retention; confirmed deletion and verified only r-1841 removed.")
            return {"before": sorted(before), "after_cancel": sorted(before), "after_confirm": sorted(after)}
        record("delete cancel retains; confirmation removes only selected row", deletion)

        def refresh_states():
            page.locator("#refresh-runs").click()
            expect(page.locator("#run-list").get_attribute("aria-busy") == "true", "Refresh did not expose aria-busy")
            expect("Current results stay available" in page.locator("#load-status").inner_text(), "Refresh omitted current-results status")
            expect(len(rows(page)) == 3, "Current rows were not retained during refresh")
            page.locator("#cancel-refresh").click()
            expect(page.locator("#run-list").get_attribute("aria-busy") is None, "Cancel left list busy")
            expect(page.locator("#retry-refresh").is_visible(), "Cancel did not expose retry")
            expect("Refresh canceled" in page.locator("#load-status").inner_text(), "Cancel feedback missing")
            page.locator("#retry-refresh").click()
            page.wait_for_function("!document.querySelector('#run-list').hasAttribute('aria-busy') && document.querySelector('#load-status').textContent.includes('up to date')", timeout=5000)
            expect(len(rows(page)) == 3, "Retry changed local rows")
            page.locator("#preview-error").click()
            page.wait_for_function("!document.querySelector('#load-error').hidden", timeout=5000)
            expect("current list is still available" in page.locator("#load-error").inner_text(), "Recoverable error did not preserve list message")
            expect(len(rows(page)) == 3, "Recoverable error changed current rows")
            page.locator("#retry-error").click()
            page.wait_for_function("document.querySelector('#load-error').hidden && document.querySelector('#load-status').textContent.includes('up to date')", timeout=5000)
            expect(page.locator("#run-list").get_attribute("aria-busy") is None, "Successful retry left list busy")
            step("Observed refresh busy/current rows, canceled and retried; induced recoverable error and retried to success.")
            return {"rows_after_recovery": [r["id"] for r in rows(page)], "updated_text": page.locator("#last-updated").inner_text()}
        record("refresh busy/current rows, cancel/retry, error/retry", refresh_states)

        def independent_settings():
            page.locator("#palette-choice").select_option("night")
            expect(page.locator("html").get_attribute("data-palette") == "night", "Night palette was not applied")
            page.locator("#density-choice").select_option("condensed")
            expect(page.locator("html").get_attribute("data-density") == "condensed", "Condensed density was not applied")
            expect(page.locator("html").get_attribute("data-palette") == "night", "Density change reset palette")
            page.locator("#palette-choice").select_option("clear")
            expect(page.locator("html").get_attribute("data-density") == "condensed", "Palette change reset density")
            page.locator("#density-choice").select_option("balanced")
            step("Changed palette and density in each direction and checked each retained the other setting.")
            return {"palette": "clear", "density": "balanced"}
        record("palette and density independence", independent_settings)

        def motion_and_reduced():
            page.locator("#motion-choice").select_option("quiet-slide")
            page.locator('[data-view-run="r-1842"]').click()
            motion_info = page.locator("#run-drawer").evaluate("e => ({animationName:getComputedStyle(e).animationName,animationDuration:getComputedStyle(e).animationDuration,transform:getComputedStyle(e).transform})")
            expect(page.locator("#run-drawer").is_visible(), "Motion drawer did not open")
            expect(motion_info["animationName"] == "drawer-quiet-slide", f"Selected motion was not applied: {motion_info}")
            page.locator("#close-drawer").click()
            page.locator("#motion-choice").select_option("light-elastic")
            page.locator('[data-view-run="r-1842"]').click()
            elastic_info = page.locator("#run-drawer").evaluate("e => ({animationName:getComputedStyle(e).animationName,animationDuration:getComputedStyle(e).animationDuration})")
            expect(elastic_info["animationName"] == "drawer-light-elastic", f"Elastic motion was not applied: {elastic_info}")
            page.locator("#close-drawer").click()
            page.emulate_media(reduced_motion="reduce")
            page.locator('[data-view-run="r-1842"]').click()
            reduced_info = page.locator("#run-drawer").evaluate("e => ({animationName:getComputedStyle(e).animationName,animationDuration:getComputedStyle(e).animationDuration,transform:getComputedStyle(e).transform})")
            expect(page.locator("#run-drawer").is_visible(), "Reduced-motion drawer did not open")
            expect(reduced_info["animationName"] == "none", f"Reduced motion did not disable drawer animation: {reduced_info}")
            expect(page.locator("#close-drawer").is_visible() and page.locator("#run-again").is_visible(), "Drawer controls unusable with reduced motion")
            page.locator("#close-drawer").click()
            page.emulate_media(reduced_motion="no-preference")
            page.locator("#motion-choice").select_option("none")
            step("Verified quiet-slide runs without reduced motion; light-elastic resolves to no animation under reduced motion and remains operable.")
            return {"quiet_slide": motion_info, "light_elastic": elastic_info, "reduced_motion": reduced_info}
        record("drawer motion toggle and reduced-motion usability", motion_and_reduced)

        # Begin keyboard-order measurements in a freshly loaded document so earlier pointer
        # activity cannot leave the browser's sequential focus cursor near the end of the page.
        page = context.new_page()
        page.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        page.on("console", lambda msg: raw_errors.append({"source": "console", "type": msg.type, "text": msg.text}) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: raw_errors.append({"source": "pageerror", "text": str(exc)}))
        page.on("requestfailed", lambda req: raw_errors.append({"source": "requestfailed", "url": req.url, "failure": req.failure}))
        page.on("response", lambda res: raw_errors.append({"source": "http", "status": res.status, "url": res.url}) if res.status >= 400 else None)
        response = page.goto(URL, wait_until="networkidle")
        step(f"Fresh browser page for accessibility/visual review: GET {URL}; HTTP {response.status if response else 'no response'}.")

        def desktop_accessibility_and_contrast():
            labels = accessible_controls(page)
            unnamed = [c for c in labels if not c["name"]]
            expect(not unnamed, f"Visible interactive controls without an accessible-name source: {unnamed}")
            focusables = page.evaluate("""() => [...document.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled)')].filter(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return !e.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0}).map(e=>({id:e.id,name:e.getAttribute('aria-label')||e.innerText?.trim()||e.labels?.[0]?.innerText?.trim()||e.value||'',tag:e.tagName.toLowerCase()}))""")
            page.evaluate("document.activeElement.blur()")
            seen = []
            for _ in range(len(focusables) + 1):
                page.keyboard.press("Tab")
                active = page.evaluate("({id:document.activeElement.id,view:document.activeElement.getAttribute('data-view-run'),tag:document.activeElement.tagName.toLowerCase(),name:document.activeElement.getAttribute('aria-label')||document.activeElement.innerText?.trim()||document.activeElement.labels?.[0]?.innerText?.trim()||document.activeElement.value||'',outline:getComputedStyle(document.activeElement).outlineStyle,outlineWidth:getComputedStyle(document.activeElement).outlineWidth,outlineColor:getComputedStyle(document.activeElement).outlineColor,isBody:document.activeElement===document.body})")
                if active["isBody"]:
                    break
                seen.append({"id": active["id"], "tag": active["tag"], "name": active["name"], "outlineStyle": active["outline"], "outlineWidth": active["outlineWidth"], "outlineColor": active["outlineColor"]})
                if len(seen) == 1:
                    screenshot(page, "desktop-keyboard-focus.png", full_page=False)
            expect(len(seen) == len(focusables), f"Keyboard traversal did not visit all controls before page focus ended: expected {len(focusables)}, got {len(seen)}")
            no_outline = [item for item in seen if item["outlineStyle"] in ("none", "hidden") or item["outlineWidth"] in ("0px", "0px 0px")]
            expect(not no_outline, f"Keyboard focus lacked a visible outline on some controls: {no_outline}")
            page.evaluate("document.activeElement.blur()")
            keyboard_opened = False
            for _ in range(len(focusables)):
                page.keyboard.press("Tab")
                if page.evaluate("document.activeElement.getAttribute('data-view-run')") == "r-1842":
                    page.keyboard.press("Enter")
                    keyboard_opened = page.locator("#run-drawer").is_visible()
                    break
            expect(keyboard_opened, "Keyboard Enter could not open run r-1842 details")
            page.keyboard.press("Escape")
            expect(page.locator("#run-drawer").is_hidden(), "Keyboard-opened detail did not close with Escape")
            keyboard_return = page.evaluate("document.activeElement.getAttribute('data-view-run')")
            expect(keyboard_return == "r-1842", f"Keyboard detail did not return focus to opener: {keyboard_return}")
            measurements["desktop_visible_controls"] = labels
            measurements["desktop_focusables"] = focusables
            measurements["desktop_tab_sequence"] = seen
            clear_contrast = capture_contrast(page)
            for item in clear_contrast:
                item["ratio"] = contrast_ratio_from_measurement(item)
            measurements["contrast_clear"] = clear_contrast
            for item in clear_contrast:
                if item.get("ratio") is not None:
                    threshold = 3.0 if float(item["fontSize"].replace("px", "")) >= 24 or (float(item["fontSize"].replace("px", "")) >= 18.66 and int(item["fontWeight"]) >= 700) else 4.5
                    expect(item["ratio"] >= threshold, f"Contrast below WCAG text check for {item['name']}: {item['ratio']}:1 < {threshold}:1")
            page.locator("#palette-choice").select_option("night")
            dark = capture_contrast(page)
            for item in dark:
                item["ratio"] = contrast_ratio_from_measurement(item)
            measurements["contrast_night"] = dark
            for item in dark:
                if item.get("ratio") is not None:
                    threshold = 3.0 if float(item["fontSize"].replace("px", "")) >= 24 or (float(item["fontSize"].replace("px", "")) >= 18.66 and int(item["fontWeight"]) >= 700) else 4.5
                    expect(item["ratio"] >= threshold, f"Night-palette contrast below WCAG text check for {item['name']}: {item['ratio']}:1 < {threshold}:1")
            screenshot(page, "desktop-night-palette.png")
            page.locator("#palette-choice").select_option("clear")
            step("Enumerated visible controls and names, tabbed through desktop focus order, inspected :focus-visible outline, and measured key text contrast in both palettes.")
            return {"visible_controls": len(labels), "focusables": len(focusables), "tab_stops_recorded": len(seen), "first_focus": seen[0], "keyboard_detail_focus_return": keyboard_return, "contrast_clear": clear_contrast, "contrast_night": dark}
        record("desktop controls, keyboard focus visibility, and key text contrast", desktop_accessibility_and_contrast)

        def narrow_viewport():
            page.set_viewport_size({"width": 390, "height": 844})
            page.evaluate("window.scrollTo(0,0)")
            page.locator("#density-choice").select_option("balanced")
            page.locator("#palette-choice").select_option("clear")
            screenshot(page, "mobile-390-initial.png")
            dimensions = page.evaluate("""() => {
              const wrap=document.querySelector('.table-wrap'), button=document.querySelector('[data-view-run="r-1842"]');
              return {viewport:innerWidth,documentScrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body.scrollWidth,tableClientWidth:wrap.clientWidth,tableScrollWidth:wrap.scrollWidth,tableScrollLeft:wrap.scrollLeft,tableOverflow:getComputedStyle(wrap).overflowX,viewButtonRect:(()=>{const r=button.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})(),wrapRect:(()=>{const r=wrap.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})()};
            }""")
            expect(dimensions["documentScrollWidth"] <= 390, f"Page has horizontal overflow at 390px: {dimensions}")
            if dimensions["tableScrollWidth"] > dimensions["tableClientWidth"]:
                page.locator(".table-wrap").evaluate("e => e.scrollLeft=e.scrollWidth")
                dimensions["tableScrollLeft"] = page.locator(".table-wrap").evaluate("e => e.scrollLeft")
                last = page.locator("#run-list tr:first-child td:last-child button")
                expect(last.is_visible(), "Last-column control inaccessible after horizontal table scroll")
                expect(dimensions["tableScrollLeft"] > 0, "Table reports overflow but could not scroll horizontally")
                last_position = last.evaluate("e => {const r=e.getBoundingClientRect(),w=e.closest('.table-wrap').getBoundingClientRect();return {left:r.left,right:r.right,wrapLeft:w.left,wrapRight:w.right}}")
                expect(last_position["right"] <= last_position["wrapRight"] + 1 and last_position["right"] >= last_position["wrapLeft"], f"Last-column control was not in the visible scrolled table area: {last_position}")
                dimensions["last_control_after_scroll"] = last_position
                page.locator(".table-wrap").evaluate("e => e.scrollLeft=0")
            labels = accessible_controls(page)
            expect(all(c["name"] for c in labels), f"A visible mobile control has no accessible name: {labels}")
            # Keyboard interaction: reach the status select, change it, verify a matching result, and restore.
            page.evaluate("document.activeElement.blur()")
            reached = False
            for _ in range(40):
                page.keyboard.press("Tab")
                if page.evaluate("document.activeElement.id") == "status-filter":
                    reached = True
                    break
            expect(reached, "Status filter was not keyboard reachable at 390px")
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            expect({r["id"] for r in visible_rows(page)} == {"r-1842", "r-1840"}, "Keyboard status selection did not update rows")
            page.locator("#clear-filters").click()
            # Pointer interaction at narrow width: open a row and close its drawer.
            page.locator('[data-view-run="r-1842"]').click()
            expect(page.locator("#run-drawer").is_visible(), "Pointer could not open detail at 390px")
            screenshot(page, "mobile-390-detail.png")
            page.locator("#close-drawer").click()
            expect(page.locator("#run-drawer").is_hidden(), "Close failed at 390px")
            focusables = page.evaluate("""() => [...document.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled)')].filter(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return !e.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0}).map(e=>({id:e.id,name:e.getAttribute('aria-label')||e.innerText?.trim()||e.labels?.[0]?.innerText?.trim()||e.value||''}))""")
            measurements["mobile_dimensions"] = dimensions
            measurements["mobile_visible_controls"] = labels
            measurements["mobile_focusables"] = focusables
            step("Set 390x844 viewport; checked document/table overflow and internal scroll, accessible control names, keyboard status selection, pointer detail open/close.")
            return {"dimensions": dimensions, "visible_controls": len(labels), "keyboard_focusables": len(focusables), "status_filter_keyboard": "passed", "pointer_detail": "passed"}
        record("390px narrow layout, keyboard/pointer operation and overflow access", narrow_viewport)

        browser.close()

    report = {
        "schema": "preset-browser-acceptance-results/1",
        "started_at_utc": started_at,
        "target": {
            "html": str(TARGET / "ui-presets.html"),
            "css": str(TARGET / "ui-presets.css"),
            "html_sha256": hashlib.sha256((TARGET / "ui-presets.html").read_bytes()).hexdigest(),
            "css_sha256": hashlib.sha256((TARGET / "ui-presets.css").read_bytes()).hexdigest(),
        },
        "browser": browser_metadata,
        "original_rows": original_rows,
        "actions": actions,
        "outcomes": outcomes,
        "measurements": measurements,
        "raw_errors": raw_errors,
        "screenshots": [str(p) for p in sorted(ARTIFACTS.glob("*.png"))],
        "attempts": [
            {"attempt": 1, "harness_corrections": 0, "command": "python /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/validate_presets.py", "outcome": "completed with failures retained", "outcomes": json.loads((ROOT / "attempt-1-results.json").read_text())["outcomes"]},
            {"attempt": 2, "harness_corrections": 1, "command": "python /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/validate_presets.py", "outcome": "completed with failures retained", "outcomes": json.loads((ROOT / "attempt-2-results.json").read_text())["outcomes"]},
            {"attempt": 3, "harness_corrections": 2, "command": "python /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/validate_presets.py", "outcome": "completed"}
        ],
        "measurements_unavailable": {"tokens": None, "cost": None, "provider_identity": None, "active_time": None},
    }
    (ROOT / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"outcomes": outcomes, "raw_errors": raw_errors, "results_path": str(ROOT / "results.json"), "screenshots": report["screenshots"]}, indent=2))


if __name__ == "__main__":
    main()
