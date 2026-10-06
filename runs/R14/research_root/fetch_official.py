"""Read official public attachments only; source lookup, no third-party execution."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib
import importlib.util
import json
import urllib.request

DIRECTORY=Path(__file__).resolve().parent
rows=[]
for stem,url in [
 ('2026-bigdata-charter','https://files.mathorcup.org/uploads/files/20260903/1788430945523653.pdf'),
 ('2026-bigdata-registration','https://files.mathorcup.org/uploads/files/20260903/1788430033944665.pdf')]:
    row=dict(url=url,accessed=datetime.now(timezone(timedelta(hours=8))).isoformat(),source='official attachment',
             authentic_content_verified=False)
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=20) as response:
            raw=response.read()
            row.update(status=response.status,final_url=response.url,size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if raw.startswith(b'%PDF'):
            path=DIRECTORY/(stem+'.pdf')
            with path.open('xb') as handle:handle.write(raw)
            row.update(pdf_header=True,saved_as=path.name)
            if importlib.util.find_spec('pypdf'):
                from pypdf import PdfReader
                reader=PdfReader(path)
                text='\n\n'.join(page.extract_text() or '' for page in reader.pages)
                target=DIRECTORY/(stem+'.txt')
                with target.open('x',encoding='utf-8',newline='\n') as handle:handle.write(text)
                row.update(extracted_text=target.name,pages=len(reader.pages),authentic_content_verified=True)
        else:
            row['limits']='Response is not a PDF; unseen rule contents remain unknown.'
    except Exception as exc:
        row.update(error_type=type(exc).__name__,error=str(exc),limits='Failed public source lookup; no rule/date/AI permission inferred.')
    rows.append(row)
with (DIRECTORY/'retrieval.json').open('x',encoding='utf-8',newline='\n') as handle:
    json.dump(dict(lookups=rows,limits='Primary-source retrieval only; compare official dates/contents before use.'),handle,ensure_ascii=False,indent=2);handle.write('\n')
print(json.dumps(rows,ensure_ascii=False))
