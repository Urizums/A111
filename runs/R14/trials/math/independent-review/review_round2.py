import json
from pathlib import Path
base=Path('runs/R14/trials/math/independent-review')
review=json.loads((base/'review.json').read_text(encoding='utf-8'))
figure_names={1:'demand_forecast.png',2:'demand_allocation.png',3:'forecast_allocation.png',4:'forecast_allocation.png',5:'forecast_allocation.png',6:'demand_forecast.png',7:'demand_forecast.png',8:'forecast_allocation.png'}
solver_names={1:'solver.py',2:'solver.py',3:'solve.py',4:'solve.py',5:'solve.py',6:'solve.py',7:'solve.py',8:'solve.py'}
receipt_names={1:['attempt-1-main.json','attempt-1-check.json'],2:['receipt-source-check.json','receipt-smoke.json','receipt-malformed.json','receipt-verification.json'],3:['receipts/source-check-final.json','receipts/final-main-smoke.json','receipts/final-malformed-rejection.json'],4:['receipts/main-smoke.json','receipts/malformed-smoke.json'],5:['receipt-main.json','receipt-malformed.json','receipt-main-correction-1.json'],6:['smoke-valid-command.json','smoke-malformed-command.json'],7:['main-smoke.json','main-rerun-01.json','main-rerun-02.json','malformed-smoke.json','malformed-rerun-02.json'],8:['reproduction/command.json','boundary-check/command.json']}
locators={}
for i in range(1,9):
 root=Path(f'runs/R14/trials/math/L{i}')
 names=[solver_names[i],'results.json','workflow.md','paper.md','verification.md',figure_names[i],*receipt_names[i]]
 locators[f'L{i}']={str(root/n).replace('\\','/'): (root/n).is_file() for n in names}
