"""Source-bound synthesis first step; no regrading of the four trials."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
rows=[]
for level in range(1,5):
    path=ROOT/f'runs/R19/levels/L{level}/diagnostic-result.json'
    j=json.loads(path.read_text(encoding='utf-8'))
    rows.append(dict(level=level,diagnostic_path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        initial=j['initial_scientific_verdict'],latest=j['latest_scientific_verdict'],initial_quality=j['initial_quality'],latest_quality=j['latest_quality'],
        latest_mandatory_pass=j['latest_mandatory_pass'],paper_artifacts=j.get('paper_artifacts') or [e['path'] for e in json.loads((ROOT/f'runs/R19/levels/L{level}/execution-v2-lock.json').read_text(encoding='utf-8'))['files'] if e['path'] in {f'runs/R19/levels/L{level}/execution-v2/paper/paper.md',f'runs/R19/levels/L{level}/execution-v2/paper/paper.pdf'}],closure_reason=j['closure_reason']))
assert all(len(row['paper_artifacts'])==2 and all((ROOT/p).is_file() for p in row['paper_artifacts']) for row in rows)
out=ROOT/'runs/R19/final/comparison.json'
assert not out.exists()
out.write_text(json.dumps(dict(candidate='C11',status='four_actual_diagnostics_read_not_regraded',trials=rows,
    conditions='Same frozen C11, official revised spring D raw files and original L1-4 prompts; independent first reviews, same-actor informed revisions separately recorded.',
    confounds=['One generated sample per level; no repeat-trial estimates','Admissible support/orientation defaults and algorithm/search choices differ','Informed extra research/repair resources are not first-trial resources'],
    limits='Descriptive mechanism evidence only; not causal prompt-level ranking, prize/score estimate, original global optima or October big-data readiness.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(actual_levels=4,latest=[dict(level=r['level'],mandatory_pass=r['latest_mandatory_pass']) for r in rows],synthesis='started_evidence_readback_only')))
