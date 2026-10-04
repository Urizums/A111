"""Execute actual host responses; machine checks and protocol rejection probes."""
import copy,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'skills/forge-agent-flow/scripts'))
import factoryctl,flowctl,packagectl
out=Path(__file__).parent
load=lambda p:json.loads(p.read_text())
def save(n,v): (out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
p=load(root/'challenges/renewal-flow/package.json');plan=p['acceptance']['plan'];responses=load(out/'host-responses.json')['responses'];rows=[];checks=[]
for case in plan['cases']:
 name=case['id'];s=load(out/(name+'-state-start.json'));r=responses[name];before=copy.deepcopy(s)
 bad=copy.deepcopy(r);bad['invocation_id']='stale-reply'
 try:packagectl.advance(p,s,bad)
 except flowctl.FlowError as e:save(name+'-stale-rejection.json',dict(error=str(e),unchanged=s==before))
 else:raise AssertionError('Stale reply accepted')
 assert s==before
 bad=copy.deepcopy(r);bad['artifacts']['result']['unexpected']=True
 try:packagectl.advance(p,s,bad)
 except flowctl.FlowError as e:save(name+'-shape-rejection.json',dict(error=str(e),unchanged=s==before))
 else:raise AssertionError('Extra field accepted')
 assert s==before
 malformed=copy.deepcopy(case['inputs']);malformed['holds']='one'
 try:packagectl.start(p,malformed)
 except flowctl.FlowError as e:save(name+'-input-rejection.json',dict(error=str(e)))
 else:raise AssertionError('Wrong input type accepted')
 end=packagectl.advance(p,s,r);save(name+'-state-final.json',end)
 actual=end['flow_state']['artifacts']['result']
 assert actual==case['expected']['result'],(actual,case['expected'])
 assert packagectl.pending(p,end)['status']=='completed'
 rows.append(dict(case_id=name,run=end,checks=[dict(id=c['id'],kind=c['kind'],status='pass',evidence=['runs/R02/flow/'+name+'-state-final.json','runs/R02/flow/'+name+'-stale-rejection.json','runs/R02/flow/'+name+'-shape-rejection.json','runs/R02/flow/'+name+'-input-rejection.json']) for c in plan['criteria']]))
 checks.append(dict(case=name,exact_policy='pass',stale='rejected_unchanged',shape='rejected_unchanged',input='rejected'))
results=dict(package_hash=flowctl.digest(p),plan_hash=p['acceptance']['plan_hash'],cases=rows);save('case-results.json',results);assessment=packagectl.assess(p,results);save('assessment.json',assessment);assert assessment['verdict']=='pass',assessment
s=load(out/'factory-verify.json')
for label,artifact in [('verify',dict(evaluation=dict(results=results))),('deliver',dict(delivery=dict(package='challenges/renewal-flow/package.json',assessment_path='runs/R02/flow/assessment.json',limits=plan['limitations'])))]:
 d=factoryctl.pending(s);save(label+'-dispatch.json',d);r=dict(invocation_id=d['invocation_id'],outcome='ok',artifacts=artifact,evidence=['runs/R02/flow/case-results.json']);save(label+'-response.json',r);s=factoryctl.advance(s,r);save('factory-'+label+'-complete.json',s)
save('report.json',dict(passed=True,cases=checks,host='Root agent, same-context; no native child/provider SDK claim',limits=plan['limitations'],tokens=None,cost=None))
print(json.dumps(dict(cases_passed=len(checks),protocol_rejections=12,factory_status=factoryctl.pending(s)['status'])))
