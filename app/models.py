from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
from datetime import datetime
import uuid


class TargetIn(BaseModel):
    name: str
    url: HttpUrl
    method: str = "GET"
    expected_statuses: List[int] = [200, 201, 204]
    timeout_ms: int = 3000
    interval_s: int = 60
    retries: int = 2
    backoff_s: float = 0.5
    headers: Optional[Dict[str, str]] = None
    enabled: bool = True
    severity: str = "HIGH"


class Target(TargetIn):
    id: str

    @staticmethod
    def from_in(data: TargetIn) -> "Target":
        return Target(id=str(uuid.uuid4()), **data.model_dump())


class CheckResult(BaseModel):
    target_id: str
    checked_at: datetime
    ok: bool
    status: Optional[int] = None
    latency_ms: int
    error: Optional[str] = None
