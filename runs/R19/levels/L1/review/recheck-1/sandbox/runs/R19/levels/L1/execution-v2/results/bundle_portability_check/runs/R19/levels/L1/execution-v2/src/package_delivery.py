"""Runnable official-source bundle; explicit scope, no reviewer runtime."""
from pathlib import Path
import hashlib,json,zipfile
from solve import ROOT


def build():
    relative_root=Path('runs/R19/levels/L1/execution-v2');entries={}
    for name in ['src','configs','inputs','model','figures','paper','results/final','results/sensitivity','results/v2','results/modules_v3','results/clean_reproduction_final','review']:
        for p in (ROOT/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and 'qa' not in p.relative_to(ROOT).parts and 'drafts' not in p.relative_to(ROOT).parts:
                entries[(relative_root/p.relative_to(ROOT)).as_posix()]=p
    for name in ['README.md','REVISION.md','TODO.md','results/smoke_v3.json','logs/repair_iterations.md','logs/repair_commands.json','logs/environment.json','history/original_result.json','history/repair_regression_attempt_01_failed.json','history/initial_review_report.md','history/initial_review_result.json']:
        entries[(relative_root/name).as_posix()]=ROOT/name
    raw=ROOT.parents[2]/'inputs/raw'
    for p in raw.iterdir():
        if p.is_file():entries[(Path('runs/R19/inputs/raw')/p.name).as_posix()]=p
    manifest={'kind':'informed F1 repair, author checks only; initial a4 failed; independent re-review pending',
              'scope':'official-source 7-task regeneration, disclosed/adjacent regression, 235 layout checks, paper rebuild; not automatic replay of complete past research history',
              'root_result_json':'external completion record omitted to avoid self-reference and stale ZIP hash',
              'payload_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in sorted(entries.items())}}
    dest=ROOT/'bundle_manifest.json';dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    entries[(relative_root/'bundle_manifest.json').as_posix()]=dest
    with zipfile.ZipFile(ROOT/'algorithm_bundle.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for name,p in sorted(entries.items()):z.write(p,name)
    report={'entries':len(entries),'bytes':(ROOT/'algorithm_bundle.zip').stat().st_size,'sha256':hashlib.sha256((ROOT/'algorithm_bundle.zip').read_bytes()).hexdigest(),'included_reviewer_runtime':False}
    (ROOT/'logs/bundle_build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':build()
