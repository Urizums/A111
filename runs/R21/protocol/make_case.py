"""One fixed original case; coordinator-private generation, never author input."""
import csv
import hashlib
import json
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'runs/R21'
RAW = BASE / 'inputs/raw'
PRIVATE = BASE / 'evaluation'
lock = json.loads((BASE / 'protocol-lock.json').read_text(encoding='utf-8'))
for row in lock['files']:
    b = (ROOT / row['path']).read_bytes()
    assert len(b) == row['size_bytes'] and hashlib.sha256(b).hexdigest() == row['sha256']
assert not RAW.exists() and not PRIVATE.exists(), 'Never replace/reseed a realized case.'
RAW.mkdir(parents=True)
PRIVATE.mkdir()
rng = random.Random(2026100902)
start, origin, end = date(2026,5,1), datetime(2026,10,31,18), date(2026,12,12)
future_begin = date(2026,11,1)
stores = [(f'S{i:02}',f'Z{(i-1)//4+1}',0.72+0.041*i) for i in range(1,13)]
items = [(f'K{j:02}',2+j%4,2.5+0.6*j,0.6+0.15*j,55) for j in range(1,9)]

def write(folder, name, headers, rows):
    with (folder / name).open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)

write(RAW,'stores.csv',['store_id','zone_id'],[(s,z) for s,z,_ in stores])
write(RAW,'items.csv',['item_id','procurement_yuan','shortage_yuan','waste_yuan','daily_max_units'],items)
reports, weather, promo, calendar, truth = [], [], [], [], []
common = 0.0
for n in range((end-start).days+1):
    day = start + timedelta(days=n)
    ds = day.isoformat()
    lead = (day-future_begin).days
    event = int(n%19 in [5,6]) if day<future_begin else int(lead%7 in [2,3])
    calendar.append([ds,day.weekday(),event])
    common = 0.38*common+rng.gauss(0,1.25)
    zone_rain = {}
    for z in range(1,4):
        rain = max(0,6+5*math.cos(n*0.37+z)+rng.gauss(0,3))
        zone_rain[f'Z{z}'] = rain
        publish = datetime.combine(day-timedelta(days=1),datetime.min.time())+timedelta(hours=16)
        if day>=future_begin and lead<14:
            publish = origin.replace(hour=16)
        forecast = '' if rng.random()<0.03 else round(max(0,rain+rng.gauss(0,3.5)),2)
        weather.append([ds,f'Z{z}',publish.isoformat(),'forecast',forecast])
        if day<future_begin:
            weather.append([ds,f'Z{z}',(datetime.combine(day,datetime.min.time())+timedelta(days=1,hours=9)).isoformat(),'observed',round(rain,2)])
    for s,z,scale in stores:
        for j,(k,cost,cu,co,cap) in enumerate(items,1):
            discount = 0.12 if (n+int(s[1:])*2+j*5)%29<5 else 0.0
            announce = datetime.combine(day-timedelta(days=10),datetime.min.time())+timedelta(hours=12)
            promo.append([ds,s,k,announce.isoformat(),discount])
            mean = (8.4+1.05*j)*scale+(2.1+0.23*j)*int(day.weekday()>=5)
            mean += (2.6+0.24*j)*event+25*discount-0.12*zone_rain[z]
            mean += 0.006*n*(1 if j%2 else -0.2)+common
            sigma = 1.5+0.065*max(mean,0)+0.55*event
            y = max(0,round(mean+rng.gauss(0,sigma)))
            if day>=future_begin:
                truth.append([ds,s,k,y])
                continue
            publish = datetime.combine(day,datetime.min.time())+timedelta(days=1,hours=9)
            value = max(0,y-rng.choice([0,0,0,1]))
            reports.append([ds,s,k,1,publish.isoformat(),value,round(y*(cost+4),2)])
            if rng.random()<0.22:
                reports.append([ds,s,k,2,(publish+timedelta(days=2)).isoformat(),y,round(y*(cost+4),2)])
    if day<future_begin and n in [16,47,91,141,173]:
        reports.extend([reports[-1].copy(),reports[-2].copy()])
write(RAW,'demand_reports.csv',['service_date','store_id','item_id','revision','available_at','demand_units','settlement_yuan'],reports)
write(RAW,'weather.csv',['service_date','zone_id','available_at','kind','rain_mm'],weather)
write(RAW,'promotions.csv',['service_date','store_id','item_id','announced_at','discount_fraction'],promo)
write(RAW,'calendar.csv',['service_date','weekday_monday_zero','holiday'],calendar)
write(PRIVATE,'holdout_truth.csv',['service_date','store_id','item_id','demand_units'],truth)
decision = dict(origin=origin.isoformat(),timezone='Asia/Shanghai',future_begin=future_begin.isoformat(),future_end=end.isoformat(),
    capacity_units_per_day=1600,procurement_budget_yuan_per_day=6000,inventory='fresh daily; no carry; unmet demand lost',
    activity='holiday column is a fictional two-day business event, not official holiday',horizon_days=42)
(RAW/'decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary = dict(original=True,seed=2026100902,stores=12,items=8,history_dates=184,future_dates=42,future_rows=len(truth),
    report_rows=len(reports),public_raw_files=7,regeneration_allowed=False,future_truth_read_by_author=False,
    limits='Synthetic mechanism known to coordinator, withheld from builders/executors/independent initial preparation; no contest solution or real business data.')
assert len(truth)==4032
for band in range(6):
    rs=calendar[-42+7*band:-42+7*(band+1)] if band<5 else calendar[-7:]
    assert len(rs)==7 and sum(int(r[2]) for r in rs)==2
(PRIVATE/'generation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
