"""Root-only study setup and receipt plumbing. No native calls or business answers."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT/'runs/R01/candidate/forge-agent-flow'
CAPTURE = CANDIDATE/'scripts/capture.py'
PLAN = json.loads((STUDY/'study-plan.json').read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')


def call(sample, label, argv):
    log = sample/'coordinator/logs'/(label+'.json')
    r = subprocess.run([sys.executable,str(CAPTURE),'cli','--record',str(log),'--actor','coordinator','--',*map(str,argv)],
                       cwd=ROOT,capture_output=True,text=True)
    if r.returncode:
        print(r.stdout);print(r.stderr,file=sys.stderr)
        raise RuntimeError('Captured command failed: '+label)
    return json.loads(r.stdout) if r.stdout.strip() else None


def mark(sample, label, stage, event):
    return call(sample,label,[sys.executable,CAPTURE,'mark','--events',sample/'coordinator/events',
                              '--actor','coordinator','--stage',stage,'--event',event])


def native(sample, label, tool, event, payload):
    return call(sample,label,[sys.executable,CAPTURE,'native','--record',sample/'coordinator/native'/(label+'.json'),
                             '--actor','coordinator','--tool',tool,'--event',event,'--payload',payload])


def prepare(spec):
    sample=STUDY/'samples'/spec['id'];worker=sample/'worker';worker.mkdir(parents=True,exist_ok=False)
    mark(sample,'001-setup-begin','setup','begin')
    material=(ROOT/spec['material']).resolve();protocol=STUDY/'public/protocol.md';bootstrap=STUDY/'public/bootstrap.py'
    command=[sys.executable,str(CAPTURE),'cli','--record',str(worker/'logs/001-bootstrap.json'),
             '--actor','worker','--',sys.executable,str(bootstrap),str(sample/'job/request.json')]
    prompt='EXACT FIRST COMMAND (execute before any other shell command):\n'+shlex.join(command)+'\n\n'
    prompt+='Then follow the bound public protocol and original material printed by bootstrap. Mode '+spec['mode']+'. Complete your own original business task, separate draft, captured preflight and markers within its stated scope/budget. No sibling reads, delegation, global status queries, network or external effects.'
    work=dict(prompt=prompt,inputs=dict(mode=spec['mode'],material=str(material),protocol=str(protocol),
          capture=str(CAPTURE),hostdraft=str(CANDIDATE/'scripts/hostdraft.py'),worker=str(worker)),
          input_files=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [material,protocol,bootstrap,ROOT/PLAN['candidate_lock']]],
          write_paths=[str(worker)],reply_path=str(worker/'reply.json'))
    save(sample/'work.json',work)
    if spec['kind']=='project':
        plan=dict(schema_version='forge-project-plan/1',id='study_'+spec['id'],goal='Apply original '+spec['pair']+' material policy',deliverable_kind='scoped_task',
             requirements=[dict(id='req_source',text='Return all exact decisions from supplied policy, with no external effects.',origin='explicit',basis=str(material),acceptance_ids=['a_source'])],
             acceptance=[dict(id='a_source',assertion='Business decisions match every original source policy field and order.',required=True,level='review')],
             tasks=[dict(id='work',title='Apply original source policy',depends_on=[],owner='gpt-6-luna',write_paths=['worker/'],acceptance_ids=['a_source'])])
        save(sample/'plan.json',plan)
        call(sample,'002-init',[sys.executable,CANDIDATE/'scripts/projectctl.py','init',sample/'plan.json','--state',sample/'state.json'])
        args=['--kind','project','--state',sample/'state.json','--task','work']
    else:
        package=json.loads((ROOT/'skills/forge-agent-flow/assets/example-package.json').read_text())
        package['design']['necessity']['rationale']='One bounded original policy-classification node, no external capability.'
        flow=package['flow'];flow['id']='study_'+spec['pair'].lower();flow['goal']='Apply original source policy exactly without external actions.'
        flow['assumptions']=['Original material is supplied and no external effects are performed.']
        flow['inputs']={'material':{'type':'string','description':'Original JSON material and its exact decision policy.'}}
        flow['artifacts']={'decisions':{'type':'array','description':'Source-ordered decisions with exact required original fields.'}};flow['outputs']=['decisions'];flow['entry']='classify'
        node=flow['nodes'][0];node.update(id='classify',reads=['material'],writes=['decisions'],prompt='Apply the supplied JSON material policy. Return decisions in source order with its exact required fields; never perform external actions.',acceptance=['All decisions match original material policy exactly.'],emits={'ok':['decisions'],'error':[],'blocked':[]})
        package['execution']['node_settings']={'classify':{'model':'gpt-6-luna','write_scope':[str(worker)]}}
        package['acceptance']['criteria']=[dict(id='source',kind='machine',required=True,assertion='Every decision equals original source policy in original order.')]
        save(sample/'package.json',package);save(sample/'inputs.json',{'material':material.read_text()})
        call(sample,'002-start',[sys.executable,CANDIDATE/'scripts/packagectl.py','start',sample/'package.json','--inputs',sample/'inputs.json','--state',sample/'state.json'])
        args=['--kind','package','--state',sample/'state.json','--package',sample/'package.json']
    call(sample,'003-prepare',[sys.executable,CANDIDATE/'scripts/hostbridge.py','prepare',*args,'--work',sample/'work.json','--job',sample/'job','--parent','/root'])
    issue=call(sample,'004-issue',[sys.executable,CANDIDATE/'scripts/hostbridge.py','issue','--job',sample/'job'])
    save(sample/'issue.json',issue);save(sample/'spawn-arguments.json',issue['spawn_arguments'])
    mark(sample,'005-setup-end','setup','end')
    native(sample,'006-create-intent','collaboration.spawn_agent','intent',sample/'spawn-arguments.json')
    print(json.dumps(issue['spawn_arguments'],ensure_ascii=False,indent=2))


def accepted(sample):
    native(sample,'007-create-return','collaboration.spawn_agent','return',sample/'create-return.json')
    call(sample,'008-accepted',[sys.executable,CANDIDATE/'scripts/hostbridge.py','accepted','--job',sample/'job','--receipt',sample/'create-return.json'])
    mark(sample,'009-receive-begin','receive','begin')


def poll_intent(sample,n):
    if not 1<=n<=PLAN['settings']['status_queries_per_worker']:raise ValueError('Query budget exhausted')
    arg=json.loads((sample/'issue.json').read_text())['host_status_query'];save(sample/f'query-{n}-arguments.json',arg)
    native(sample,f'query-{n}-intent','collaboration.list_agents','intent',sample/f'query-{n}-arguments.json')
    print(json.dumps(arg))


def poll_return(sample,n):
    path=sample/f'query-{n}-return.json'
    native(sample,f'query-{n}-return','collaboration.list_agents','return',path)
    status=json.loads(path.read_text())['agents'][0]['agent_status']
    command='receive' if isinstance(status,dict) and 'completed' in status else 'observe'
    args=[sys.executable,CANDIDATE/'scripts/hostbridge.py',command,'--job',sample/'job','--receipt',path]
    if command=='receive':args+=['--reply',sample/'worker/reply.json']
    result=call(sample,f'query-{n}-{command}',args)
    if command=='receive':mark(sample,'receive-end','receive','end')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','accepted','poll-intent','poll-return']);parser.add_argument('sample');parser.add_argument('--query',type=int)
    a=parser.parse_args();spec=next(x for x in PLAN['samples'] if x['id']==a.sample);sample=STUDY/'samples'/a.sample
    if a.action=='prepare':prepare(spec)
    elif a.action=='accepted':accepted(sample)
    elif a.action=='poll-intent':poll_intent(sample,a.query)
    else:poll_return(sample,a.query)
