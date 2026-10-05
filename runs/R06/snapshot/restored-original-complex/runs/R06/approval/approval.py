"""Local fictional approval-rule example. No external authority, network or side effects."""
import argparse,hashlib,json,os,re,sqlite3,sys
from pathlib import Path

class Conflict(ValueError):pass
def strict_load(path):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('Duplicate JSON key')
            result[k]=v
        return result
    def invalid(value):raise ValueError('Non-finite JSON value')
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=invalid)
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def identity(value):return isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}',value) is not None
def validate(policy,r):
    if set(policy)!={'schema','version','fictional_local_only','enabled','allowed_categories','max_amount_cents'} or policy['schema']!='local-demo-approval-policy/1' or policy['fictional_local_only'] is not True:raise ValueError('Only explicit local demo policies supported')
    if type(policy['enabled']) is not bool or not identity(policy['version']) or type(policy['max_amount_cents']) is not int or policy['max_amount_cents']<0:raise ValueError('Invalid policy')
    if not isinstance(policy['allowed_categories'],list) or not policy['allowed_categories'] or not all(identity(x) for x in policy['allowed_categories']):raise ValueError('Invalid categories')
    fields={'request_id','idempotency_key','ticket_id','expected_version','category','amount_cents','risk','evidence_complete','requester','reviewer'}
    if not isinstance(r,dict) or set(r)!=fields:raise ValueError('Exact request fields required')
    if not all(identity(r[k]) for k in ['request_id','idempotency_key','ticket_id','category','requester','reviewer']):raise ValueError('Invalid request identity')
    if type(r['expected_version']) is not int or r['expected_version']<0:raise ValueError('Invalid expected version')
    if r['amount_cents'] is not None and (type(r['amount_cents']) is not int or r['amount_cents']<0):raise ValueError('Amount must be nonnegative integer cents or null')
    if r['risk'] not in {'low','medium','high','unknown'} or type(r['evidence_complete']) is not bool:raise ValueError('Invalid risk/evidence')
def classify(p,r):
    if not p['enabled']:reason='policy_disabled'
    elif r['reviewer']==r['requester']:reason='self_review'
    elif r['amount_cents'] is None:reason='amount_unknown'
    elif r['category'] not in p['allowed_categories']:reason='category_review'
    elif r['risk']!='low':reason='risk_review'
    elif not r['evidence_complete']:reason='evidence_missing'
    elif r['amount_cents']>p['max_amount_cents']:reason='amount_review'
    else:return 'approved','sample_rule_match'
    return 'manual',reason

def connect(path):
    db=sqlite3.connect(path,timeout=10,isolation_level=None);db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''CREATE TABLE IF NOT EXISTS tickets(ticket_id TEXT PRIMARY KEY, version INTEGER NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL, policy_version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS requests(idempotency_key TEXT PRIMARY KEY,request_id TEXT UNIQUE NOT NULL,payload TEXT NOT NULL,response TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id),previous_version INTEGER NOT NULL,new_version INTEGER NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,policy_version TEXT NOT NULL,request_id TEXT NOT NULL,UNIQUE(ticket_id,new_version));''')
    return db
def decide(path,policy,r,crash=False):
    validate(policy,r);payload=canonical({'policy':policy,'request':r});db=connect(path)
    try:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT * FROM requests WHERE idempotency_key=? OR request_id=?',(r['idempotency_key'],r['request_id'])).fetchall()
        if existing:
            if len(existing)!=1 or existing[0]['payload']!=payload:raise Conflict('Idempotency/request identity content conflict')
            response=json.loads(existing[0]['response']);db.commit();return dict(**response,reused=True)
        previous=db.execute('SELECT * FROM tickets WHERE ticket_id=?',(r['ticket_id'],)).fetchone();version=previous['version'] if previous else 0
        if version!=r['expected_version']:raise Conflict('Expected version conflict; latest version '+str(version))
        decision,reason=classify(policy,r);response=dict(ticket_id=r['ticket_id'],version=version+1,decision=decision,reason=reason,policy_version=policy['version'],request_id=r['request_id'],local_demo_only=True)
        db.execute('INSERT INTO tickets VALUES (?,?,?,?,?) ON CONFLICT(ticket_id) DO UPDATE SET version=excluded.version,decision=excluded.decision,reason=excluded.reason,policy_version=excluded.policy_version',(r['ticket_id'],version+1,decision,reason,policy['version']))
        db.execute('INSERT INTO audit(ticket_id,previous_version,new_version,decision,reason,policy_version,request_id) VALUES (?,?,?,?,?,?,?)',(r['ticket_id'],version,version+1,decision,reason,policy['version'],r['request_id']))
        db.execute('INSERT INTO requests VALUES (?,?,?,?)',(r['idempotency_key'],r['request_id'],payload,canonical(response)))
        if crash:os._exit(75)
        db.commit();return dict(**response,reused=False)
    except BaseException:db.rollback();raise
    finally:db.close()
def inspect(path,ticket):
    with connect(path) as db:
        row=db.execute('SELECT * FROM tickets WHERE ticket_id=?',(ticket,)).fetchone()
        return dict(ticket=dict(row) if row else None,audit=[dict(x) for x in db.execute('SELECT * FROM audit WHERE ticket_id=? ORDER BY id',(ticket,))],local_demo_only=True)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path,required=True);sub=p.add_subparsers(dest='action',required=True)
    d=sub.add_parser('decide');d.add_argument('request',type=Path);d.add_argument('--policy',type=Path,required=True);d.add_argument('--simulate-crash-before-commit',action='store_true')
    g=sub.add_parser('inspect');g.add_argument('ticket_id');a=p.parse_args()
    try:
        result=decide(a.database,strict_load(a.policy),strict_load(a.request),a.simulate_crash_before_commit) if a.action=='decide' else inspect(a.database,a.ticket_id)
        print(json.dumps(result,ensure_ascii=False));return 0
    except Conflict as exc:print(json.dumps({'error':str(exc),'conflict':True}),file=sys.stderr);return 3
    except (ValueError,TypeError,OSError,sqlite3.Error) as exc:print(json.dumps({'error':str(exc)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
