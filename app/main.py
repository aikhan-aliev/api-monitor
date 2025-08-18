from fastapi import FastAPI, HTTPException
from typing import Optional
from app.models import TargetIn, Target
from app.store import add_target, list_targets, remove_target, get_last_result
from app.scheduler import start_scheduler, schedule_all_targets
from app.models import CheckResult
from datetime import datetime

app = FastAPI(title="API Monitor (MVP)")

@app.on_event("startup")
async def on_startup():
    demo = Target.from_in(TargetIn(
        name="GitHub API Root",
        url="https://api.github.com/",
        interval_s=60,
        timeout_ms=3000,
        expected_statuses=[200]
    ))
    add_target(demo)
    start_scheduler()
    schedule_all_targets()

@app.get("/")
def home():
    return {"message": "API Monitor is running. See /docs for API spec."}

@app.get("/targets")
def get_targets():
    return list_targets()

@app.post("/targets", status_code=201)
def create_target(target_in: TargetIn):
    t = Target.from_in(target_in)
    add_target(t)
    # re-schedule so the new target gets its own job
    schedule_all_targets()
    return t

@app.delete("/targets/{target_id}")
def delete_target(target_id: str):
    ok = remove_target(target_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Target not found")
    schedule_all_targets()
    return {"deleted": target_id}

@app.get("/status")
def status(target_id: Optional[str] = None):
    """
    If target_id is provided, return only that target's last result;
    otherwise return last results for all targets we know about.
    """
    if target_id:
        r = get_last_result(target_id)
        if not r:
            # If no check has run yet, return a placeholder
            return {"target_id": target_id, "message": "No checks recorded yet"}
        return r
    # For MVP, we only keep the last result per target in memory.
    # Expose the list by matching target ids from the store.
    from app.store import TARGETS, LAST_RESULTS
    out = []
    for tid, tgt in TARGETS.items():
        r = LAST_RESULTS.get(tid)
        if r:
            out.append(r)
        else:
            out.append({"target_id": tid, "ok": None, "message": "No checks recorded yet"})
    return out
