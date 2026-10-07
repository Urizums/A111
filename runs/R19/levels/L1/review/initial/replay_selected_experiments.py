"""Scope-adapted experiment function replay; copied source files unchanged.
Overrides ROOT output and selects five declared scenarios. Not a full CLI replay.
"""
from independent_audit import OUT,EXEC,raw_config
import sys,json,shutil
sys.path.insert(0,str(OUT/'sandbox/runs/R19/levels/L1/execution/src'))
import experiments
dest=OUT/'experiment-rerun'
if dest.exists():raise RuntimeError('Output must be new')
(dest/'configs').mkdir(parents=True);(dest/'results/final').mkdir(parents=True)
cfg=raw_config();(dest/'configs/base.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
for n in ['fixed_T1.json','fixed_T2.json','pattern_pool.json']:shutil.copy2(EXEC/'results/final'/n,dest/'results/final'/n)
selected=['base','T1_cost_300','bearing_250','cargo_height_-5','directional_union_resultant']
original_cases=experiments.scenarios
experiments.scenarios=lambda cfg:[r for r in original_cases(cfg) if r[0] in selected]
experiments.ROOT=dest
(OUT/'experiment-replay-adaptation.json').write_text(json.dumps({'source_files_changed':False,'runtime_adaptations':['experiments.ROOT redirected to initial/experiment-rerun','scenarios filtered to five predeclared cases'],'selection_reasons':{'base':'current conditions','T1_cost_300':'count/cost objective separation','bearing_250':'cumulative load boundary','cargo_height_-5':'actual dimensions change and generic fallback','directional_union_resultant':'material original-rule ambiguity'},'original_cfg_source':'own original DOCX parser','original_pool':'frozen pool independently audited, reused for pure-cost scenarios','per_master_limit_seconds':5,'scenario_window_seconds':240,'claim_limit':'five scoped original experiment paths, not all32 CLI or performance comparison'},ensure_ascii=False,indent=2),encoding='utf-8')
experiments.experiment_all(240,False)
