from independent_audit import raw_config,audit,OUT
import json,copy,itertools,sys
sys.path.insert(0,str(OUT/'sandbox/runs/R19/levels/L1/execution/src'))
from check import check_fleet as author_check
from solve import validate_config
base=raw_config();cs={c['id']:c for c in base['cargo']};records=[]
def item(cid,k=1,x=0,y=0,z=0,dims=None):
    c=cs[cid];ds=dims or c['dims'];perm=next(list(p) for p in itertools.permutations(range(3)) if [c['dims'][j] for j in p]==list(ds))
    return {'item_id':f'{cid}-{k:04d}','type_id':cid,'truck_id':'test','x':x,'y':y,'z':z,'dx':ds[0],'dy':ds[1],'dz':ds[2],'weight':c['weight'],'category':c['category'],'orientation':perm}
def case(name,items,expected,change=None,complete=False):
    cfg=copy.deepcopy(base)
    if change:change(cfg)
    truck={'truck_id':'test','vehicle_type':'T1','vehicle':copy.deepcopy(cfg['vehicles'][0]),'items':items};d={'config':cfg,'fleet':[truck]}
    independent,_=audit(d,name,complete,cfg)
    try:
        r=author_check(d['fleet'],cfg,complete);accepted=r['valid'];err=r.get('errors',[]);exception=None
    except Exception as e:accepted=False;err=[];exception=repr(e)
    records.append({'name':name,'expected_valid':expected,'independent_valid':independent['valid'],'independent_violations':independent['violations'],'author_checker_valid':accepted,'author_errors':err,'author_exception':exception,'author_checker_correct':accepted==expected,'independent_correct':independent['valid']==expected,'input':d})
case('valid face contact',[item('G1'),item('G1',2,x=60)],True)
case('positive volume overlap .01cm',[item('G1'),item('G1',2,x=59.99)],False)
case('rotated box beyond wall',[item('G1',y=180,dims=[30,60,40])],False)
case('top clearance short with grounded stack',[item('G5',k,z=(k-1)*60) for k in range(1,4)]+[item('G2',z=180,dims=[25,35,50])],False)
case('over payload',[item('G1')],False,lambda c:c['vehicles'][0].update(payload=10))
case('duplicate IDs',[item('G1'),item('G1',x=60)],False)
case('missing full inventory',[],False,complete=True)
case('directional rotated',[item('G4',dims=[60,80,50])],False)
case('fragile loaded',[item('G3'),item('G1',z=40)],False)
case('gap under fragile',[item('G2',dims=[35,50,25]),item('G2',2,x=40,dims=[35,50,25]),item('G3',z=25)],False)
case('noncoplanar support',[item('G2',dims=[35,50,25]),item('G1',x=35,dims=[40,60,30]),item('G3',z=30)],False)
case('cumulative load exceeds though direct load does not',[item('G5',k,z=(k-1)*60) for k in range(1,4)],False,lambda c:c.update(bearing=200))
case('direct center outside one directional support',[item('G4'),item('G4',2,x=80),item('G1',x=49,z=50)],False)
case('inventory overflow',[item('G1'),item('G1',2,x=60)],False,lambda c:c['cargo'][0].update(quantity=1))
badfragile=item('G3');badfragile['category']='standard'
case('source category relabel conceals load above G3',[badfragile,item('G1',z=40)],False)
badcfg=copy.deepcopy(base);badcfg['cargo'][0]['weight']=None
try:validate_config(badcfg);missing_rejected=False;missing_message=None
except Exception as e:missing_rejected=True;missing_message=repr(e)
report={'tests':records,'author_correct_count':sum(r['author_checker_correct'] for r in records),'independent_correct_count':sum(r['independent_correct'] for r in records),'test_count':len(records),'missing_business_input_rejected':missing_rejected,'missing_business_error':missing_message,'order':'run after own frozen final and all scenario audits, then inspect author checker as tested object','claim_limit':'controlled task-relevant mutations; final immutable placements audited separately'}
(OUT/'independent-boundary-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['author_correct_count','independent_correct_count','test_count','missing_business_input_rejected']},ensure_ascii=False));print('false_acceptances',[r['name'] for r in records if not r['author_checker_correct']])
