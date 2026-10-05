"""Bundle the tested candidate, complete evidence workspace, and readable reports."""
import hashlib,io,json,tarfile
from pathlib import Path

root=Path(__file__).resolve().parents[3]
delivery=Path('/workspace/deliveries')
archives=['A111-R06-candidate-20261004.tar.gz','A111-R06-review-20261004.tar.gz']
verified=[]
candidate=json.loads((root/'runs/R06/final/source-candidate.json').read_text())
for name in archives:
    with tarfile.open(delivery/name) as archive:
        manifest=json.load(archive.extractfile('agent-forge/delivery-manifest.json'))
        names=archive.getnames()
        assert len(names)==len(set(names))==len(manifest['files'])+1
        assert set(names)=={'agent-forge/'+r['path'] for r in manifest['files']}|{'agent-forge/delivery-manifest.json'}
        indexed={r['path']:r for r in manifest['files']}
        for row in manifest['files']:
            member=archive.getmember('agent-forge/'+row['path']);assert member.isfile()
            data=archive.extractfile(member).read()
            assert len(data)==row['size_bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
        assert all(indexed[r['path']]['sha256']==r['sha256'] for r in candidate['files'])
        verified.append({'archive':name,'files':len(manifest['files']),'content_id':manifest['content_id'],
                         'sha256':hashlib.sha256((delivery/name).read_bytes()).hexdigest(),'all_candidate_files_match':True})
inputs={
 'candidate/'+archives[0]:(delivery/archives[0]).read_bytes(),
 'workspace/'+archives[1]:(delivery/archives[1]).read_bytes(),
}
for name,path in {
 'VERIFICATION_REPORT.md':'runs/R06/VERIFICATION_REPORT.md','issues.json':'runs/R06/issues.json',
 'summary.json':'runs/R06/final/summary.json','publication-check.json':'runs/R06/final/publication-check.json',
 'repair-budget-audit.json':'runs/R06/final/repair-budget-audit.json','RECOVERY.md':'runs/R06/RECOVERY.md',
 'checkpoint-at-packaging.json':'state/checkpoint.json',
}.items():inputs['reports/'+name]=(root/path).read_bytes()
inputs['README.txt']=('''R05/R06 审阅包；未提交或推送 dev，项目仍 active。

先读 reports/VERIFICATION_REPORT.md、issues.json、publication-check.json。
恢复完整工作区：解压 workspace/A111-R06-review-20261004.tar.gz，得到 agent-forge/。
该工作区包含代码、原始失败、测试报告及较新的状态。遵循 RECOVERY.md，先核实实际宿主与租约。
candidate/A111-R06-candidate-20261004.tar.gz 是两种 Python 的解压安装/冒烟实际使用的精确归档。
workspace 归档只追加了报告和状态；本包核对了两者全部交付文件哈希，以及固定候选的 1,446 个文件一致。
归档自己的后验报告不回填到原包；它们在 reports/ 和 workspace 归档中。
checkpoint-at-packaging 记录打包时仍持锁的 Root，是历史快照；恢复时查当前实际锁，不能复用旧 PID/worker。
所有必需独立验收、provider 与跨会话阻塞解除前，禁止提交或推送 dev。
''').encode()
inputs['archive-integrity.json']=(json.dumps({'archives':verified,'candidate_sha256':candidate['sha256']},indent=2)+'\n').encode()
manifest={'schema':'forge-review-envelope/1','files':[{'path':p,'size_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for p,b in sorted(inputs.items())]}
inputs['MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
output=delivery/'A111-R06-complete-review-20261004.tar.gz'
with output.open('xb') as stream,tarfile.open(fileobj=stream,mode='w:gz') as archive:
    for name,data in sorted(inputs.items()):
        entry=tarfile.TarInfo('A111-R06/'+name);entry.size=len(data);entry.mode=0o644
        archive.addfile(entry,io.BytesIO(data))
with tarfile.open(output) as archive:
    assert len(archive.getmembers())==len(inputs)
    for row in manifest['files']:
        data=archive.extractfile('A111-R06/'+row['path']).read()
        assert len(data)==row['size_bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
sha=hashlib.sha256(output.read_bytes()).hexdigest()
output.with_name(output.name+'.sha256').write_text(sha+'  '+output.name+'\n')
print(json.dumps({'archive':str(output),'sha256':sha,'size_bytes':output.stat().st_size,'all_envelope_members_verified':True,'nested_archives':verified}))
