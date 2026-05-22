import logging
from datetime import datetime, date

import pytz
from sqlalchemy import select

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Meal
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


async def send_lunch_reminder(bot) -> None:
    """13:00 local time — remind to log lunch if not logged yet."""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
    for user in users:
        try:
            tz    = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
            if local.hour == 15 and local.minute == 0:
                # Check if lunch already logged today
                lunch = (await session.execute(
                    select(Meal).where(
                        Meal.user_id == user.id,
                        Meal.date == date.today(),
                        Meal.meal_type == "lunch",
                    )
                )).scalar_one_or_none()

                if not lunch:
                    reminder = {
                        "ru": "🍲 Уже время обеда!\n\nВнеси данные про свой обед 👇",
                        "uk": "🍲 Вже час обіду!\n\nВнеси дані про свій обід 👇",
                        "en": "🍲 It's lunch time!\n\nLog your lunch data 👇",
                    }
                    await bot.send_message(
                        user.id,
                        reminder.get(user.language, reminder["ru"])
                    )
        except Exception as e:
            logger.warning(f"Lunch reminder failed for {user.id}: {e}")


async def send_dinner_reminder(bot) -> None:
    """18:00 local time — remind to log dinner if not logged yet."""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
    for user in users:
        try:
            tz    = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
            if local.hour == 18 and local.minute == 0:
                # Check if dinner already logged today
                dinner = (await session.execute(
                    select(Meal).where(
                        Meal.user_id == user.id,
                        Meal.date == date.today(),
                        Meal.meal_type == "dinner",
                    )
                )).scalar_one_or_none()

                if not dinner:
                    reminder = {
                        "ru": "🍖 Уже время ужина!\n\nВнеси данные про свой ужин 👇",
                        "uk": "🍖 Вже час вечері!\n\nВнеси дані про свою вечерю 👇",
                        "en": "🍖 It's dinner time!\n\nLog your dinner data 👇",
                    }
                    await bot.send_message(
                        user.id,
                        reminder.get(user.language, reminder["ru"])
                    )
        except Exception as e:
            logger.warning(f"Dinner reminder failed for {user.id}: {e}")


async def send_weight_reminder(bot) -> None:
    """Every Sunday at 20:00 user's local time."""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
    for user in users:
        try:
            tz    = pytz.timezone(user.timezone)
            local = now_utc.astimezone(tz)
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
