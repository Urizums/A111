import json, math, hashlib
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[5]
PROBLEM = BASE / 'runs/R14/cases/math/problem.json'
OUT = Path(__file__).resolve().parent

def load_and_validate(path):
    raw = path.read_bytes()
    obj = json.loads(raw.decode('utf-8'))
    stations = ['A','B','C']
    weeks = obj['data']
    if len(weeks) != 8 or [w['week'] for w in weeks] != list(range(1,9)):
        raise ValueError('Expected exactly weeks 1–8 in order')
    for w in weeks:
        for s in stations:
            if isinstance(w.get(s), bool) or not isinstance(w.get(s), (int,float)) or not math.isfinite(w[s]) or w[s] < 0:
                raise ValueError(f'Invalid nonnegative numeric demand: week {w.get("week")}, station {s}')
    dist = obj['distribution']
    for group in ('delivery_cost_per_unit','unmet_prediction_penalty_per_unit','station_caps'):
        for s in stations:
            v = dist[group][s]
            if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or v < 0:
                raise ValueError(f'Invalid numeric {group}[{s}]: {v!r}')
    total = dist['total_available_units']
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError('total_available_units must be a nonnegative integer')
    return obj, hashlib.sha256(raw).hexdigest()

def forecasts(data, target_week):
    x = np.array([r['week'] for r in data], dtype=float)
    result = {}
    for s in 'ABC':
        slope, intercept = np.polyfit(x, [r[s] for r in data], 1)
        result[s] = float(slope*target_week + intercept)
    return result

def score(x, pred, dist):
    return sum(dist['delivery_cost_per_unit'][s]*x[s] + dist['unmet_prediction_penalty_per_unit'][s]*max(pred[s]-x[s],0) for s in 'ABC')

def optimize(pred, dist):
    caps, total = dist['station_caps'], dist['total_available_units']
    best = None
    for a in range(int(caps['A'])+1):
      for b in range(int(caps['B'])+1):
       for c in range(int(caps['C'])+1):
        if a+b+c > total: continue
        x = {'A':a,'B':b,'C':c}
        v = score(x,pred,dist)
        if best is None or v < best[0]: best=(v,x)
    return best

def main():
    obj, digest = load_and_validate(PROBLEM)
    data=obj['data']; dist=obj['distribution']; pred=forecasts(data, 9)
    # Rolling-origin evaluation: for target weeks 3..8 fit only weeks before target.
    errors={s:[] for s in 'ABC'}; naive={s:[] for s in 'ABC'}
    for target in range(3,9):
        train=data[:target-1]; actual=data[target-1]
        p=forecasts(train, target)
        for s in 'ABC':
            errors[s].append(abs(p[s]-actual[s]))
            naive[s].append(abs(train[-1][s]-actual[s]))
    mae={s:float(np.mean(errors[s])) for s in 'ABC'}
    naive_mae={s:float(np.mean(naive[s])) for s in 'ABC'}
    alloc_obj, alloc=optimize(pred,dist)
    # independent recomputation and feasibility checks
    recomputed=score(alloc,pred,dist)
    assert all(isinstance(v,int) and v>=0 and v<=dist['station_caps'][s] for s,v in alloc.items())
    assert sum(alloc.values())<=dist['total_available_units'] and math.isclose(recomputed,alloc_obj)
    # Exercise the production input loader with the supplied malformed-cost variant.
    bad=json.loads(json.dumps(obj)); bad['distribution']['delivery_cost_per_unit']['A']='two CNY'
    bad_path=OUT/'malformed-cost-input.json'
    bad_path.write_text(json.dumps(bad,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    malformed_rejected=False
    try:
        load_and_validate(bad_path)
    except ValueError: malformed_rejected=True
    assert malformed_rejected
    results={'input_sha256':digest,'units':obj['units'],'forecast_method':'Per-station ordinary least-squares linear trend, demand ~ week, fit weeks 1–8; extrapolate to week 9; no future demand used.','predictions_week9':{s:round(pred[s],6) for s in 'ABC'},'validation':{'method':'For each target week 3–8, fit only earlier weeks and forecast that specific next week; compare to last-observation naive baseline.','targets':[3,4,5,6,7,8],'linear_trend_mae_units_per_week':mae,'naive_last_value_mae_units_per_week':naive_mae,'interpretation':'Six origins only; descriptive, not evidence of general superiority.'},'allocation':alloc,'allocation_objective_CNY':round(alloc_obj,6),'objective_recomputed_CNY':round(recomputed,6),'allocation_terms_CNY':{s:{'delivery':dist['delivery_cost_per_unit'][s]*alloc[s],'unmet':dist['unmet_prediction_penalty_per_unit'][s]*max(pred[s]-alloc[s],0)} for s in 'ABC'},'constraints':{'total_allocated':sum(alloc.values()),'total_available':dist['total_available_units'],'station_caps':dist['station_caps'],'nonnegative_integer':True,'all_feasible':True},'optimality_evidence':'Exhaustive enumeration of all integer triples within station caps and total stock (31*26*36 upper bound; infeasible triples skipped); minimum objective found. Exact only for stated forecast/objective/constraints.','malformed_cost_boundary':{'outcome':'rejected','input_file':'malformed-cost-input.json','validation_entrypoint':'load_and_validate','reason':'nonnumeric delivery_cost_per_unit[A]','optimization_performed':False},'limitations':['Eight observations per station; linear trend is a simple baseline and ignores seasonality/uncertainty.','Penalty and delivery costs treated as supplied deterministic inputs.','No empirical comparison beyond six rolling origins; no contest or real deployment conclusion.']}
    (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fig,ax=plt.subplots(figsize=(8,4.8))
    x=np.arange(1,10)
    colors={'A':'#1769aa','B':'#d17a00','C':'#32804b'}
    for s in 'ABC':
        ax.plot(range(1,9),[r[s] for r in data],marker='o',color=colors[s],label=f'{s} observed')
        ax.scatter([9],[pred[s]],marker='x',s=70,color=colors[s],label=f'{s} week 9 forecast')
    ax.set(title='Weekly demand and week 9 linear-trend forecasts',xlabel='Week',ylabel='Demand (units/week)')
    ax.set_xticks(x); ax.grid(alpha=.25); ax.legend(ncol=2,fontsize=8); fig.tight_layout()
    fig.savefig(OUT/'demand_forecast.png',dpi=160); plt.close(fig)
    print(json.dumps({'predictions':results['predictions_week9'],'allocation':alloc,'objective':alloc_obj,'mae':mae,'naive_mae':naive_mae,'malformed_rejected':malformed_rejected},ensure_ascii=False))
if __name__=='__main__': main()
