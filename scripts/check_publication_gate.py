"""Fail closed before dev publication. This checks evidence integrity, not semantic truth."""
import argparse,hashlib,json
from pathlib import Path
from delivery import read_file

REQUIRED_TASKS={
 'BACKLOG-preset_browser_acceptance','BACKLOG-versioned_preset_catalog',
 'BACKLOG-real_agent_executor_integration','BACKLOG-real_worker_failure_recovery_trials',
 'BACKLOG-bridge_budget_timeout_validation','BACKLOG-host_protocol_overhead_comparison',
 'CAP-sdk_adapter_contract','X01-concurrent_ticket_edits','R06-feedback_snapshot',
 'R06-feedback_budget','R06-fresh_context_validation','R06-scheduled_handoff'}
REQUIRED_CHECKS={'independent_final_ui','original_regressions','candidate_regressions',
 'installed_smoke','archive_smoke','new_defects_retested','repair_budget_audit'}

def check(root,destination='waw1w1/A111:dev'):
    errors=[]
    def load(path):return json.loads(read_file(root,path))
    def verify_ref(ref):
        data=read_file(root,ref['path'])
        if hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('Evidence hash changed: '+ref['path'])
        return data
    try:
        gate=load('state/publication-gate.json');state=load('state/continuation.json')
        if gate.get('schema')!='forge-publication-gate/1':errors.append('Unknown gate schema')
        if gate.get('destination')!=destination:errors.append('Destination differs from authorized gate')
        declared=set(gate.get('required_open_tasks',[]))|set(gate.get('new_review_required_tasks',[]))
        if not REQUIRED_TASKS<=declared:errors.append('Required scope was removed or missing')
        tasks={t['id']:t for t in state['tasks']}
        if len(tasks)!=len(state['tasks']):errors.append('Duplicate task identities')
        for name in sorted(REQUIRED_TASKS|declared):
            t=tasks.get(name)
            if not t or t.get('status')!='done':errors.append(name+': '+str(t.get('status') if t else 'missing'));continue
            if t.get('blocker') or t.get('repairs_used',0)>t.get('repair_limit',2):errors.append(name+': unresolved blocker or exceeded budget')
            if not t.get('evidence'):errors.append(name+': missing acceptance evidence')
            for ref in t.get('evidence',[]):verify_ref(ref)
        candidate=gate.get('candidate')
        if not candidate or not candidate.get('files'):errors.append('Final candidate identity is missing');candidate_hash=None
        else:
            paths=[x['path'] for x in candidate['files']]
            if len(set(paths))!=len(paths):errors.append('Duplicate final candidate paths')
            for ref in candidate['files']:verify_ref(ref)
            candidate_hash=hashlib.sha256(json.dumps(candidate['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if candidate.get('sha256')!=candidate_hash:errors.append('Final candidate manifest hash mismatch')
        checks=gate.get('checks',{})
        for name in sorted(REQUIRED_CHECKS):
            row=checks.get(name,{})
            if row.get('status')!='pass':errors.append(name+': '+str(row.get('status','not_run')));continue
            if not candidate_hash or row.get('candidate_sha256')!=candidate_hash:errors.append(name+': stale or unbound candidate')
            if not row.get('evidence'):errors.append(name+': missing evidence')
            for ref in row.get('evidence',[]):verify_ref(ref)
        for finding in gate.get('findings',[]):
            if finding.get('required',True) and finding.get('status')!='fixed_and_retested':errors.append('Open required finding: '+finding.get('id','unknown'))
        if gate.get('unreconciled_native'):errors.append('Native calls remain unreconciled')
    except (ValueError,OSError,KeyError,TypeError) as exc:errors.append(str(exc))
    return {'schema':'forge-publication-check/1','destination':destination,'publishing_allowed':not errors,'errors':errors,
            'limits':'Local fail-closed evidence check; Root must review semantics and current remote head. No GitHub branch-protection or authenticated provider guarantee.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--destination',default='waw1w1/A111:dev');p.add_argument('--out',type=Path);a=p.parse_args();result=check(a.root,a.destination);raw=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with a.out.open('x') as f:f.write(raw)
    print(raw,end='');return 0 if result['publishing_allowed'] else 2

if __name__=='__main__':raise SystemExit(main())
