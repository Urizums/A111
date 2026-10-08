import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE='runs/R19/final/forward/review/'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def entry(p):return dict(path=p.relative_to(ROOT).as_posix(),size_bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(name,obj):(HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
identities=[]
for relative in ['runs/R19/final/candidate/C12-lock.json','runs/R19/final/forward/inputs/input-lock.json',
    'runs/R19/final/forward/evaluation-lock.json','runs/R19/final/forward/review-preparation-lock.json',
    'runs/R19/final/forward/production-lock.json',BASE+'method-lock.json']:
    lp=ROOT/relative
    checks=[]
    for expected in load(lp)['files']:
        actual=entry(ROOT/expected['path'])
        checks.append(dict(expected=expected,actual=actual,matches=actual==expected))
    identities.append(dict(lock=entry(lp),all_match=all(c['matches'] for c in checks),files=checks))
save('final-identity-check.json',dict(all_match=all(x['all_match'] for x in identities),locks=identities,
    scope='After all actual execution/review: locked source, production and precommitted receiver method unchanged'))
wf=load(HERE/'workflow-receipts.json');ind=load(HERE/'independent-recomputation.json')
pairs=load(HERE/'paired-receiving-observations.json');paper=load(HERE/'paper-review.json');failures=load(HERE/'input-failure-observations.json')
assert all(x['all_match'] for x in identities)
assert wf['all_four_completed'] and wf['all_started_commands_terminal']
assert all(x['valid'] for x in ind['new_and_original'].values()) and ind['solution_semantic_match']
assert all(x['independent_recompute']['valid'] and x['objective_matches_independent_oracle'] for x in ind['variants'])
assert pairs['all_agree'] and pairs['all_started_processes_terminal'] and pairs['false_acceptances']==pairs['false_rejections']==0
assert failures['all_reject_as_expected'] and failures['all_started_processes_terminal']
assert paper['all_pages_actually_viewed'] and paper['all_numeric_tables_agree'] and not paper['missing_source_lines']
mandatory=[
 dict(id='b1',verdict='pass',sources=['runs/R19/final/forward/inputs/problem.md','runs/R19/final/forward/inputs/raw.json'],
      source_clause='All original items, identities, fixed orientation, no overlap/boundary/clearance/payload violation; complete single support; recursively transmitted cumulative external load; minimum trucks then minimum cost',
      evidence=[BASE+'independent-recomputation.json',BASE+'consumer-solution.json',BASE+'workflow-receipts.json'],
      observation='Own raw-source checks confirm complete feasible actual one-truck solution and recomputed cost; independent nonempty bound closes original optimum',
      limits='Original four-unit-cube instance only; not arbitrary near-boundary numeric, geometric or physical correctness'),
 dict(id='b2',verdict='pass',sources=['runs/R19/final/forward/acceptance.json','runs/R19/final/forward/production/workflow.md'],
      source_clause='Selected smoke assertions require activated real end-to-end conditions and actual reception; remaining constraints stay in full acceptance',
      evidence=[BASE+'smoke-activation.json',BASE+'workflow-receipts.json',BASE+'paired-receiving-observations.json',BASE+'paper-review.json'],
      observation='Actual raw run has stacked supports and fragile-on-standard; actual three-level counterexample transmits two levels and is rejected for recursive overload by actual frozen receiver; paper result values traced',
      limits='Selected actual workflow assertions on this source only; all uncovered assertions addressed in other mandatory checks'),
 dict(id='b3',verdict='pass',sources=['runs/R19/final/forward/inputs/problem.md','runs/R19/final/forward/acceptance.json'],
      source_clause='Output labels cannot change original identity; finite relevant value domains must be checked before physical/objective comparisons and aggregates; valid/invalid actual receiver pairing',
      evidence=[BASE+'paired-receiving-observations.json',BASE+'input-failure-observations.json'],
      observation='23 actual CLI paired receiver cases agree with own source logic; identity laundering, wrong support, nonfinite axes/objectives/metadata rejected; four declared input failure routes reject without fake solution',
      limits='Bounded paired cases, not exhaustive receiver reliability or universal false acceptance/rejection rates'),
 dict(id='b4',verdict='pass',sources=['runs/R19/final/forward/inputs/request.md','runs/R19/final/forward/inputs/problem.md','runs/R19/final/forward/acceptance.json'],
      source_clause='Complete Chinese scientific argument and final PDF/editable source; numbers, units, formulas, assumptions and claim strength agree; no page quota',
      evidence=[BASE+'paper-review.json',BASE+'pdf-text.txt',BASE+'independent-recomputation.json',BASE+'pdf-pages/page-1.png',BASE+'pdf-pages/page-8.png'],
      observation='Full Markdown and eight freshly rendered PDF pages actually read; coordinate/load/eight-variant tables independently recomputed; all 131 effective source lines present after exact header/footer normalization; complete bounded argument',
      limits='Final frozen eight-page PDF/editable source and inspected scientific meaning; no style/page/model gate or external contest/safety claim'),
 dict(id='b5',verdict='pass',sources=['runs/R19/final/forward/inputs/request.md','runs/R19/final/forward/inputs/problem.md','runs/R19/final/forward/acceptance.json'],
      source_clause='Transferred usable workflow and runnable program from original raw; fresh independent consumer performs feasibility/objective/paper-value recomputation; author self-check alone insufficient',
      evidence=[BASE+'method-lock.json',BASE+'workflow-receipts.json',BASE+'independent-recomputation.json',BASE+'paper-review.json'],
      observation='Fresh acceptor executes four actual workflow commands from original input in independent output domain, binds source identities and uses own physical/objective logic plus instance-specific oracle and full document reading',
      limits='New material vertical slice/two contexts only; no original three-role/four-level performance replication or causal candidate ranking')]
payload=[entry(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ('result.json','manifest.json')]
result=dict(schema='C12-forward-independent-reception/1',candidate='C12',state='complete_stopped',
    frozen_at=datetime.now(timezone.utc).isoformat(),first_verdict=True,overall='pass_for_frozen_b1_b5',
    mandatory=mandatory,production_modified=False,method_identity_preserved=True,all_source_locks_match=True,
    actual_scope='Fresh independent source-bound reception of frozen new four-item task and transferred workflow',
    telemetry=dict(provider=None,model=None,tokens=None,cost=None),
    actual_checks=dict(workflow_commands=4,valid_invalid_receiver_cases=len(pairs['cases']),
        receiver_false_acceptances=pairs['false_acceptances'],receiver_false_rejections=pairs['false_rejections'],
        input_failure_routes=len(failures['cases']),parameter_variants_with_own_oracle=len(ind['variants']),
        full_pdf_pages_rendered_and_actually_viewed=paper['pdf_pages'],effective_source_lines_matched=len(paper['source_line_coverage'])),
    terminal_state='Every started synchronous workflow/receiving/input-failure/render process has a terminal receipt; no unfinished sessions or background processes',
    failed_requirement_evidence=[],report=BASE+'report.md',payload=payload,
    unverified_outside_scope=['Arbitrary instances/near-boundary floats and all potential receiver defects',
        'Industrial/road/axle/vibration/loading-channel empirical safety',
        'Causal C11/C12 superiority, new levels, prize/contest/October performance'],
    next_action='Stop all writes and deliver first independent verdict to root; no producer repair or altered gate')
save('result.json',result)
save('manifest.json',dict(schema='C12-forward-independent-reception-manifest/1',
    files=[entry(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='manifest.json']))
print(json.dumps(dict(state=result['state'],overall=result['overall'],mandatory=[(b['id'],b['verdict']) for b in mandatory],
    production_files_still_match=len(identities[4]['files']),payload_files=len(payload),manifest_files=len(load(HERE/'manifest.json')['files'])),ensure_ascii=False))
