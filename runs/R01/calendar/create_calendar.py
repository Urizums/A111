"""One-off workshop calendar; deliberately no project/factory wrapper."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

root = Path(__file__).resolve().parent
source = json.loads((root/'input.json').read_text())
start = datetime.fromisoformat(source['local_start']).replace(tzinfo=ZoneInfo(source['timezone']))
end = start + timedelta(minutes=source['duration_minutes'])
utc = lambda value:value.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
escape = lambda text:text.replace('\\','\\\\').replace('\n','\\n').replace(';','\\;').replace(',','\\,')
lines = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Agent Forge//One-off Workshop//ZH','BEGIN:VEVENT',
         'UID:'+source['uid'],'DTSTAMP:'+utc(datetime.now(timezone.utc)),
         'DTSTART:'+utc(start),'DTEND:'+utc(end),'SUMMARY:'+escape(source['title']),
         'DESCRIPTION:'+escape(source['description']),'LOCATION:'+escape(source['location']),
         'END:VEVENT','END:VCALENDAR']
(root/'workshop.ics').write_bytes(('\r\n'.join(lines)+'\r\n').encode())
print(json.dumps(dict(path=str(root/'workshop.ics'),start_utc=utc(start),end_utc=utc(end)),ensure_ascii=False))
