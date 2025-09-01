# app/main.py

from fastapi import FastAPI
from app.api import router
from app.db import init_db, get_or_create_demo_target
from app.scheduler import start_scheduler, schedule_all_targets

# Create FastAPI app
app = FastAPI(title="API Monitor (MVP, SQLite)")

# Mount the API router
app.include_router(router)


@app.on_event("startup")
async def on_startup():
    """
    1. Initialize the SQLite database (creates tables if they don't exist).
    2. Add a demo target (GitHub API) if it’s not already in the database.
    3. Start the scheduler and schedule all targets to run their periodic checks.
    """
    # Step 1: Initialize DB
    await init_db()

    # Step 2: Add demo target
    await get_or_create_demo_target()

    # Step 3: Start scheduler and schedule targets
    start_scheduler()
    await schedule_all_targets()
