"""Preserve failed validation, unblock only the distinct host-diagnostic branch."""
import json
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from coordinate import read,write,result

def main():
    evidence=['runs/R08/validation/simple/result.json','runs/R08/validation/simple/results/reconciliation.json','runs/R08/validation/complex-terminal.json','runs/R08/validation/frozen-lock.json','runs/R08/validation/native-create-returns.json','runs/R08/validation/root-repair-ledger.json']
    write('runs/R08/R08-03-result.json',result('R08-03',evidence,[
        'Fresh Luna/max simple executor produced correct reconciliation; source/output check passed',
        'Simple first business artifact elapsed 195.193523698 seconds from first capture begin; includes tools and failures',
        'Fresh Luna/max complex executor performed setup but produced no business artifact or independent reviewer',
        'Complex reported three corrections against limit two and read two C7 assets outside its assigned scope; execution stopped',
        'No complex successor business step; original R07 failure remains unchanged'
    ],['R08-03 acceptance failed; no candidate performance or generalization conclusion','No authenticated provider timing or cost; write scopes are instruction-level','First-command captures and frozen raw bytes retained; complete original bridge/snapshot predispatch protocol was not exercised'],metrics={'simple_first_artifact_seconds':195.193523698,'complex_first_artifact_seconds':None,'candidate_repairs':0,'simple_actor_repairs':2,'complex_actor_repairs':3,'complex_actor_limit':2,'tokens':None,'cost':None},status='fail'))
    s=read('state/continuation.json')
    t=next(t for t in s['tasks'] if t['id']=='R09-01');assert t['status']=='planned' and not t['attempts']
    before=t['depends_on'];t['depends_on']=[];t['inputs'].append('runs/R09/PLAN_ADDENDUM.md')
    s['events'].append(dict(at=datetime.now(timezone.utc).isoformat(),command='continue_distinct_unblocked_host_diagnostics',result=dict(task='R09-01',old_depends_on=before,new_depends_on=[],basis='runs/R09/PLAN_ADDENDUM.md',acceptance_changed=False,old_budgets_changed=False,R08_transition_may_advance=False)))
    s['execution'].update(current_coordinator='root-codex-r08-desktop',session_state='active_bounded_branch_work',current_report='runs/R08/REPORT.md',latest_capability_probe='runs/R09/preflight/wsl-probe.json',current_native_pending=[],native_pending=[],current_native_completed=[dict(worker='/root/r08_simple',outcome='business_passed',evidence='runs/R08/validation/simple/result.json'),dict(worker='/root/r08_complex',outcome='failed_budget_exceeded',evidence='runs/R08/validation/complex-terminal.json')],background_code_execution_verified=False,monitor_enabled=False)
    write('state/continuation.json',s)
    budget=read('runs/R08/validation/root-repair-ledger.json')
    budget['complex_executor']=dict(used=3,limit=2,exceeded=True,further_repairs_allowed=False,evidence='runs/R08/validation/complex-terminal.json')
    write('runs/R08/validation/root-repair-ledger.json',budget)
    phase=read('state/phase-todo.json');last=phase['tasks'][-1]
    last.update(status='blocked',blocker='R08-03 complex case failed and exceeded frozen two-repair limit; phase acceptance is incomplete.',evidence=['runs/R08/validation/complex-terminal.json','runs/R09/PLAN_ADDENDUM.md'],next_action='Retain R08 gate; continue independent R09-01 host diagnostics without archiving R08.')
    write('state/phase-todo.json',phase)
    cp=read('state/checkpoint.json')
    cp.update(current_validation='R08: C7 authoring and inherited376 passed; simple fresh task passed; complex incomplete with three corrections beyond limit2; R08-03 blocked. R07 and full product gate unchanged.',R08_validation_budget='runs/R08/validation/root-repair-ledger.json',R09_branch='runs/R09/PLAN_ADDENDUM.md')
    write('state/checkpoint.json',cp)

if __name__=='__main__':main()
