"""Independent parse of the saved ICS against the source and known zone offset."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

root=Path(__file__).resolve().parent
source=json.loads((root/'input.json').read_text())
raw=(root/'workshop.ics').read_bytes()
assert raw.endswith(b'\r\n') and raw.count(b'BEGIN:VEVENT')==1
assert all(len(line)<=75 for line in raw.split(b'\r\n'))
fields=dict(line.split(':',1) for line in raw.decode().split('\r\n') if ':' in line)
start=datetime.strptime(fields['DTSTART'],'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
end=datetime.strptime(fields['DTEND'],'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
assert start.astimezone(ZoneInfo(source['timezone'])).replace(tzinfo=None)==datetime.fromisoformat(source['local_start'])
assert end-start==timedelta(minutes=source['duration_minutes'])
assert fields['UID']==source['uid'] and fields['SUMMARY']==source['title']
assert fields['DESCRIPTION'].replace('\\,',',').replace('\\;',';')==source['description']
assert fields['LOCATION']==source['location'] and 'ATTENDEE' not in fields
print(json.dumps(dict(passed=True,checks=8,source_fields_preserved=True,delivery_type='scoped_task',factory_created=False)))
