"""Coordinator's original fixture; not an agent input, solution or skill runner."""
import csv
import hashlib
import json
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / 'runs/R20/inputs/raw'
PRIVATE = ROOT / 'runs/R20/evaluation'
assert not RAW.exists(), 'Do not replace a frozen sample.'
RAW.mkdir(parents=True)
PRIVATE.mkdir(exist_ok=True)
rng = random.Random(2026100901)
start = date(2026, 5, 1)
origin = datetime(2026, 9, 30, 18)
end = date(2026, 10, 14)
stores = [(f'S{i:02}', f'Z{(i-1)//4+1}', round(0.8+i*0.035, 3)) for i in range(1, 13)]
skus = [(f'K{j:02}', 2+j%4, 2.5+j*0.6, 0.6+j*0.15, 55) for j in range(1, 9)]

def write(name, headers, rows, private=False):
    path = (PRIVATE if private else RAW) / name
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
    return path

write('stores.csv', ['store_id', 'zone_id'], [(s, z) for s, z, _ in stores])
write('items.csv', ['item_id', 'procurement_yuan', 'shortage_yuan', 'waste_yuan', 'daily_max_units'], skus)
reports, weather, promo, calendar, truth = [], [], [], [], []
for n in range((end-start).days+1):
    day = start+timedelta(days=n)
    ds = day.isoformat()
    holiday = int(day in {date(2026,6,19), date(2026,9,25)} or day.month == 10 and day.day <= 7)
    calendar.append([ds, day.weekday(), holiday])
    for z in range(1,4):
        rain = max(0, 5+7*math.sin(n*0.71+z)+rng.gauss(0,4))
        forecast = max(0, rain+rng.gauss(0,3))
        weather.append([ds, f'Z{z}', (datetime.combine(day-timedelta(days=1),datetime.min.time())+timedelta(hours=16)).isoformat(), 'forecast', round(forecast,2)])
        if day < date(2026,10,1):
            weather.append([ds,f'Z{z}',(datetime.combine(day,datetime.min.time())+timedelta(days=1,hours=9)).isoformat(),'observed',round(rain,2)])
        # Future forecasts are a 14-day bulletin actually available at this task's fixed origin.
        if day >= date(2026,10,1):
            weather[-1][2] = origin.replace(hour=16).isoformat()
        for s, zone, scale in stores:
            if zone != f'Z{z}':
                continue
            for j, (sku, cost, cu, co, cap) in enumerate(skus,1):
                discount = 0.15 if (n+int(s[1:])*3+j*2)%23 < 4 else 0
                announced = datetime.combine(day-timedelta(days=10),datetime.min.time())+timedelta(hours=12)
                if announced > origin:
                    announced = origin-timedelta(days=4)
                promo.append([ds,s,sku,announced.isoformat(),discount])
                base = (7+j*1.5)*scale
                mean = base + (3+j*0.4)*int(day.weekday() >= 5)+5*holiday+32*discount-0.18*rain
                mean += max(0,n-80)*0.035*(1 if j%2 else -0.3)
                demand = max(0, round(mean+rng.gauss(0, 2+mean*0.12)))
                if day >= date(2026,10,1):
                    truth.append([ds,s,sku,demand])
                    continue
                publish = datetime.combine(day,datetime.min.time())+timedelta(days=1,hours=9)
                provisional = max(0,demand-rng.choice([0,0,0,1,2]))
                reports.append([ds,s,sku,1,publish.isoformat(),provisional,round(demand*(cost+4),2)])
                revise = publish+timedelta(days=2)
                if rng.random() < 0.2 and revise <= origin:
                    reports.append([ds,s,sku,2,revise.isoformat(),demand,round(demand*(cost+4),2)])
    # A raw export can contain repeated delivery rows; identities and revision timestamps distinguish updates.
    if n in [13,39,85,112]:
        reports.extend([reports[-1].copy(),reports[-2].copy()])

# Forecast missingness belongs to the public raw snapshot, not a prescribed imputation method.
for row in weather:
    if row[3] == 'forecast' and rng.random() < 0.025:
        row[4] = ''
write('demand_reports.csv', ['service_date','store_id','item_id','revision','available_at','demand_units','settlement_yuan'], reports)
write('weather.csv', ['service_date','zone_id','available_at','kind','rain_mm'], weather)
write('promotions.csv', ['service_date','store_id','item_id','announced_at','discount_fraction'], promo)
write('calendar.csv', ['service_date','weekday_monday_zero','holiday'], calendar)
write('holdout_truth.csv', ['service_date','store_id','item_id','demand_units'],truth,private=True)
config = dict(origin=origin.isoformat(),timezone='Asia/Shanghai',future_begin='2026-10-01',future_end='2026-10-14',
    capacity_units_per_day=1600,procurement_budget_yuan_per_day=6000,inventory='fresh daily; no carry; unmet demand lost')
(RAW/'decision.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
summary = dict(original=True, seed=2026100901, stores=12,items=8,history_days=153,future_days=14,
    report_rows=len(reports),weather_rows=len(weather),future_truth_rows=len(truth),
    limits='Entirely synthetic, no contest question/solution or real customer data. Generator and future truth withheld from production.')
(PRIVATE/'generation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
assert len(truth) == 1344 and len(calendar) == 167
print(json.dumps(summary))