# Read only authorized underlying L3 records and request/lock to reconcile the budget.
req=json.loads(Path('runs/R14/cases/math/L3/request.json').read_text(encoding='utf-8'))
r3=json.loads(Path('runs/R14/trials/math/L3/result.json').read_text(encoding='utf-8'))
lock=json.loads(Path('runs/R14/candidate/C9-lock.json').read_text(encoding='utf-8'))
assert req['repair_limit']==2 and r3['budget']['trial_level3']['limit']==2
assert lock['repairs_used']==2 and lock['candidate_source_repairs']==0 and lock['author_orchestration_corrections']==2
l3_budget={
 'case_limit':req['repair_limit'],
 'producer_reported_trial_corrections':r3['budget']['trial_level3']['corrections_used'],
 'case_level_events':[
  {'event':'Initial exploratory file reads omitted required runs/R14 prefix; three lookups failed.','classification':'one orchestration correction when path was corrected; three failed lookups are one grouped root-cause event, not three corrections','evidence':'runs/R14/trials/math/L3/result.json budget.failed_attempts[0]','raw_command_receipt':'none found among L3 retained receipts; event/count are recorded in result.json and verification.md, so raw invocation detail is unverified','producer_budget_field':'correction_budget_count=0','independent_count':1},
  {'event':'Hash the actual --input bytes in reusable solver invocations.','classification':'one source/construction correction','evidence':'runs/R14/trials/math/L3/result.json budget.corrections[0] and current solve.py/source-check behavior','producer_budget_field':'included among two corrections','independent_count':1},
  {'event':'Remove duplicated hardcoded L3 correction count from source-check output.','classification':'one source/check construction correction','evidence':'runs/R14/trials/math/L3/result.json budget.corrections[1] and current source_check.py/source_check.json','producer_budget_field':'included among two corrections','independent_count':1}
 ],
 'independent_case_cumulative_count':3,
 'case_budget_result':'3/2; limit exceeded by one when source/construction and orchestration correction categories are cumulatively counted',
 'candidate_lock_domain':{'repairs_used':lock['repairs_used'],'repair_limit':lock['repair_limit'],'source_repairs':lock['candidate_source_repairs'],'orchestration_corrections':lock['author_orchestration_corrections'],'classification':'separate frozen C9 candidate history; 2/2 and not reset by this case'},
 'lineage_event_total_across_separate_domains':5,
 'lineage_total_caveat':'Arithmetic total across candidate history (2) plus L3 case (3) is 5 events, but the lock and case request define separate denominators; report both rather than silently treating them as one 2-round case budget.',
 'confidence_limit':'Two source corrections and the path correction are recorded in the trial result/verification, but no raw receipt for the three failed path lookups was found. The correction count is the best-supported cumulative reading of the retained event ledger; exact command-level details for the lookup failure remain unknown.'
}
addendum={
 'schema':'r14-independent-math-review-addendum/1',
 'review_stage':'Second review after coordinator requirement and locator feedback; initial blind review remains unchanged in review.json/review.md.',
 'scope':'Re-audit L3 cumulative budget and m5; validate/repair evidence locators for all initial per-requirement source fields. No other root diagnostics, author addenda or new reconciliations were read.',
 'initial_artifacts_preserved':['runs/R14/trials/math/independent-review/review.json','runs/R14/trials/math/independent-review/review.md'],
 'locator_audit':{'checked_against_filesystem':True,'per_level_exact_paths':locators,'observed_locator_error':'The initial review used {root}solve.py generically for m2/m3, which does not exist for L1 and L2; both producer files are solver.py. The initial m4/m5 fields used generic artifact labels rather than exact per-level file paths.','corrected_path_map':{f'L{i}':{'solver':f'runs/R14/trials/math/L{i}/{solver_names[i]}','results':f'runs/R14/trials/math/L{i}/results.json','workflow':f'runs/R14/trials/math/L{i}/workflow.md','paper':f'runs/R14/trials/math/L{i}/paper.md','figure':f'runs/R14/trials/math/L{i}/{figure_names[i]}','verification':f'runs/R14/trials/math/L{i}/verification.md','receipts':[f'runs/R14/trials/math/L{i}/{p}' for p in receipt_names[i]]} for i in range(1,9)},'all_listed_corrected_paths_exist':all(all(v.values()) for v in locators.values())},
 'L3_budget_reconciliation':l3_budget,
 'verdict_changes':{'L3_m5':{'initial':'pass','addendum':'fail','reason':'The initial m5 pass accepted the producer summary’s trial counter (2/2) without accumulating the separately recorded failed-path recovery with the two source/construction corrections. Under C9’s cumulative source/orchestration/construction/fallback counting rule, L3 is 3/2. The trial budget is therefore not truthfully reconciled; m5 also requires failures/budget preserved.','evidence':'runs/R14/cases/math/L3/request.json repair_limit=2; runs/R14/candidate/C9-lock.json candidate domain=2/2; runs/R14/trials/math/L3/result.json budget.failed_attempts[0] plus budget.corrections[0:2]; retained L3 source-check/main/malformed receipts confirm actual required checks ran, but do not evidence the initial failed reads.'},'other_original_verdicts':'No change to the original m1-m4 verdicts or other levels. In particular L7 m3 remains fail.'},
 'revised_counts':{'original_review':{'pass':39,'fail':1,'unverified':0},'after_addendum':{'pass':38,'fail':2,'unverified':0},'basis':'Only L3 m5 changes from pass to fail; L7 m3 was already failed.'},
 'reviewer_budget':{'round1':'Independent calculation index bug corrected; 1/2 reviewer corrections used.','round2':'This addendum repairs source locators and cumulative budget accounting; 2/2 reviewer corrections used.','remaining':0,'instruction':'No third review/correction round will be performed. No locked producer artifact was edited.'},
 'limitations':['The initial relative-path failure has no raw command receipt; its occurrence is recorded by the trial in result.json/verification.md. Count one grouped orchestration correction, while keeping command details unverified.','C9 candidate history (2/2) and L3 trial request (limit 2) are separate stated budget domains. Their lineage event total is reported as 5, while the L3 case itself is 3/2.','Authenticated model, tokens and cost remain unknown/null.'],
 'global_boundary':'The review remains limited to the eight mathematical artifacts and shared detailed acceptance contract. Fold schemes differ by level. It does not infer level causality/ranking or any contest outcome.'
}
(base/'round2-locator-audit.json').write_text(json.dumps({'schema':'r14-round2-locator-audit/1','locators':locators,'all_files_exist':all(all(v.values()) for v in locators.values())},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(base/'addendum.json').write_text(json.dumps(addendum,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md='''# Independent review addendum — round 2

This is the second review after coordinator requirement and locator feedback. The initial blind review remains unchanged in `review.json` and `review.md`. This addendum used only the original L3 request, the C9 lock/skill accounting rule, the L3 original result/receipts, and actual L1–L8 trial files for locator validation. No root diagnostic or later author reconciliation was used.

## Revised finding

**L3 m5 changes from pass to fail.** L3’s request sets a two-correction limit. Its result records two source/construction corrections and separately records an earlier orchestration failure: initial reads used the wrong relative prefix, three lookups failed, then the paths were corrected. Under C9’s rule to accumulate source, orchestration, construction and fallback corrections, that recovery is one additional correction. The L3 case count is therefore **3/2**, not 2/2. The three failed lookups share one cause and count as one correction event.

The C9 candidate lock separately records 0 source repairs + 2 orchestration corrections = **2/2** in its own frozen history. The combined lineage event total is 5 (C9 history 2 plus L3 case 3), but the lock and L3 request define separate budget domains; the L3 case alone already exceeds its own limit. The producer’s `correction_budget_count: 0` for the failed-path event is inconsistent with cumulative correction accounting. L3’s source-check, main-smoke and malformed-input receipts are real and retained; they do not erase the budget overrun.

The lookup failure appears in L3 `result.json` and `verification.md`, but no raw command receipt for those failed reads was found. Thus the event is recorded and countable under the cumulative rule, while its exact command-level details remain unverified.

## Locator correction

The initial review used a generic `solve.py` source path for every level in m2/m3. The actual L1 and L2 producer source is `solver.py`; L3–L8 use `solve.py`. The initial m4/m5 entries also named artifact classes without exact filenames. The filesystem locator audit is in `round2-locator-audit.json`; all corrected source, results, workflow, paper, figure, verification and receipt paths listed there exist. These locator fixes do not change the other substantive m1–m4 findings.

## Status and budget

The overall review now has **38 pass, 2 fail, 0 unverified** across the 40 checks. L7 m3 remains the original failure; L3 m5 is the new failure. The reviewer used its second and final correction round: round 1 corrected the independent calculation script’s indexing error; round 2 corrected evidence locators and cumulative budget accounting. Reviewer budget is **2/2**. No third review round will be performed, and no locked producer artifact was changed.

Findings remain bounded to these eight math artifacts and the shared detailed contract. Per-level validation folds differ. No level-causality/ranking or competition outcome follows; model identity, token use and cost remain unknown/null.
'''
(base/'addendum.md').write_text(md,encoding='utf-8')
print(json.dumps({'locator_paths_exist':all(all(v.values()) for v in locators.values()),'l3_trial_cumulative':3,'new_counts':addendum['revised_counts']['after_addendum'],'reviewer_budget':addendum['reviewer_budget']},ensure_ascii=False))
