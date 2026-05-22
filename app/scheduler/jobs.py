"""
Scheduled jobs:
  - 07:00 local time → morning greeting
  - 21:00 local time → daily report
"""
import logging
from datetime import datetime, date

import pytz
from sqlalchemy import select

from app.db import AsyncSessionLocal, User
from app.localization import t
from app.services.report import build_report

logger = logging.getLogger(__name__)


async def send_morning_greetings(bot) -> None:
    """Send morning greeting to all users whose local time is 07:00."""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users  = result.scalars().all()

    for user in users:
        try:
            tz  = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
            if local.hour == 7 and local.minute == 0:
                await bot.send_message(user.id, t("morning", user.language))
        except Exception as e:
            logger.warning(f"Morning greeting failed for {user.id}: {e}")


async def send_evening_reports(bot) -> None:
    """Send daily summary to all users whose local time is 21:00."""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users  = result.scalars().all()

    for user in users:
        try:
            tz    = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
            if local.hour == 21 and local.minute == 0:
                async with AsyncSessionLocal() as session:
                    text = await build_report(user, session, meal_type="full",
                                              report_date=date.today())
                await bot.send_message(user.id, text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Evening report failed for {user.id}: {e}")
