from typing import Dict, Optional
from app.models import Target, CheckResult

# In-memory "database" for the MVP.
TARGETS: Dict[str, Target] = {}
LAST_RESULTS: Dict[str, CheckResult] = {}

def add_target(t: Target) -> None:
    TARGETS[t.id] = t

def get_target(tid: str) -> Optional[Target]:
    return TARGETS.get(tid)

def list_targets():
    return list(TARGETS.values())

def remove_target(tid: str) -> bool:
    return TARGETS.pop(tid, None) is not None

def set_last_result(r: CheckResult) -> None:
    LAST_RESULTS[r.target_id] = r

def get_last_result(tid: str) -> Optional[CheckResult]:
    return LAST_RESULTS.get(tid)
