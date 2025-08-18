import time
import asyncio
import random
from datetime import datetime
from typing import Optional
import httpx
from app.models import Target, CheckResult

async def http_check(target: Target) -> CheckResult:
    """
    Perform an HTTP request with retries and backoff.
    Returns a CheckResult with latency, status, and error if any.
    """
    attempts = 0
    delay = target.backoff_s
    start = time.perf_counter()
    last_error: Optional[str] = None
    status_code: Optional[int] = None

    # One AsyncClient for this check (simple and fine for MVP).
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.request(
                    method=target.method,
                    url=str(target.url),
                    headers=target.headers or {},
                    timeout=target.timeout_ms / 1000,
                )
                status_code = resp.status_code
                break  # success
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_error = str(e)
                attempts += 1
                if attempts > target.retries:
                    break
                # Exponential backoff + tiny jitter
                await asyncio.sleep(delay + random.random() * 0.2)
                delay *= 2

    latency_ms = int((time.perf_counter() - start) * 1000)
    ok = (status_code in set(target.expected_statuses)) if status_code is not None else False

    return CheckResult(
        target_id=target.id,
        checked_at=datetime.utcnow(),
        ok=ok,
        status=status_code,
        latency_ms=latency_ms,
        error=last_error if not ok else None,
    )
