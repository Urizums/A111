from urllib.request import Request, urlopen
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
root = Path('runs/R16/source')
items = [
 ('D_corrected.zip','https://www.mathorcup.org/uploads/files/20260417/1776438403640865.zip'),
 ('all_questions.zip','https://mathorcup.org/uploads/files/20260417/1776383723989262.zip'),
]
for name,url in items:
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; archival retrieval)'})
    with urlopen(req,timeout=45) as r:
        data=r.read()
        info={'file':name,'url':url,'status':r.status,'headers':dict(r.headers.items()),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'retrieved_utc':datetime.now(timezone.utc).isoformat()}
    (root/name).write_bytes(data)
    print(json.dumps(info,ensure_ascii=False))
