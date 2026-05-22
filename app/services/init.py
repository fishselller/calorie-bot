from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduler.jobs import send_morning_greetings, send_evening_reports


def create_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # Run every minute — each job checks internally if it's the right hour for the user's TZ
    scheduler.add_job(
        send_morning_greetings,
        trigger="cron",
        minute="*",
        kwargs={"bot": bot},
        id="morning",
        replace_existing=True,
        misfire_grace_time=30,
    )
    scheduler.add_job(
        send_evening_reports,
        trigger="cron",
        minute="*",
        kwargs={"bot": bot},
        id="evening",
        replace_existing=True,
        misfire_grace_time=30,
    )
    return scheduler
