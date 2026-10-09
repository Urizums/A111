from pathlib import Path
import argparse,json,re,base64,hashlib,importlib.util
from pypdf import PdfReader
ap=argparse.ArgumentParser();ap.add_argument('--execution',required=True);ap.add_argument('--paper',required=True);ap.add_argument('--newout',required=True);a=ap.parse_args();ex=Path(a.execution);paper=Path(a.paper);out=Path(a.newout);out.mkdir(parents=True,exist_ok=False)
md=(paper/'paper.md').read_text('utf-8');ele=json.loads((paper/'paper_elements.json').read_text('utf-8'));tabs=[e for e in ele if e['kind']=='table'];blocks=[];current=[]
for line in md.splitlines()+['']:
    if line.startswith('|'):current.append(line)
    elif current:blocks.append(current);current=[]
assert len(blocks)==len(tabs)==14
parsed=[]
for b,t in zip(blocks,tabs):
    cells=[[s.strip() for s in line.strip().strip('|').split('|')] for line in b]
    assert len(cells)==len(t['rows'])+2 and cells[0]==t['headers']
    assert all(re.fullmatch(r':?-{3,}:?',s) for s in cells[1])
    assert cells[2:]==[[str(v) for v in row] for row in t['rows']]
    assert all(len(row)==len(t['headers']) for row in cells)
    parsed.append({'title':t['title'],'rows':len(t['rows']),'columns':len(t['headers']),'contiguous_GFM_block':True})
parser='explicit GFM contiguous header/delimiter/row structural parser'
if importlib.util.find_spec('mistune'):
    import mistune
    ast=mistune.create_markdown(renderer='ast',plugins=['table'])(md);assert sum(e['type']=='table' for e in ast)==14;parser+=' + mistune table-plugin AST'
texts=[p.extract_text() for p in PdfReader(paper/'paper.pdf').pages];pdftext=re.sub(r'\s+','',''.join(texts));missing=[]
for t in tabs:
    for row in [t['headers']]+t['rows']:
        for c in row:
            if re.sub(r'\s+','',str(c)) not in pdftext:missing.append(str(c))
assert not missing,missing
assert len(texts)==13 and all(len(t)>200 for t in texts)
assert '论文位于 execution/paper-final-v4' in md
assert all((paper/e['path']).exists() for e in ele if e['kind'] in ['figure','equation'])
commands=[]
for p in sorted((ex/'commands').glob('*.json')):
    if int(p.name.split('-')[0])>16:continue
    d=json.loads(p.read_text('utf-8'));assert d['state']=='finished' and d['end']['monotonic_ns']>=d['begin']['monotonic_ns']
    for stream in ['stdout','stderr']:
        raw=base64.b64decode(d[stream+'_base64'],validate=True);assert raw.decode('utf-8',errors='replace')==d[stream]
    commands.append({'file':str(p),'exit_code':d['exit_code'],'stdout_raw_bytes':len(base64.b64decode(d['stdout_base64'])),'stderr_raw_bytes':len(base64.b64decode(d['stderr_base64']))})
assert [c['exit_code'] for c in commands]==[0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0]
freeze=json.loads((ex/'prospective-freeze.json').read_text('utf-8'))
for name,digest in freeze['source_hashes'].items():assert hashlib.sha256((ex/'source/v1'/name).read_bytes()).hexdigest()==digest
result={'scope':'author document/interface/raw-evidence self-check; not independent acceptance or substitute for actual visual inspection','GFM_parser':parser,'tables':parsed,'all_table_cells_found_in_extracted_pdf':True,'pdf_pages':len(texts),'pdf_chars_by_page':[len(t) for t in texts],'figure_files':5,'final_path_correct':True,'command_raw_byte_receipts':commands,'initial_frozen_scientific_sources_unchanged':True,'expected_rejection':'010 output-exists guard, exit1 before fit','unexpected_failure_retained':'006 formula renderer, exit1, document-only repair, v1 retained','passed':True}
with (out/'final-document-check.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
