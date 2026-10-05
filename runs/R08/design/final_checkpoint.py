"""Finalize shared status under a real short-lived coordinator file lock."""
import fcntl
import json
import os
from pathlib import Path
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from coordinate import read,write
def now():return datetime.now(timezone.utc).isoformat()

def main():
    previous=read('state/coordinator-lease.json')
    write('runs/R08/design/lease-release.json',previous)
    with (ROOT/'state/coordinator.lock').open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        lease=dict(owner='root-codex-r08-final-checkpoint',pid=os.getpid(),acquired_at=now(),scope='single checkout advisory file lock, not distributed host isolation')
        write('state/coordinator-lease.json',lease)
        s=read('state/continuation.json');cp=read('state/checkpoint.json')
        s['execution'].update(session_state='checkpoint_for_published_main',R08_final_validation='runs/R08/design/auxiliary-stable.json',R08_repair_ledger='runs/R08/validation/root-repair-ledger-2.json',coordinator_heartbeat=now(),checkpoint_reason='C7 implemented; R08 complex blocked with budget overrun retained; distinct R09-01 completed; R09-02 fresh checkout verification remains next. No pending current native worker or background code claim.',coordinator_release_evidence='runs/R08/design/lease-release.json')
        s['events'].append(dict(at=now(),command='final_checkpoint_for_main',result=dict(R08_phase_passed=False,R09_01_actual_done=True,next_task_id='R09-02',current_native_pending=[],old_budgets_unchanged=True)))
        cp.update(updated_at=now(),execution=s['execution'],termination='Scoped development and evidence committed for main; R08 phase remains blocked, next queue R09-02; current native calls terminal, timer disabled.',R08_final_regressions=dict(inherited=376,auxiliary_stable=53,windows_preflight=6,wsl_preflight=6,semantic_R08_03='failed_complex_budget_overrun'),R08_latest_repair_ledger='runs/R08/validation/root-repair-ledger-2.json')
        write('state/continuation.json',s);write('state/checkpoint.json',cp)
        lease['released_at']=now();write('state/coordinator-lease.json',lease)
        write('runs/R08/design/final-checkpoint-lease.json',lease)
    print(json.dumps(dict(checkpoint_saved=True,lease_released=True,next_task='R09-02',R08_advance=False)))

if __name__=='__main__':main()
