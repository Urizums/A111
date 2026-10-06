"""Development packaging only. No executable helper enters the distributed skill."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

root=Path(__file__).resolve().parents[2]
workspace=root.parents[1]
source=root/'runs/R10/candidate/C8/forge-agent-flow'
output=workspace/'outputs/forge-agent-flow'
archive=workspace/'outputs/Forge-C8-meta-workflow.zip'
standalone=workspace/'work/c8-standalone/forge-agent-flow'
assert not output.exists() and not archive.exists() and not standalone.exists()
output.parent.mkdir(parents=True,exist_ok=True)
lock=json.loads((root/'runs/R10/candidate/C8-lock.json').read_text(encoding='utf-8'))
assert len(lock['files'])==5
for row in lock['files']:
    p=root/row['path'];raw=p.read_bytes()
    assert p.is_relative_to(source) and p.suffix=='.md'
    assert hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['size_bytes']
shutil.copytree(source,output)
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(output.rglob('*')):
        if p.is_file():z.write(p,'forge-agent-flow/'+p.relative_to(output).as_posix())
standalone.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        relative=Path(member.filename)
        assert not relative.is_absolute() and '..' not in relative.parts and relative.suffix=='.md'
    z.extractall(standalone.parent)
checked=[]
for row in lock['files']:
    rel=(root/row['path']).relative_to(source)
    assert (standalone/rel).read_bytes()==(source/rel).read_bytes()==(output/rel).read_bytes()
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',(standalone/rel).read_text(encoding='utf-8')):
        target=(standalone/rel).parent/link.split('#')[0]
        assert target.resolve().is_relative_to(standalone.resolve()) and target.is_file()
    checked.append(rel.as_posix())
result=dict(ok=True,files=checked,output=str(output),archive=str(archive),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),archive_size_bytes=archive.stat().st_size,standalone_extraction=str(standalone),byte_identical=True,script_files=0,test_files=0,personal_installation=False,scope='real standalone packaging and structural checks; R10/R11 behavioral acceptance separate',tokens=None,cost=None)
target=root/'runs/R11/package/standalone-result.json'
target.parent.mkdir(parents=True,exist_ok=True)
with target.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False))
