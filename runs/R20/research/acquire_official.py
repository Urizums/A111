"""Read the two current organizer PDFs; keep original bytes and real failures."""
import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from pypdf import PdfReader

BASE = Path(__file__).resolve().parent
DOCS = [
    ('charter-2026', 'https://files.mathorcup.org/uploads/files/20260903/1788430945523653.pdf'),
    ('registration-2026', 'https://files.mathorcup.org/uploads/files/20260903/1788430033944665.pdf'),
]
rows = []
for name, url in DOCS:
    row = dict(name=name, source=url, retrieved_at=datetime.now(timezone.utc).isoformat())
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
            row.update(final_url=response.url, status=response.status,
                       content_type=response.headers.get('Content-Type'))
        assert data.startswith(b'%PDF-'), 'Not a PDF response'
        path = BASE / 'raw' / (name + '.pdf')
        with path.open('xb') as stream:
            stream.write(data)
        reader = PdfReader(path)
        text = '\n\n'.join(f'PAGE {i+1}\n' + (page.extract_text() or '')
                           for i, page in enumerate(reader.pages))
        extracted = BASE / (name + '-text.txt')
        with extracted.open('x', encoding='utf-8') as stream:
            stream.write(text)
        row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                   pages=len(reader.pages), path=path.name, extracted_text=extracted.name,
                   extraction='Actual pypdf page extraction; not visual inspection or rule interpretation')
    except Exception as error:
        row['error'] = dict(type=type(error).__name__, message=str(error))
    rows.append(row)
path = BASE / 'acquisition.json'
with path.open('x', encoding='utf-8') as stream:
    json.dump(dict(originals=rows, source_pages=['https://mathorcup.org/detail/2495',
        'https://mathorcup.org/detail/2494'], no_solution_or_paper_research=True,
        context='Official public raw documents only; web PDF redirect errors kept, no authorization denial.'),
        stream, ensure_ascii=False, indent=2)
print(json.dumps(rows, ensure_ascii=True))
raise SystemExit(1 if any('error' in row for row in rows) else 0)
