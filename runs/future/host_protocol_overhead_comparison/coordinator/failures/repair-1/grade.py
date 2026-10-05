"""Root source grader, never supplied to workers. It does not call providers."""
import copy
import hashlib
import json
from pathlib import Path
import sys

def expected(m):
    out=[]
    if m['id']=='P1':
        bookings=copy.deepcopy(m['bookings'])
        for r in m['requests']:
            if r['start']>=r['end']: d,e='reject','invalid_interval'
            elif r['tool'] not in m['tools']: d,e='review','unknown_tool'
            elif any(b['tool']==r['tool'] and r['start']<b['end'] and b['start']<r['end'] for b in bookings): d,e='reject','conflict'
            else: d,e='accept','free';bookings.append(r)
            out.append(dict(id=r['id'],decision=d,reason=e))
    elif m['id']=='P2':
        hosts=copy.deepcopy(m['hosts'])
        for r in m['jobs']:
            host=None
            if r['cpu']<=0 or r['memory']<=0:d,e='reject','invalid_request'
            else:
                h=next((h for h in hosts if h['cpu']>=r['cpu'] and h['memory']>=r['memory']),None)
                if h is None:d,e='wait','capacity_unavailable'
                else:
                    d,e,host='assign','capacity',h['id'];h['cpu']-=r['cpu'];h['memory']-=r['memory']
            out.append(dict(id=r['id'],decision=d,reason=e,host=host))
    elif m['id']=='K1':
        for r in m['submissions']:
            if r['owner_consent'] is not True:d,e='hold','consent_required'
            elif r['provenance_docs'] is False:d,e='review','provenance_missing'
            elif r['material'] not in ['ceramic','textile','metal']:d,e='review','unsupported_material'
            elif r['condition']=='fragile':d,e='review','conservation_needed'
            else:d,e='accept','eligible'
            out.append(dict(id=r['id'],decision=d,reason=e))
    elif m['id']=='K2':
        seats=m['seats'].copy()
        for r in m['applications']:
            if r['incomplete']:d,e='reject','incomplete'
            elif r['age']<16:d,e='review','guardian_required'
            elif r['track'] not in seats:d,e='review','unknown_track'
            elif seats[r['track']]>0:d,e='admit','seat_available';seats[r['track']]-=1
            else:d,e='wait','full'
            out.append(dict(id=r['id'],decision=d,reason=e))
    else:raise ValueError('Unbound material')
    return {'decisions':out}

def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def grade(sample):
    request=json.loads((sample/'job/request.json').read_text())
    mpath=Path(request['work']['inputs']['material']); m=json.loads(mpath.read_text())
    want=expected(m); got=json.loads((sample/'worker/business.json').read_text())
    reply=json.loads((sample/'worker/reply.json').read_text())
    embedded=reply['result'] if request['kind']=='project' else reply['result']['artifacts']
    checks={'exact_original_decisions':got==want,'reply_matches_business':embedded==got,
            'bound_inputs_unchanged':all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'] for x in request['work']['input_files']),
            'artifact_hashes':all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'] for x in reply['artifacts'])}
    logs=[(p,json.loads(p.read_text())) for p in sorted((sample/'worker/logs').glob('*.json'))]
    checks['captured_bootstrap_first']=bool(logs) and min(logs,key=lambda x:x[1]['begin']['monotonic_ns'])[0].name=='001-bootstrap.json'
    checks['captured_preflight']=any('check-reply' in j['argv'] and j.get('exit_code')==0 and 'payload_valid' in j.get('stdout','') for p,j in logs)
    draft=json.loads((sample/'worker/reply.draft.json').read_text())
    checks['separate_incomplete_draft']=draft['outcome'] is None
    corrections=json.loads((sample/'worker/corrections.json').read_text())
    checks['reported_repair_budget']=len(corrections['corrections'])<=2
    report=dict(schema='forge-source-review/1',sample=sample.name,source=ref(mpath),policy=m['policy'],
                expected=want,observed=got,checks=checks,business_pass=all(checks.values()),
                corrections=corrections,worker_logs=[ref(p) for p,j in logs],
                limits=['Root is independent of business workers but authored protocol and grader.',
                        'Recorded subprocess inventory is cooperative, not authenticated completeness or provider compute time.',
                        'Original source inspection and grader authoring precede measured decision construction.'])
    with (sample/'coordinator/source-review.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'sample':sample.name,'checks':checks,'expected':want,'observed':got}))

if __name__=='__main__':grade(Path(sys.argv[1]).resolve())
