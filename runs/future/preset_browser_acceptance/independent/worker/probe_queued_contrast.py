#!/usr/bin/env python3
"""Supplemental live contrast measurement for the queued status label."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/workspace/A111/runs/future/preset_browser_acceptance/independent/worker")
URL = "http://127.0.0.1:8765/ui-presets.html"

def lum(rgb):
    values=[]
    for channel in rgb:
        x=channel/255
        values.append(x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4)
    return 0.2126*values[0]+0.7152*values[1]+0.0722*values[2]

def ratio(fg,bg):
    l1,l2=sorted((lum(fg),lum(bg)),reverse=True)
    return round((l1+0.05)/(l2+0.05),2)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path="/usr/bin/chromium",headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1440,"height":1000})
    page.route("**/favicon.ico",lambda route:route.fulfill(status=204,body=""))
    page.goto(URL,wait_until="networkidle")
    page.locator("#create-run").click()
    records=[]
    for palette in ("clear","night"):
        page.locator("#palette-choice").select_option(palette)
        sample=page.locator(".status-queued").evaluate("""el=>{
          const f=getComputedStyle(el).color.match(/[0-9.]+/g).slice(0,3).map(Number);
          let bg=[0,0,0,0];
          for(let n=el;n;n=n.parentElement){const m=getComputedStyle(n).backgroundColor.match(/[0-9.]+/g);if(!m)continue;const a=m.length>=4?Number(m[3]):1,c=[Number(m[0]),Number(m[1]),Number(m[2]),a],ba=c[3]+bg[3]*(1-c[3]);if(ba)bg=[0,1,2].map(i=>(c[i]*c[3]+bg[i]*bg[3]*(1-c[3]))/ba).concat([ba]);if(ba>=.999)break;}
          return {text:el.innerText,foreground:f,background:bg.slice(0,3),computedForeground:getComputedStyle(el).color,computedBackground:`rgba(${bg.join(',')})`};
        }""")
        sample["palette"]=palette
        sample["contrast_ratio"]=ratio(sample["foreground"],sample["background"])
        records.append(sample)
    result={"command":"python /workspace/A111/runs/future/preset_browser_acceptance/independent/worker/probe_queued_contrast.py","browser":"Chromium via /usr/bin/chromium","viewport":{"width":1440,"height":1000},"checks":records,"threshold_normal_text":4.5,"status":"passed" if all(x["contrast_ratio"]>=4.5 for x in records) else "failed"}
    (ROOT/"queued-contrast.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    browser.close()
