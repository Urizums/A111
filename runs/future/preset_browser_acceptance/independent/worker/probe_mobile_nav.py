#!/usr/bin/env python3
"""Supplemental check that narrow-screen navigation overflow remains reachable."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/workspace/A111/runs/future/preset_browser_acceptance/independent/worker")
URL = "http://127.0.0.1:8765/ui-presets.html"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    page.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    for _ in range(6):
        page.keyboard.press("Tab")
    keyboard_state = page.evaluate("""() => {
      const nav=document.querySelector('.primary-nav'), last=nav.querySelector('a[href="#settings"]');
      const n=nav.getBoundingClientRect(), r=last.getBoundingClientRect();
      return {activeText:document.activeElement.innerText.trim(),navClientWidth:nav.clientWidth,navScrollWidth:nav.scrollWidth,navScrollLeft:nav.scrollLeft,navRect:{left:n.left,right:n.right},lastLinkRect:{left:r.left,right:r.right},pageScrollWidth:document.documentElement.scrollWidth};
    }""")
    page.screenshot(path=str(ROOT / "screenshots" / "mobile-nav-keyboard.png"), full_page=False, animations="disabled")
    assert keyboard_state["activeText"] == "Preferences", keyboard_state
    assert keyboard_state["navScrollWidth"] > keyboard_state["navClientWidth"], keyboard_state
    assert keyboard_state["navScrollLeft"] > 0, keyboard_state
    assert keyboard_state["lastLinkRect"]["left"] >= keyboard_state["navRect"]["left"] - 1, keyboard_state
    assert keyboard_state["lastLinkRect"]["right"] <= keyboard_state["navRect"]["right"] + 1, keyboard_state
    assert keyboard_state["pageScrollWidth"] == 390, keyboard_state

    page.goto(URL, wait_until="networkidle")
    nav = page.locator(".primary-nav")
    nav.scroll_into_view_if_needed()
    rect = nav.bounding_box()
    page.mouse.move(rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2)
    page.mouse.wheel(350, 0)
    page.wait_for_timeout(100)
    pointer_state = page.evaluate("""() => {
      const nav=document.querySelector('.primary-nav'), last=nav.querySelector('a[href="#settings"]');
      const n=nav.getBoundingClientRect(), r=last.getBoundingClientRect();
      return {navClientWidth:nav.clientWidth,navScrollWidth:nav.scrollWidth,navScrollLeft:nav.scrollLeft,navRect:{left:n.left,right:n.right},lastLinkRect:{left:r.left,right:r.right},pageScrollWidth:document.documentElement.scrollWidth};
    }""")
    assert pointer_state["navScrollLeft"] > 0, pointer_state
    assert pointer_state["lastLinkRect"]["right"] <= pointer_state["navRect"]["right"] + 1, pointer_state
    assert pointer_state["pageScrollWidth"] == 390, pointer_state
    assert not errors, errors
    result = {"command": "python /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/probe_mobile_nav.py", "viewport": {"width": 390, "height": 844}, "keyboard": keyboard_state, "pointer_horizontal_wheel": pointer_state, "raw_errors": errors, "status": "passed"}
    (ROOT / "mobile-nav-access.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    browser.close()
