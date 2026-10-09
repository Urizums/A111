from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
ex=Path('runs/R22/execution');sys.path.insert(0,str(ex/'source/v1'))
from run_replay import matrix,metrics
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=ex/'science-v1';b=ex/'clean-v1';out=ex/'author-selfcheck-v1';out.mkdir(exist_ok=False)
frozen=json.loads((ex/'prospective-freeze.json').read_text('utf-8'))
for f in frozen['scientific_source_identities']+frozen['authorized_source_identities']:assert sha(Path(f['path']))==f['sha256']
first=json.loads((ex/'receipts/0007-first-science-v1.json').read_text('utf-8'));fr=json.loads((ex/'receipts/0006-freeze-science.json').read_text('utf-8'));assert fr['state']=='finished' and fr['exit_code']==0 and fr['end']['utc']<first['begin']['utc'];assert frozen['actual_frozen_at_utc']<first['begin']['utc']
comp=[]
for p in sorted(a.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(a);q=b/rel;assert q.exists()
    if p.suffix=='.csv':
        x=pd.read_csv(p);y=pd.read_csv(q);assert list(x)==list(y) and len(x)==len(y)
        ignore=['seconds','fit_predict_seconds'];cols=[c for c in x if c not in ignore]
        for c in cols:
            if pd.api.types.is_numeric_dtype(x[c]):assert np.allclose(x[c].to_numpy(float),y[c].to_numpy(float),rtol=0,atol=1e-9,equal_nan=True),(str(rel),c)
            else:assert x[c].fillna('<NA>').equals(y[c].fillna('<NA>')),(str(rel),c)
        comp.append({'path':str(rel),'kind':'csv','critical_columns':cols})
    elif p.suffix=='.npz':
        with np.load(p) as x,np.load(q) as y:
            assert set(x.files)==set(y.files)
            for key in x.files:assert np.array_equal(x[key],y[key]),(str(rel),key)
        comp.append({'path':str(rel),'kind':'exact_npz_arrays'})
    elif p.name not in ['run_identity.json','completion.json','boundaries.json']:
        assert sha(p)==sha(q),(str(rel),'bytes');comp.append({'path':str(rel),'kind':'exact_bytes'})
    else:
        x=json.loads(p.read_text());y=json.loads(q.read_text())
        if p.name=='boundaries.json':
            x['solver'].pop('seconds');y['solver'].pop('seconds');assert x==y
        elif p.name=='completion.json':x.pop('runtime_seconds');y.pop('runtime_seconds');assert x==y
        elif p.name=='run_identity.json':
            for c in ['raw_hashes','config_sha256','source_hashes']:assert x[c]==y[c]
        comp.append({'path':str(rel),'kind':'semantic_json_without_clock_and_output_path'})
# Refit original source ridge from raw-derived, byte-identical snapshots/features.
refits=[]
for p in sorted((a/'source_backtrace').glob('train_*.csv')):
    if p.name.startswith('train_features'):continue
    tag=p.stem[6:];tr=pd.read_csv(p);tf=pd.read_csv(a/f'source_backtrace/train_features_{tag}.csv');coef=np.array(json.loads(Path(f'runs/R21/execution/science-v1/models/coefficients_{tag}_shared_ridge10.json').read_text())['coefficients']);model=Ridge(alpha=10,fit_intercept=False,solver='cholesky');model.fit(matrix(tf,.3),tr.demand_units.to_numpy());diff=float(np.max(np.abs(coef-model.coef_)));assert diff<1e-8;refits.append({'origin':tag,'max_coefficient_difference':diff})
k=pd.read_csv(a/'results/keys.csv');s=pd.read_csv(a/'results/solver_daily.csv');assert len(k)==6*4032 and not k.duplicated(['origin','method_id','service_date','store_id','item_id']).any()
assert np.isfinite(k[['point','actual','lower90','upper90','q_units','shortage_yuan','waste_yuan','interval_score']]).all().all()
assert (k[['point','lower90','upper90','q_units']]>=0).all().all() and (k.lower90<=k.upper90).all()
assert (k.q_units==np.floor(k.q_units)).all() and (k.q_units<=55).all()
assert (s.q_units<=1600).all() and (s.procurement_yuan<=6000).all() and (s.status==0).all() and (s.gap<=1e-9).all()
assert np.max(np.abs(s.objective-s.objective_recomputed))<1e-6 and np.max(np.abs(s.objective-s.bound))<1e-6
for title in ['overall','stage','band','activity','activity_stage','activity_band','activity_horizon','store','item','horizon']:
    g=pd.read_csv(a/f'results/group_{title}.csv');empty=g[g.rows==0];assert (empty.days==0).all() and (empty.status=='not_estimable').all() and empty.mae.isna().all();assert g[g.rows>0].mae.notna().all()
result={'schema':'r22-author-selfcheck/1','independent':False,'source_identity':True,'freeze_before_first_fit':True,'clean_equivalent':True,'compared_artifacts':comp,'source_original_refits':refits,'solver_days':len(s),'max_objective_bound_difference':float(np.max(np.abs(s.objective-s.bound))),'point_outside_interval_count':int(((k.point<k.lower90)|(k.point>k.upper90)).sum()),'numeric_assertions':True,'empty_cell_assertions':True,'model':None,'tokens':None,'cost':None}
with (out/'selfcheck.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({c:v for c,v in result.items() if c!='compared_artifacts'},ensure_ascii=False,indent=2))
