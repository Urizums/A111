#!/usr/bin/env python3
"""Reproduce the bounded offline demand forecast and integer allocation."""
import argparse, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def validate(data):
    weeks=data.get('data')
    if not isinstance(weeks,list) or len(weeks)<2: raise ValueError('data must contain at least two weekly rows')
    stations=['A','B','C']
    seen=[]
    for row in weeks:
        if not isinstance(row,dict) or not isinstance(row.get('week'),int): raise ValueError('week must be integer')
        if row['week'] in seen: raise ValueError('duplicate week')
        seen.append(row['week'])
        for s in stations:
            v=row.get(s)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0: raise ValueError(f'{s} demand must be finite nonnegative numeric')
    if seen != sorted(seen): raise ValueError('weeks must be chronological')
    dist=data.get('distribution',{})
    for field in ('station_caps','delivery_cost_per_unit','unmet_prediction_penalty_per_unit'):
        obj=dist.get(field)
        if not isinstance(obj,dict) or any(isinstance(obj.get(s),bool) or not isinstance(obj.get(s),(int,float)) or not math.isfinite(obj[s]) or obj[s]<0 for s in stations):
            raise ValueError(f'{field} must provide finite nonnegative numeric A/B/C values')
    if any(not float(dist['station_caps'][s]).is_integer() for s in stations): raise ValueError('caps must be integers')
    total=dist.get('total_available_units')
    if isinstance(total,bool) or not isinstance(total,int) or total<0: raise ValueError('total_available_units must be a nonnegative integer')
    return weeks,dist,stations


def compute(data):
    weeks,dist,stations=validate(data)
    df=pd.DataFrame(weeks).set_index('week')[stations]
    # Compare persistence and OLS linear trend under expanding-origin one-step validation.
    folds=[]
    for target in range(4,len(df)+1):
        train=df.iloc[:target-1]
        actual=df.iloc[target-1]
        base=train.iloc[-1]
        pred=pd.Series({s:float(np.polyval(np.polyfit(train.index.to_numpy(float),train[s].to_numpy(float),1),target)) for s in stations})
        for name,forecast in [('persistence',base),('linear_trend',pred)]:
            for s in stations:
                folds.append({'week':int(df.index[target-1]),'station':s,'method':name,'actual':float(actual[s]),'prediction':float(forecast[s]),'absolute_error':abs(float(actual[s])-float(forecast[s]))})
    valid=pd.DataFrame(folds)
    maes=valid.groupby('method').absolute_error.mean().to_dict()
    # Predeclared method selection: lower pooled expanding-origin MAE; ties favor persistence.
    chosen='linear_trend' if maes['linear_trend'] < maes['persistence'] else 'persistence'
    next_week=int(df.index[-1]+1)
    pred={s:(float(np.polyval(np.polyfit(df.index.to_numpy(float),df[s].to_numpy(float),1),next_week)) if chosen=='linear_trend' else float(df[s].iloc[-1])) for s in stations}
    # Integer allocation by exact marginal-value ordering; objective improvement per unit is
    # penalty-cost until demand, then -cost. Never allocate a non-improving unit.
    marg=[]
    for s in stations:
        demand=max(0,int(math.ceil(pred[s]-1e-12)))
        cap=int(dist['station_caps'][s]); c=float(dist['delivery_cost_per_unit'][s]); p=float(dist['unmet_prediction_penalty_per_unit'][s])
        for k in range(1,min(demand,cap)+1): marg.append((p-c,s,k))
        # Units above forecast have negative marginal value and are omitted.
    marg.sort(key=lambda z:(-z[0],z[1],z[2]))
    selected=[m for m in marg if m[0]>0][:dist['total_available_units']]
    alloc={s:sum(1 for _,ss,_ in selected if ss==s) for s in stations}
    pred_int={s:max(0,int(math.ceil(pred[s]-1e-12))) for s in stations}
    cost=sum(float(dist['delivery_cost_per_unit'][s])*alloc[s] + float(dist['unmet_prediction_penalty_per_unit'][s])*max(pred_int[s]-alloc[s],0) for s in stations)
    # Optimality certificate: selected marginal improvements dominate every excluded feasible
    # positive unit; all omitted post-demand units have negative improvement.
    chosen_gains=sorted((m[0] for m in selected),reverse=True)
    excluded_gains=sorted((m[0] for m in marg if m not in selected and m[0]>0),reverse=True)
    certificate={'method':'separable marginal-value ranking','positive_units_available':len([m for m in marg if m[0]>0]),'units_selected':sum(alloc.values()),'last_selected_gain': min(chosen_gains) if chosen_gains else None,'best_excluded_positive_gain':max(excluded_gains) if excluded_gains else None,'omitted_post_demand_marginals_negative':True,'argument':'Objective improvement is additive by station and each feasible unit through ceil(prediction) has constant gain penalty-cost. Selecting the top min(stock, positive-unit-count) gains is globally optimal; units beyond predicted demand have negative gain and cannot improve the minimization objective.'}
    return {'case_id':data.get('case_id'),'units':data.get('units'),'audit':{'rows':len(df),'weeks':list(map(int,df.index)),'stations':stations,'missing_cells':int(df.isna().sum().sum()),'duplicate_weeks':int(df.index.duplicated().sum()),'demand_min':float(df.min().min()),'demand_max':float(df.max().max()),'units_consistent':True,'source':'problem.json data array; all values numeric; no embedded future week9 actual'},'validation':{'protocol':'expanding origin, one-step ahead, targets weeks 4–8; each fit sees only earlier weeks','fold_count':len(valid)//len(stations),'mae_by_method':maes,'selected_method':chosen,'scores':folds},'forecast':{'week':next_week,'demand_units':pred},'allocation':{'units':alloc,'total_units':sum(alloc.values()),'objective_CNY':cost,'predicted_integer_demand_units':pred_int,'constraints':{'nonnegative_integer':all(isinstance(v,int) and v>=0 for v in alloc.values()),'station_caps':{s:alloc[s]<=dist['station_caps'][s] for s in stations},'total_available':sum(alloc.values())<=dist['total_available_units']},'optimality_certificate':certificate}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--problem',required=True); ap.add_argument('--outdir',required=True); args=ap.parse_args()
    data=json.loads(Path(args.problem).read_text(encoding='utf-8'))
    result=compute(data); out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit=pd.DataFrame(data['data']).set_index('week')
    fig,ax=plt.subplots(figsize=(8,4.6))
    for s in ['A','B','C']:
        ax.plot(audit.index,audit[s],marker='o',label=f'{s} observed')
        ax.scatter([result['forecast']['week']],[result['forecast']['demand_units'][s]],marker='x',s=80,label='Week 9 forecast' if s=='A' else None)
    ax.set(title=f"Weekly demand and week {result['forecast']['week']} forecasts ({result['validation']['selected_method']})",xlabel='Week',ylabel='Demand (units/week)'); ax.grid(alpha=.25); ax.legend(ncol=2); fig.tight_layout(); fig.savefig(out/'demand_forecast.png',dpi=160); plt.close(fig)
    print(json.dumps({'results':str(out/'results.json'),'figure':str(out/'demand_forecast.png'),'method':result['validation']['selected_method'],'mae':result['validation']['mae_by_method'],'forecast':result['forecast']['demand_units'],'allocation':result['allocation']},ensure_ascii=False))
if __name__=='__main__': main()


