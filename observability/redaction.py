from __future__ import annotations
import re
from typing import Any
_SECRET_KEY=re.compile(r"(token|secret|password|api[_-]?key|authorization|cookie|credential|private[_-]?key)",re.I)
_BEARER=re.compile(r"(?i)(bearer\\s+)[A-Za-z0-9._~+/=-]+")
def redact_value(value: Any)->Any:
    if isinstance(value,dict): return {k:("[REDACTED]" if _SECRET_KEY.search(str(k)) else redact_value(v)) for k,v in value.items()}
    if isinstance(value,list): return [redact_value(v) for v in value]
    if isinstance(value,tuple): return [redact_value(v) for v in value]
    if isinstance(value,str): return _BEARER.sub(r"\\1[REDACTED]",value)
    return value
