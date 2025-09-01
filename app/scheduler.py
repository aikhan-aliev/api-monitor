from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.checks.http_check import http_check
from app.db import list_targets, insert_check_result

scheduler = AsyncIOScheduler()


async def run_check_for_target(target):
    result = await http_check(target)
    await insert_check_result(result)


async def schedule_all_targets():
    scheduler.remove_all_jobs()
    targets = await list_targets()
    for t in targets:
        if t.enabled:
            scheduler.add_job(
                run_check_for_target,
                "interval",
                seconds=t.interval_s,
                args=[t],
                id=t.id,
                replace_existing=True,
            )


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
