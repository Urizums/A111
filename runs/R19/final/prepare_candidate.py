"""Prepare implicated C12 documents and a distinct forward slice."""
import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'runs/R19/final'


def row(path):
    data = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(),
                size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), path
    path.write_text(value if isinstance(value, str) else
                    json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')


old = ROOT / 'runs/R19/candidate/C11/forge-agent-flow'
new = HERE / 'candidate/C12/forge-agent-flow'
oldlock = json.loads((ROOT / 'runs/R19/candidate/C11-lock.json').read_text(encoding='utf-8'))
assert all(row(ROOT / entry['path']) == entry for entry in oldlock['files'])
shutil.copytree(old, new)
path = new / 'references/evaluation.md'
text = path.read_text(encoding='utf-8')
anchor = 'remove a rejection condition or silently call acceptance a smoke pass.'
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + '''
Make the case activate the condition named in its selected assertion: a
support-load claim needs stacked/transmitted load; a floor-only case leaves
that claim untested.''')
anchor = 'Require the appropriate target runtime: numerical computation for numerical'
assert text.count(anchor) == 1
text = text.replace(anchor, '''Bind artifact identities and fields to original source definitions before
recomputation; producer labels cannot override source constraints. Check the
relevant value domain before comparisons or aggregation: NaN/Inf cannot stand
for finite physical quantities or pass a constraint by default. Preserve source
conflicts rather than silently trusting output metadata.

''' + anchor)
path.write_text(text, encoding='utf-8')
path = new / 'references/modeling.md'
text = path.read_text(encoding='utf-8')
before = '''fatal mathematical or evidential defects from optional editorial polish. Repair
the former with new checked results before strengthening the narrative.'''
after = '''mathematical, evidential or meaning defects from optional style. Language that
obscures definitions, reasoning or conclusion scope belongs in substantive
review; do not defer it to later polishing. Repair the affected argument against
checked evidence before strengthening the narrative.'''
assert text.count(before) == 1
text = text.replace(before, after)
anchor = '## Interpret prompt detail honestly'
assert text.count(anchor) == 1
text = text.replace(anchor, '''Check the format the reader will receive: critical numbers, units, formulas,
assumptions and claim strength must survive rendering, conversion and rewriting.
Correct source text does not establish a correct exported document. Explain for
the intended reader; keep execution provenance accessible without letting internal
run logs replace the scientific or practical argument.

''' + anchor)
path.write_text(text, encoding='utf-8')
files = [p for p in sorted(new.rglob('*')) if p.is_file()]
assert len(files) == 9 and all(p.suffix == '.md' for p in files)
references = []
for path in files:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if '://' not in target and not target.startswith('#'):
            assert (path.parent / target.split('#')[0]).exists(), (path, target)
            references.append(target)
write(HERE / 'candidate/C12-lock.json',
      dict(schema='forge-revision-lock/1', revision='C12', parent='C11',
           frozen_at=datetime.now(timezone.utc).isoformat(),
           files=[row(p) for p in files],
           claim='Distinct doc-only identity; forward acceptance pending, not replacement C11 verdict.'))
package = HERE / 'package/Forge-C12-meta-workflow-candidate.zip'
package.parent.mkdir()
with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(new.parent).as_posix())
with zipfile.ZipFile(package) as archive:
    assert archive.testzip() is None and len(archive.namelist()) == 9
    for path in files:
        assert archive.read(path.relative_to(new.parent).as_posix()) == path.read_bytes()
write(HERE / 'package/package-lock.json',
      dict(schema='forge-revision-lock/1', revision='C12-package',
           files=[row(package)], claim='ZIP bytes/9 Markdown, no scripts/tests; behavior pending.'))
inputs = HERE / 'forward/inputs'
inputs.mkdir(parents=True)
preparation = ROOT / 'runs/R19/observations/forward-case-preparation'
for name in ['request.md', 'problem.md', 'raw.json']:
    shutil.copyfile(preparation / name, inputs / name)
with (inputs / 'problem.md').open('a', encoding='utf-8') as stream:
    stream.write('\n最终论文交付PDF与可编辑中文源文，供独立读者查看；这是文件格式要求，不是篇幅配额。\n')
write(inputs / 'input-lock.json',
      dict(schema='forge-revision-lock/1', revision='C12-forward-new-raw',
           frozen_at=datetime.now(timezone.utc).isoformat(),
           files=[row(inputs / name) for name in ['request.md', 'problem.md', 'raw.json']],
           origin='New root-created toy; original preparation retained. PDF/source format clarified before dispatch. No old solutions/papers.'))
criteria = [
    dict(id='b1', assertion='Original raw goal/identities/units/constraints and all items respected; actual model/computed output with justified bounded conclusions.'),
    dict(id='b2', assertion='Selected smoke assertions have activated conditions and actual receiving evidence; uncovered assertions stay in full gate, not silently weakened.'),
    dict(id='b3', assertion='Receiver checks source-bound identity and relevant finite value domains; actual valid/invalid paired paths do not default to producer labels or invalid comparisons.'),
    dict(id='b4', assertion='Usable complete Chinese scientific argument and final PDF/source agree on numbers, units, formulas, assumptions and claim strength; reader recovers problem, mechanism, result and limits.'),
    dict(id='b5', assertion='Fresh independent consumer executes from raw through transferred workflow and recomputes relevant feasibility/objectives/paper values; author checks alone are not acceptance.')
]
write(HERE / 'forward/acceptance.json',
      dict(frozen_at=datetime.now(timezone.utc).isoformat(), candidate='C12',
           mandatory=criteria,
           producer_packet='Only C12, own request/raw problem and neutral tools/write boundary; no external acceptance/expected answers/old cases/root diagnosis.',
           reviewer_packet='Original request/raw/skill, frozen design/actual outputs and assertions; no intended numeric answer/author diagnosis/previous verdict.',
           roles='Fresh combined designer/producer and separate fresh independent consumer/acceptor; two contexts, not the original three-context L1-4 condition.',
           limits='Relevant new-task vertical slice only; no causal C11/C12 superiority, new level, contest/prize or October performance claim. No universal repair cap or artificial whole-task deadline.'))
assert all(row(ROOT / entry['path']) == entry for entry in oldlock['files'])
write(HERE / 'preparation-result.json',
      dict(candidate='C12', changed_references=['evaluation.md', 'modeling.md'],
           markdown_files=9, bundled_scripts=0, bundled_tests=0,
           local_references_checked=len(references), zip=row(package),
           prior_C11_unchanged=True, forward_status='frozen_not_dispatched'))
print(json.dumps(dict(candidate='C12', documents=9, product_scripts=0,
                      product_tests=0, zip_readback_equal=True, forward='prepared_not_executed')))
