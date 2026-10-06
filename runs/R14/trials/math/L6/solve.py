#!/usr/bin/env python
"""Reproducible offline forecast and integer allocation for problem.json."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
import matplotlib.pyplot as plt


def solve(problem: dict) -> dict:
    weeks = problem.get('data')
    if not isinstance(weeks, list) or len(weeks) < 3:
        raise ValueError('data must contain at least 3 weekly observations')
    stations = ['A', 'B', 'C']
    df = pd.DataFrame(weeks)
    required = {'week', *stations}
    if set(df.columns) != required or df[list(required)].isna().any().any():
        raise ValueError('data schema/missing-value check failed')
    for c in required:
        if not pd.api.types.is_numeric_dtype(df[c]) or not np.isfinite(df[c].to_numpy(dtype=float)).all():
            raise ValueError(f'data field {c} must be finite numeric')
    if df.week.duplicated().any() or not (df.week.diff().dropna() > 0).all():
        raise ValueError('week values must be unique and strictly increasing')
    if (df[stations] < 0).any().any():
        raise ValueError('demand must be nonnegative')

    # Audit is descriptive and does not alter raw observations.
    audit = {'rows': int(len(df)), 'stations': stations, 'missing_cells': int(df.isna().sum().sum()),
             'duplicate_weeks': int(df.week.duplicated().sum()),
             'weeks': [int(df.week.min()), int(df.week.max())],
             'demand_min': {s: float(df[s].min()) for s in stations},
             'demand_max': {s: float(df[s].max()) for s in stations},
             'units': problem['units']}
    # Rolling-origin one-step validation. Fit OLS on weeks strictly before target.
    val = {}
    for s in stations:
        rows = []
        for j in range(3, len(df)):
            hist = df.iloc[:j]
            t = float(df.week.iloc[j])
            pred_trend = float(np.polyfit(hist.week.to_numpy(float), hist[s].to_numpy(float), 1)[0] * t +
                               np.polyfit(hist.week.to_numpy(float), hist[s].to_numpy(float), 1)[1])
            pred_naive = float(hist[s].iloc[-1])
            actual = float(df[s].iloc[j])
            rows.append({'target_week': int(t), 'actual': actual, 'naive_last': pred_naive,
                         'linear_trend': pred_trend})
        val[s] = rows
    metrics = {}
    for method in ['naive_last', 'linear_trend']:
        errs = [r[method]-r['actual'] for s in stations for r in val[s]]
        metrics[method] = {'MAE_units_per_week': float(np.mean(np.abs(errs))),
                           'RMSE_units_per_week': float(np.sqrt(np.mean(np.square(errs)))),
                           'n_station_origins': len(errs)}
    # Selected method is fixed in advance by interpretability and common forecast practice;
    # the comparison is tiny and not used to assert statistical superiority.
    forecasts = {}
    for s in stations:
        coef = np.polyfit(df.week.to_numpy(float), df[s].to_numpy(float), 1)
        forecasts[s] = max(0.0, float(np.polyval(coef, float(df.week.iloc[-1] + 1))))

    dist = problem['distribution']
    caps = dist['station_caps']; costs = dist['delivery_cost_per_unit']; penalties = dist['unmet_prediction_penalty_per_unit']
    for s in stations:
        for label, mapping in [('cap', caps), ('cost', costs), ('penalty', penalties)]:
            v = mapping[s]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v):
                raise ValueError(f'{label} for {s} must be finite numeric')
        if caps[s] < 0 or costs[s] < 0 or penalties[s] < 0:
            raise ValueError('caps/costs/penalties must be nonnegative')
    stock = dist['total_available_units']
    if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
        raise ValueError('total_available_units must be a nonnegative integer')
    if any(int(caps[s]) != caps[s] for s in stations):
        raise ValueError('station caps must be integer')
    # Variables: x_i integer delivered, u_i continuous shortage. Constraints:
    # u_i >= demand_i - x_i; x_i + u_i >= demand_i; total x <= stock.
    n=6; c=np.array([costs[s] for s in stations] + [penalties[s] for s in stations], float)
    integ=np.array([1,1,1,0,0,0], int)
    lb=np.zeros(n); ub=np.array([caps[s] for s in stations]+[np.inf]*3,float)
    mat=lil_matrix((4,n)); lo=np.full(4,-np.inf); hi=np.full(4,np.inf)
    for i,s in enumerate(stations): mat[i,i]=1; mat[i,3+i]=1; lo[i]=forecasts[s]
    for i in range(3): mat[3,i]=1
    hi[3]=stock
    res=milp(c, integrality=integ, bounds=Bounds(lb,ub), constraints=LinearConstraint(mat.tocsr(),lo,hi),
             options={'mip_rel_gap':0.0})
    if not res.success or res.x is None:
        raise RuntimeError(f'optimizer failed: {res.message}')
    alloc={s:int(round(res.x[i])) for i,s in enumerate(stations)}
    # Independent exhaustive integer oracle for this small bounded instance.
    best=None; best_x=None; feasible=0
    for a in range(int(caps['A'])+1):
      for b in range(int(caps['B'])+1):
       for cval in range(int(caps['C'])+1):
        if a+b+cval > stock: continue
        feasible+=1
        xs={'A':a,'B':b,'C':cval}
        obj=sum(costs[s]*xs[s]+penalties[s]*max(forecasts[s]-xs[s],0) for s in stations)
        if best is None or obj < best-1e-10: best,best_x=obj,xs
    objective=sum(costs[s]*alloc[s]+penalties[s]*max(forecasts[s]-alloc[s],0) for s in stations)
    if alloc != best_x or abs(objective-best)>1e-8:
        raise AssertionError('MILP result differs from independent enumeration')
    allocation={'units_week9':alloc,'total_units':sum(alloc.values()),
                'cap_slack':{s:int(caps[s]-alloc[s]) for s in stations},
                'stock_slack':int(stock-sum(alloc.values())),
                'shortage_units':{s:float(max(forecasts[s]-alloc[s],0)) for s in stations},
                'objective_CNY':float(objective), 'objective_recomputed_CNY':float(best),
                'enumerated_feasible_allocations':feasible,
                'optimality_evidence':'scipy.milp (zero requested relative gap) agrees with independent exhaustive enumeration of every feasible integer allocation'}
    # Actual figure from raw observations + computed forecast + allocation.
    fig,ax=plt.subplots(figsize=(8,4.6))
    for s in stations:
        ax.plot(df.week,df[s],marker='o',label=f'{s} observed')
        ax.scatter([9],[forecasts[s]],marker='x',s=75)
        ax.plot([8,9],[df[s].iloc[-1],forecasts[s]],linestyle='--',alpha=.7)
    ax.set(title='Weekly demand and week 9 linear-trend forecasts',xlabel='Week',ylabel='Demand (units/week)')
    ax.set_xticks(range(1,10)); ax.grid(alpha=.25); ax.legend(ncol=3,fontsize=8)
    fig.tight_layout()
    return {'case_id':problem['case_id'],'audit':audit,'validation':{'protocol':'rolling-origin one-step; at each origin train only on earlier weeks; origins 4–8','predictions':val,'metrics':metrics},
            'forecast_method':'per-station ordinary least squares linear trend on weeks 1–8, extrapolated one week; clipped at zero',
            'forecast_week9_units_per_week':forecasts,'allocation':allocation,'milp_status':res.message,
            'uncertainty':'No probabilistic intervals estimated; eight weeks are too little to establish calibrated uncertainty.'},fig


def main():
    p=argparse.ArgumentParser(); p.add_argument('problem',type=Path); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    try:
        problem=json.loads(a.problem.read_text(encoding='utf-8'))
        result,fig=solve(problem)
        a.out.mkdir(parents=True,exist_ok=True)
        result_path=a.out/'results.json'; result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        fig.savefig(a.out/'demand_forecast.png',dpi=170); plt.close(fig)
        print(json.dumps({'status':'ok','results':str(result_path),'figure':str(a.out/'demand_forecast.png'),'objective_CNY':result['allocation']['objective_CNY']}))
    except Exception as e:
        print(json.dumps({'status':'rejected','error':str(e)},ensure_ascii=False))
        raise SystemExit(2)
if __name__=='__main__': main()

