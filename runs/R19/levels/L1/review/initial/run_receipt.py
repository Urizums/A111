from pathlib import Path
import subprocess,shutil,json,time,datetime,hashlib,os,argparse
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(label,args,cwd,timeout=180):
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['MPLCONFIGDIR']=str(HERE/'runtime-matplotlib')
    with (HERE/f'{label}-stdout.txt').open('w',encoding='utf-8') as so,(HERE/f'{label}-stderr.txt').open('w',encoding='utf-8') as se:
        proc=subprocess.Popen(args,cwd=cwd,env=env,stdout=so,stderr=se,text=True)
        timed_out=False
        try: code=proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill();code=proc.wait();timed_out=True
    result={'label':label,'command':args,'cwd':str(cwd),'pid':proc.pid,'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':time.perf_counter()-t,'exit_code':code,'timed_out':timed_out,'process_terminal':proc.poll() is not None,'timeout_limit_seconds':timeout,'stdout_path':f'{label}-stdout.txt','stderr_path':f'{label}-stderr.txt'}
    (HERE/f'{label}-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
if __name__=='__main__':
    sandbox=HERE/'sandbox'; dest=sandbox/'runs/R19/levels/L1/execution';src=ROOT/'runs/R19/levels/L1/execution'
    if sandbox.exists():raise RuntimeError('Sandbox must be new; preserve prior receipts')
    shutil.copytree(src,dest)
    raw=sandbox/'runs/R19/inputs/raw';raw.mkdir(parents=True)
    for name in ['2026年第十六届MathorCup数学应用挑战赛题目—D题.pdf','附件1.docx','附件2：验证数据集.xlsx']:
        shutil.copy2(ROOT/'runs/R19/inputs/raw'/name,raw/name)
    copied=[]
    for p in src.rglob('*'):
        if p.is_file(): copied.append({'relative':p.relative_to(src).as_posix(),'original_sha256':sha(p),'copy_sha256':sha(dest/p.relative_to(src))})
    (HERE/'copy-verification.json').write_text(json.dumps({'files':copied,'all_match':all(x['original_sha256']==x['copy_sha256'] for x in copied),'source_code_modified':False},ensure_ascii=False,indent=2),encoding='utf-8')
    receipt=run('raw-reproduce',['py','-3.12','-X','utf8','-B',str(dest/'src/reproduce.py'),'--out',str(HERE/'raw-rerun')],sandbox,180)
    print(json.dumps(receipt,ensure_ascii=False,indent=2))
