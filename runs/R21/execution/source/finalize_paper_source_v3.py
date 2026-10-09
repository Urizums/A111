from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ex=Path(__file__).resolve().parent.parent;old=ex/'source/build_paper_v2.py';new=ex/'source/build_paper_v3.py';text=old.read_text('utf-8')
assert '论文位于 execution/paper-v1' in text
text=text.replace('论文位于 execution/paper-v1','论文位于 execution/paper-final')
with new.open('x',encoding='utf-8') as f:f.write(text)
entry={'utc':datetime.now(timezone.utc).isoformat(),'category':'document provenance correction','reason':'visual audit found appendix final paper directory still named failed paper-v1','change':'point final-paper directory to paper-final; no numeric, scientific, model, or selection change','previous_pdf_and_pages_preserved':'paper-v2','old_source_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'new_source_sha256':hashlib.sha256(new.read_bytes()).hexdigest()}
with (ex/'paper-provenance-correction-v3.json').open('x',encoding='utf-8') as f:json.dump(entry,f,ensure_ascii=False,indent=2)
print(json.dumps(entry,ensure_ascii=False,indent=2))
