from pathlib import Path
import zipfile,json,subprocess,sys,time,datetime,hashlib,shutil
R=Path(__file__).resolve().parents[1]
readme='''# 可运行算法附件（L2 v2）
离线Windows Python3.12，已有numpy/scipy/python-docx/openpyxl；不安装、不联网。
尺寸整数mm，质量kg，费用元/趟；CSV每件ID/同质类型/类别/原尺寸/单重，JSON车厢内尺寸/载重/费用/30mm间隙。
从本目录运行：
py -3.12 -X utf8 -B code/main.py --raw raw --config configs/main.json --output results/full
py -3.12 -X utf8 -B code/check_cases.py
py -3.12 -X utf8 -B code/validate.py --placements results/full/selected/q2_cost/placements.csv --items data/items.csv --vehicles data/vehicles.json --output results/full/external_validation.json
--scenario all默认完成四个全运和两车型单车集；--scenario q2_cost只运行单个费用主问题，少了其它场景提供的候选，可能得到更差合法上界。--items/--vehicles/--config/--output可指定接口。
主种子19、22随机启动+3固定权重，45秒每场景MILP；外层总耗时更长。有限库、限时及容差不证明全局最优或次级库内最优。库存严格等式，全部输出独立构造代码的checker重算后导出。单车点为搜索非支配集。
新保护块与累计传载假设在论文，全部底面充分支撑/均匀密度/接触面积分担为保守工程模型，未验证动态材料安全。易碎地板/固定方向可config声明；定向仅012。未知官方I/O、AI规则/投稿授权，附件2缺完整订单字段，仅资格审计。
本ZIP包含真实源码、原三官方文件、输入与配置，没有预装答案。完整论文、对照9条、当前36参数、原36历史/首审、失败与资源账在外部execution-v2研究交付包，不要求此小算法ZIP单独包含全部研究历史。
'''
if __name__=='__main__':
 package=R/'algorithm.zip'
 (R/'algorithm_README.md').write_text(readme,encoding='utf8')
 with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
  for n in ['main.py','blocks.py','validate.py','check_cases.py']:z.write(R/'code'/n,'code/'+n)
  for folder in ['data','raw','configs']:
   for p in (R/folder).rglob('*'):
    if p.is_file():z.write(p,p.relative_to(R).as_posix())
  z.write(R/'algorithm_README.md','README.md')
 stage=R/'checks/zip_unpacked'
 if stage.exists():raise RuntimeError('refuse overwrite prior zip check')
 with zipfile.ZipFile(package) as z:z.extractall(stage)
 d=R/'logs/zip_full';d.mkdir(parents=True,exist_ok=True);cmd=[sys.executable,'-X','utf8','-B','code/main.py','--raw','raw','--config','configs/main.json','--output','results/full'];start=time.perf_counter();receipt={'command':cmd,'cwd':str(stage),'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'outer_limit_seconds':300,'zip_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'model':None,'tokens':None,'cost':None}
 (d/'start.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
 with (d/'stdout.log').open('w',encoding='utf8') as so,(d/'stderr.log').open('w',encoding='utf8') as se:
  p=subprocess.Popen(cmd,cwd=stage,stdout=so,stderr=se);receipt['pid']=p.pid
  (d/'start.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
  try:receipt['exit']=p.wait(timeout=300);receipt['timeout']=False
  except subprocess.TimeoutExpired:p.kill();p.wait();receipt['exit']=p.returncode;receipt['timeout']=True
 receipt.update({'outer_seconds':time.perf_counter()-start,'utc_finish':datetime.datetime.now(datetime.timezone.utc).isoformat()});(d/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
 if receipt['exit']!=0:raise RuntimeError('ZIP full run failed, original receipt preserved')
 from audit_v2 import metrics,rd
 items=rd(stage/'data/items.csv');records=[]
 for folder in sorted((stage/'results/full').glob('*/*')):
  if (folder/'run.json').exists():records.append(metrics(folder,items))
 assert len(items)==3000
 s=json.loads((stage/'results/full/summary.json').read_text());final=json.loads((R/'results/final/summary.json').read_text());a={r['scenario']:(r['vehicle_count'],r['cost_yuan']) for r in s['runs'] if r['method']=='column_patterns_MILP'};b={r['scenario']:(r['vehicle_count'],r['cost_yuan']) for r in final['runs'] if r['method']=='column_patterns_MILP'}
 from main import dump
 dump(R/'checks/zip_full_validation.json',{'fresh_3000_raw_all_scenarios':True,'all_layouts_recomputed':records,'current_main_hash_matches_zip':hashlib.sha256((stage/'code/main.py').read_bytes()).hexdigest()==hashlib.sha256((R/'code/main.py').read_bytes()).hexdigest(),'fresh_results':a,'delivered_results':b,'objective_equal':a==b,'limits':'limited solver timings may alter incumbent; no hidden preloaded answer; no claim universal feasibility'})
 print(json.dumps({'zip_outer_seconds':receipt['outer_seconds'],'all_layouts':len(records),'results':a,'objective_equal':a==b}))
