"""Root-only separate manual/helper decision construction after source review."""
import copy
import json
import sys
from operate import STUDY,CANDIDATE,call,mark,save
from grade import ref

sample=STUDY/'samples'/sys.argv[1]; action=sys.argv[2]
request=json.loads((sample/'job/request.json').read_text())
reply=json.loads((sample/'worker/reply.json').read_text())
review=sample/'coordinator/source-review.json'
draft=sample/'coordinator/decision.draft.json';final=sample/'coordinator/decision.json'
if action=='draft':
    mark(sample,'decision-begin','decision','begin')
    if request['work']['inputs']['mode']=='B':
        args=[sys.executable,CANDIDATE/'scripts/hostdraft.py','decision','--job',sample/'job','--out',draft]
        if request['kind']=='project':args+=['--evidence',review]
        call(sample,'decision-helper-draft',args)
    else:
        results=({'acceptance_results':{'a_source':dict(status='not_run',level='review',evidence=[ref(review)])}}
                 if request['kind']=='project' else copy.deepcopy(reply['result']))
        save(draft,dict(schema_version='forge-host-decision/1',request_hash=reply['request_hash'],
             reply_sha256=ref(sample/'worker/reply.json')['sha256'],outcome=None,results=results,reason=None))
    print(json.dumps({'draft':str(draft)}))
elif action=='final':
    accepted=json.loads(review.read_text())['business_pass']; d=json.loads(draft.read_text())
    d['outcome']='done' if accepted else 'failed';d['reason']=None if accepted else 'Original source or protocol acceptance failed; see source-review.json'
    if accepted and request['kind']=='project':d['results']['acceptance_results']['a_source']['status']='pass'
    if not accepted:d['results']=None
    save(final,d)
    call(sample,'decision-check',[sys.executable,CANDIDATE/'scripts/hostdraft.py','check-decision','--job',sample/'job','--decision',final])
    mark(sample,'decision-end','decision','end')
    print(json.dumps({'outcome':d['outcome'],'decision':str(final)}))
elif action=='commit':
    call(sample,'commit',[sys.executable,CANDIDATE/'scripts/hostbridge.py','commit','--job',sample/'job','--decision',final])
    r=call(sample,'reconcile',[sys.executable,CANDIDATE/'scripts/hostbridge.py','reconcile','--job',sample/'job'])
    save(sample/'coordinator/reconcile.json',r);print(json.dumps(r))
else:raise ValueError('Unknown action')
