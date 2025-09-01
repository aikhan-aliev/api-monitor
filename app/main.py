from fastapi import FastAPI
from app.api import router
from app.db import init_db, get_or_create_demo_target
from app.scheduler import start_scheduler, schedule_all_targets

app = FastAPI(title="API Monitor (MVP, SQLite)")

app.include_router(router)


@app.on_event("startup")
async def on_startup():
    #Initialize DB
    await init_db()

    # demo target
    await get_or_create_demo_target()

    #Start scheduler
    start_scheduler()
    await schedule_all_targets()
