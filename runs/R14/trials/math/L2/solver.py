import argparse, json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[5]
DEFAULT_INPUT = ROOT / 'runs/R14/cases/math/problem.json'
OUT = Path(__file__).resolve().parent

def validate(data):
    hist=data.get('data')
    dist=data.get('distribution', {})
    if not isinstance(hist,list) or len(hist)<2: raise ValueError('data must be a list with at least two weeks')
    stations=list(hist[0].keys()); stations.remove('week')
    for row in hist:
        if set(row)!=set(['week',*stations]) or any(not isinstance(row[s],(int,float)) or isinstance(row[s],bool) or row[s]<0 for s in stations): raise ValueError('history schema/values invalid')
    for key in ('station_caps','delivery_cost_per_unit','unmet_prediction_penalty_per_unit'):
        d=dist.get(key)
        if not isinstance(d,dict) or set(d)!=set(stations): raise ValueError(f'{key} must provide each station')
        for s,v in d.items():
            if not isinstance(v,(int,float)) or isinstance(v,bool) or v<0: raise ValueError(f'{key}.{s} must be a nonnegative number')
    if any(not isinstance(dist.get('total_available_units'),int) or dist['total_available_units']<0 for _ in [0]): raise ValueError('total_available_units must be a nonnegative integer')
    if any(int(dist['station_caps'][s]) != dist['station_caps'][s] or dist['station_caps'][s]<0 for s in stations): raise ValueError('caps must be nonnegative integers')
    return stations

def forecast(y):
    x=np.arange(1,len(y)+1,dtype=float)
    return float(np.polyval(np.polyfit(x,np.asarray(y,dtype=float),1),len(y)+1))

def run(data):
    stations=validate(data); hist=data['data']; dist=data['distribution']
    pred={s:forecast([r[s] for r in hist]) for s in stations}
    # Expanding origin: train weeks 1..t-1, predict week t, t=4..n. Compare seasonal-free last observation baseline.
    validation={s:{'model_abs_errors':[],'naive_abs_errors':[]} for s in stations}
    for t in range(3,len(hist)):
        for s in stations:
            yy=[r[s] for r in hist[:t]]; actual=hist[t][s]
            validation[s]['model_abs_errors'].append(abs(forecast(yy)-actual))
            validation[s]['naive_abs_errors'].append(abs(yy[-1]-actual))
    # Exact exhaustive integer enumeration across station caps and total stock; tie break lexicographically.
    best=None; best_x=None
    for a in range(int(dist['station_caps'][stations[0]])+1):
      for b in range(int(dist['station_caps'][stations[1]])+1):
       for c in range(int(dist['station_caps'][stations[2]])+1):
        vals=(a,b,c)
        if sum(vals)>dist['total_available_units']: continue
        obj=sum(dist['delivery_cost_per_unit'][s]*x+dist['unmet_prediction_penalty_per_unit'][s]*max(pred[s]-x,0) for s,x in zip(stations,vals))
        if best is None or obj<best-1e-10: best,best_x=obj,vals
    alloc=dict(zip(stations,best_x))
    # independently recompute objective and feasibility from emitted values
    obj=sum(dist['delivery_cost_per_unit'][s]*alloc[s]+dist['unmet_prediction_penalty_per_unit'][s]*max(pred[s]-alloc[s],0) for s in stations)
    result={'case_id':data.get('case_id'),'units':data['units'],'prediction':{'method':'per-station ordinary least-squares linear trend on all observed weeks; extrapolate one week; no external covariates','values':pred,'assumption':'short stable local linear trend; predictions may be fractional and are optimization demand targets'},'validation':{'method':'expanding-origin chronological holdout, training weeks 1..t-1, t=4..8; model parameters refit at each origin','station_metrics':{s:{'n_origins':len(validation[s]['model_abs_errors']),'linear_trend_MAE':float(np.mean(validation[s]['model_abs_errors'])),'last_observation_MAE':float(np.mean(validation[s]['naive_abs_errors']))} for s in stations},'all_origins_model_MAE':float(np.mean([e for s in stations for e in validation[s]['model_abs_errors']])),'all_origins_last_observation_MAE':float(np.mean([e for s in stations for e in validation[s]['naive_abs_errors']])),'no_future_data_used':True},'allocation':alloc,'allocation_checks':{'integer_nonnegative':all(isinstance(x,int) and x>=0 for x in alloc.values()),'within_caps':all(alloc[s]<=dist['station_caps'][s] for s in stations),'total_used':sum(alloc.values()),'total_available':dist['total_available_units'],'within_total':sum(alloc.values())<=dist['total_available_units']},'objective':{'formula':dist['objective'],'value_CNY':obj,'components_CNY':{s:{'delivery':dist['delivery_cost_per_unit'][s]*alloc[s],'unmet':dist['unmet_prediction_penalty_per_unit'][s]*max(pred[s]-alloc[s],0)} for s in stations},'optimality_evidence':'Exhaustive enumeration of every integer triple within station caps and total stock; global optimum for this finite stated model.'}}
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,default=DEFAULT_INPUT); ap.add_argument('--output',type=Path,default=OUT/'results.json'); ap.add_argument('--figure',type=Path,default=OUT/'demand_allocation.png'); a=ap.parse_args()
    data=json.loads(a.input.read_text(encoding='utf-8')); res=run(data)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.figure.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    h=data['data']; fig,axs=plt.subplots(1,2,figsize=(10,4.2))
    weeks=[r['week'] for r in h]
    for s in res['prediction']['values']:
      axs[0].plot(weeks,[r[s] for r in h],marker='o',label=f'{s} observed')
      axs[0].scatter([9],[res['prediction']['values'][s]],marker='x',s=70,label=f'{s} week 9 forecast')
    axs[0].set(title='Observed demand and week 9 forecast',xlabel='Week',ylabel='Demand (units/week)'); axs[0].legend(fontsize=7,ncol=2); axs[0].grid(alpha=.25)
    ss=list(res['allocation']); axs[1].bar(ss,[res['prediction']['values'][s] for s in ss],label='Forecast',alpha=.6); axs[1].bar(ss,[res['allocation'][s] for s in ss],label='Allocated',alpha=.8); axs[1].set(title=f"Week 9 allocation ({sum(res['allocation'].values())}/{data['distribution']['total_available_units']} units)",ylabel='Units'); axs[1].legend(); axs[1].grid(axis='y',alpha=.25)
    fig.suptitle('Source: supplied weeks 1–8; model predictions and exact allocation'); fig.tight_layout(); fig.savefig(a.figure,dpi=160); plt.close(fig)
    print(json.dumps({'output':str(a.output),'figure':str(a.figure),'objective_CNY':res['objective']['value_CNY'],'allocation':res['allocation']},ensure_ascii=False))
if __name__=='__main__': main()
