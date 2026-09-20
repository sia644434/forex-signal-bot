from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import json
from .schema import Event
from .redaction import redact_value
def parse_json_lines(text,source,service):
    events=[]
    for raw in text.splitlines():
        raw=raw.strip()
        if not raw: continue
        try: data=json.loads(raw)
        except json.JSONDecodeError: events.append(Event.now(source,service,"INFO","raw_log",raw)); continue
        if not isinstance(data,dict): events.append(Event.now(source,service,"INFO","raw_log",str(data))); continue
        ts=data.get("timestamp") or data.get("time") or datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        level=str(data.get("level") or data.get("severity") or "INFO").upper()
        message=str(data.get("message") or data.get("msg") or "")
        events.append(Event(timestamp=ts,source=source,service=service,level=level,event=str(data.get("event") or "log"),message=message,metadata=redact_value(data)))
    return events
def build_summary(events,commit_sha=None):
    items=list(events); levels=Counter(e.level for e in items); sources=Counter(e.source for e in items)
    errors=[e.to_dict() for e in items if e.level in {"ERROR","CRITICAL"}][-50:]
    return {"generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"commit_sha":commit_sha,"event_count":len(items),"levels":dict(levels),"sources":dict(sources),"errors":errors,"latest_events":[e.to_dict() for e in items[-50:]]}
def write_json(path,payload):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(redact_value(payload),ensure_ascii=False,indent=2,sort_keys=True)+"\\n",encoding="utf-8")
