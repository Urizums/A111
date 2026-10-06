import json
from pathlib import Path
from itertools import product

OUT = Path(__file__).parent
weeks = list(range(1, 9))
history = {
    'A': [20,21,22,23,24,25,26,27],
    'B': [16,15,17,18,17,19,20,19],
    'C': [23,25,24,27,26,28,30,29],
}
cost = {'A':2,'B':1,'C':3}
penalty = {'A':8,'B':6,'C':10}
caps = {'A':30,'B':25,'C':35}
stock = 60

def trend_predict(y, x_train, x_target):
    n=len(y); xb=sum(x_train)/n; yb=sum(y)/n
    slope=sum((x-xb)*(v-yb) for x,v in zip(x_train,y))/sum((x-xb)**2 for x in x_train)
    return yb+slope*(x_target-xb)

pred={s:trend_predict(y,weeks,9) for s,y in history.items()}
validation={}
for s,y in history.items():
    errors=[]; naive=[]
    for t in range(1,7): # forecast week index t using weeks 1..t, no future
        x=weeks[:t+1]; vals=y[:t+1]
        errors.append(abs(trend_predict(vals,x,weeks[t+1])-y[t+1]))
        naive.append(abs(y[t]-y[t+1]))
    validation[s]={'rolling_origins_weeks_3_to_8':len(errors),'trend_MAE':sum(errors)/len(errors),'last_value_MAE':sum(naive)/len(naive),'trend_abs_errors':errors,'last_value_abs_errors':naive}

# Enumerate all feasible integer allocations; objective exactly as stated.
# Predictions are unrounded for forecast display; shortage hinges on integer x.
keys=['A','B','C']
def obj(xs):
    return sum(cost[s]*x + penalty[s]*max(pred[s]-x,0) for s,x in zip(keys,xs))
feasible=[]
for xs in product(*(range(caps[s]+1) for s in keys)):
    if sum(xs)<=stock:
        feasible.append((obj(xs),xs))
best=min(v for v,_ in feasible)
opts=[xs for v,xs in feasible if abs(v-best)<1e-10]
# also integer-rounded forecast as a separate diagnostic
pred_round={s:round(pred[s]) for s in keys}
def obj_round(xs):
    return sum(cost[s]*x + penalty[s]*max(pred_round[s]-x,0) for s,x in zip(keys,xs))
feasible_round=[(obj_round(xs),xs) for xs in product(*(range(caps[s]+1) for s in keys)) if sum(xs)<=stock]
best_round=min(v for v,_ in feasible_round)
opts_round=[xs for v,xs in feasible_round if v==best_round]
result={
    'method':'ordinary least squares linear trend, separately per station; rolling-origin one-step absolute error for origins 3..8; direct integer enumeration of stated objective',
    'prediction_units_per_week':pred,
    'prediction_rounded_nearest_integer':pred_round,
    'validation':validation,
    'allocation_continuous_prediction':{'best_objective_CNY':best,'number_of_optima':len(opts),'solutions':opts[:12],'feasible_allocations_enumerated':len(feasible)},
    'allocation_rounded_prediction':{'best_objective_CNY':best_round,'number_of_optima':len(opts_round),'solutions':opts_round[:12]},
    'constraints':{'integer_nonnegative_caps_stock':True,'stock_used_each_reported_solution':{str(x):sum(x) for x in opts[:12]}}
}
(OUT/'independent-calculations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))

