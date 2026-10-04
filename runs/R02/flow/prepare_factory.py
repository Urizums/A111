"""Root-authored intake and frozen cases, through the original strict factory."""
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'skills/forge-agent-flow/scripts'))
import factoryctl as factory
out=root/'runs/R02/flow'
def save(name,obj): (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
request='Build a reusable library renewal agent flow. Renew for 14 days only when days_overdue=0, holds=0, renewals_used<2; otherwise staff review with explicit reasons. Preserve borrower_id and book_id. No external library actions. Strict shapes and stale-response rejection.'
criteria=[dict(id='policy',kind='machine',required=True,assertion='Exact decision, days, IDs and reasons match the explicit renewal policy.'),dict(id='protocol',kind='machine',required=True,assertion='Strict input/output shapes and stale response protection preserve the checkpoint.')]
choices={
'scope':'Reusable local renewal decision package; no account or library effects',
'inputs':'borrower_id, book_id strings; days_overdue, holds, renewals_used integers',
'outputs':'result object containing borrower_id, book_id, decision, renewal_days and reasons',
'quality':'Exact explicit policy and reasons; malformed envelopes rejected',
'tools_and_authority':'No external tools or requested filesystem writes by target node',
'failures':'Input shape errors rejected before start; stale/invalid response leaves state unchanged',
'state_and_handoffs':'One immutable input and one result in package checkpoint',
'budget_and_stop':'One target node/visit; at most two factory repairs',
'model_and_topology':'One actual host-default agent; one policy has no independent context boundary'}
contract=dict(goal=request,requirements=[dict(id='r_policy',text='Implement stated renewal policy with exact IDs and reasons',origin='explicit',basis='Renew for 14 days only when days_overdue=0, holds=0, renewals_used<2',criteria=['policy']),dict(id='r_protocol',text='Strict shapes and stale-response rejection',origin='explicit',basis='Strict shapes and stale-response rejection',criteria=['protocol'])],decisions={k:dict(choice=v,reason='Smallest complete local boundary for this explicit reusable flow',origin='derived') for k,v in choices.items()},blocking_questions=[])
cases=[]
for id,overdue,holds,used,reasons in [('eligible',0,0,0,[]),('hold',0,1,0,['reader_hold']),('overdue',3,0,0,['overdue']),('quota',0,0,2,['renewal_limit'])]:
 inputs=dict(borrower_id='B-'+id,book_id='BK-'+id,days_overdue=overdue,holds=holds,renewals_used=used)
 expected=dict(result=dict(borrower_id=inputs['borrower_id'],book_id=inputs['book_id'],decision='staff_review' if reasons else 'renew',renewal_days=0 if reasons else 14,reasons=reasons))
 cases.append(dict(id=id,inputs=inputs,expected=expected,expected_status='completed',criteria=['policy','protocol'],required=True))
plan=dict(schema='forge-eval/1',id='library_renewal',criteria=criteria,cases=cases,baseline='No reusable renewal package existed; policy read manually by the host.',limitations=['Four explicit policy branches, no real library/account effects.','One host agent; no performance comparison or provider recovery claim.'])
save('contract.json',contract);save('plan.json',plan)
s=factory.start(dict(request=request,environment=dict(host='Current Root agent',runtime='Python stdlib original factory/package controllers',external_effects=False)))
save('factory-start.json',s);d=factory.pending(s);save('intake-dispatch.json',d)
r=dict(invocation_id=d['invocation_id'],outcome='ok',artifacts=dict(contract=contract),evidence=['Root-authored contract from runs/R02/materials/flow-brief.json'])
save('intake-response.json',r);s=factory.advance(s,r);s=factory.freeze_plan(s,plan,source='runs/R02/flow/plan.json');save('factory-frozen.json',s);save('architect-dispatch.json',factory.pending(s))
print(json.dumps({'stage':factory.pending(s)['node'],'plan_cases':len(cases)}))
