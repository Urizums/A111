from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ex=Path(__file__).resolve().parent.parent;old=ex/'source/build_paper_v3.py';new=ex/'source/build_paper_v4.py';text=old.read_text('utf-8')
before="        md += [e['title'],'| '+' | '.join(e['headers'])+' |','| '+' | '.join(['---']*len(e['headers']))+' |']+['| '+' | '.join(map(str,row))+' |' for row in e['rows']]+['来源：'+e['source']]"
after="        table_lines=['| '+' | '.join(e['headers'])+' |','| '+' | '.join(['---']*len(e['headers']))+' |']+['| '+' | '.join(map(str,row))+' |' for row in e['rows']]\n        md += [e['title'],'\\n'.join(table_lines),'来源：'+e['source']]"
assert before in text;text=text.replace(before,after)
text=text.replace('论文位于 execution/paper-final','论文位于 execution/paper-final-v4')
with new.open('x',encoding='utf-8') as f:f.write(text)
entry={'utc':datetime.now(timezone.utc).isoformat(),'category':'editable document interface repair','observed':'root consumer noted blank lines between Markdown table rows break GFM tables','change':'serialize each whole table as one contiguous Markdown block; final appendix points at actual final version directory','scientific_changes':False,'old_outputs_preserved':['paper-v1','paper-v2','paper-final'],'new_outputs':'paper-final-v4','old_source_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'new_source_sha256':hashlib.sha256(new.read_bytes()).hexdigest()}
with (ex/'markdown-interface-repair-v4.json').open('x',encoding='utf-8') as f:json.dump(entry,f,ensure_ascii=False,indent=2)
print(json.dumps(entry,ensure_ascii=False,indent=2))
