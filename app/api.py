from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models import TargetIn
from app.db import (
    add_target_from_in,
    list_targets,
    remove_target,
    get_last_result_for_target,
    list_last_results_for_all_targets,
)

from app.scheduler import schedule_all_targets

router = APIRouter()


@router.get("/")
async def home():
    return {"message": "API Monitor is running. See /docs for API spec."}


@router.get("/targets")
async def get_targets():
    return await list_targets()


@router.post("/targets", status_code=201)
async def create_target(target_in: TargetIn):
    t = await add_target_from_in(target_in)
    await schedule_all_targets()
    return t


@router.delete("/targets/{target_id}")
async def delete_target(target_id: str):
    ok = await remove_target(target_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Target not found")
    await schedule_all_targets()
    return {"deleted": target_id}


@router.get("/status")
async def status(target_id: Optional[str] = None):
    if target_id:
        r = await get_last_result_for_target(target_id)
        if not r:
            return {"target_id": target_id, "message": "No checks recorded yet"}
        return r

    return await list_last_results_for_all_targets()
