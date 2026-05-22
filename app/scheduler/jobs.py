import logging
from datetime import datetime, date

import pytz
from sqlalchemy import select

from app.db.engine import AsyncSessionLocal
from app.db.models import User
from app.localization.texts import t
from app.services.report import build_report

logger = logging.getLogger(__name__)


async def send_morning_greetings(bot) -> None:
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
    for user in users:
        try:
            tz    = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
            if local.hour == 7 and local.minute == 0:
                await bot.send_message(user.id, t("morning", user.language))
        except Exception as e:
            logger.warning(f"Morning greeting failed for {user.id}: {e}")


async def send_evening_reports(bot) -> None:
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
    for user in users:
        try:
            tz    = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
            if local.hour == 21 and local.minute == 0:
                async with AsyncSessionLocal() as s2:
                    text = await build_report(user, s2, meal_type="full",
                                              report_date=date.today())
                await bot.send_message(user.id, text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Evening report failed for {user.id}: {e}")


async def send_weight_reminder(bot) -> None:
    """Every Sunday at 20:00 user's local time."""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
    for user in users:
        try:
            tz    = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
            # Sunday = weekday 6, 20:00
            if local.weekday() == 6 and local.hour == 20 and local.minute == 0:
                reminder = {
                    "ru": "⚖️ Воскресенье — время взвеситься!\n\nНажми кнопку *⚖️ Вес* или напиши /weight",
                    "uk": "⚖️ Неділя — час зважитися!\n\nНатисни кнопку *⚖️ Вага* або напиши /weight",
                    "en": "⚖️ Sunday — time to weigh in!\n\nTap *⚖️ Weight* button or type /weight",
                }
                await bot.send_message(
                    user.id,
                    reminder.get(user.language, reminder["ru"]),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.warning(f"Weight reminder failed for {user.id}: {e}")
