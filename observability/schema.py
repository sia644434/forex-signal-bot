from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from typing import Any
import json,uuid
from .redaction import redact_value
@dataclass(slots=True)
class Event:
    timestamp:str; source:str; service:str; level:str; event:str; message:str=""
    environment:str="production"; symbol:str|None=None; timeframe:str|None=None; outcome:str|None=None
    cycle_id:str|None=None; commit_sha:str|None=None; deployment_id:str|None=None; correlation_id:str|None=None
    metadata:dict[str,Any]|None=None
    @classmethod
    def now(cls,source,service,level,event,message="",**kwargs):
        return cls(datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),source,service,level.upper(),event,message,correlation_id=kwargs.pop("correlation_id",None) or str(uuid.uuid4()),metadata=kwargs.pop("metadata",None),**kwargs)
    def to_dict(self): return redact_value({k:v for k,v in asdict(self).items() if v is not None})
    def to_json(self): return json.dumps(self.to_dict(),ensure_ascii=False,separators=(",",":"),sort_keys=True)
