from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.store import list_targets, set_last_result
from app.checks.http_check import http_check

scheduler = AsyncIOScheduler()

async def run_check_for_target(target):
    result = await http_check(target)
    set_last_result(result)

def schedule_all_targets():
    scheduler.remove_all_jobs()
    for t in list_targets():
        if t.enabled:
            scheduler.add_job(
                run_check_for_target,
                "interval",
                seconds=t.interval_s,
                args=[t],
                id=t.id,
                replace_existing=True
            )

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
