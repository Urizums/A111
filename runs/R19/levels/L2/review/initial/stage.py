from pathlib import Path
import shutil,json,zipfile,hashlib,datetime
b=Path.cwd();o=b/'runs/R19/levels/L2/review/initial';e=b/'runs/R19/levels/L2/execution';s=o/'staged';s.mkdir(exist_ok=True)
shutil.copytree(e/'code',s/'code',dirs_exist_ok=True)
shutil.copy2(e/'config.json',s/'config.json')
# Inspect archive paths before extraction; source zip is never changed.
z=e/'algorithm_attachment.zip';target=o/'zip_staged';target.mkdir(exist_ok=True)
with zipfile.ZipFile(z) as a:
 for n in a.namelist():
  p=(target/n).resolve()
  if not p.is_relative_to(target.resolve()):raise ValueError('Unsafe archive member')
 a.extractall(target)
 names=a.namelist()
(o/'staging.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_code_files':[{'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'copied_hash_match':hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256((s/'code'/p.name).read_bytes()).hexdigest()} for p in (e/'code').glob('*.py')],'zip_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'zip_members':names,'source_untouched':True,'writes':str(o)},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'copied_code_files':len(list((s/'code').glob('*.py'))),'zip_members':len(names),'zip_top':[p.name for p in target.iterdir()]},ensure_ascii=False))
