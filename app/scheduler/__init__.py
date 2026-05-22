from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler(bot) -> AsyncIOScheduler:
    from app.scheduler.jobs import (
        send_morning_greetings,
        send_evening_reports,
        send_weight_reminder,
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_morning_greetings, trigger="cron", minute="*",
        kwargs={"bot": bot}, id="morning",
        replace_existing=True, misfire_grace_time=30,
    )
    scheduler.add_job(
        send_evening_reports, trigger="cron", minute="*",
        kwargs={"bot": bot}, id="evening",
        replace_existing=True, misfire_grace_time=30,
    )
    scheduler.add_job(
        send_weight_reminder, trigger="cron", minute="*",
        kwargs={"bot": bot}, id="weight_reminder",
        replace_existing=True, misfire_grace_time=30,
    )
    return scheduler
