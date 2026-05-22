from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import date, timedelta
from sqlalchemy import select, func

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Meal, Product

router = Router()

# Твой Telegram ID — только ты видишь статистику
ADMIN_ID = 245906683  # Замени на свой Telegram ID


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа.")
        return

    today = date.today()
    week_ago = today - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        # Total users
        total_users = (await session.execute(
            select(func.count()).select_from(User)
        )).scalar()

        # Total meals
        total_meals = (await session.execute(
            select(func.count()).select_from(Meal)
        )).scalar()

        # Today meals
        today_meals = (await session.execute(
            select(func.count()).select_from(Meal).where(Meal.date == today)
        )).scalar()

        # Active users today
        active_today = (await session.execute(
            select(func.count(Meal.user_id.distinct())).where(Meal.date == today)
        )).scalar()

        # Active users this week
        active_week = (await session.execute(
            select(func.count(Meal.user_id.distinct())).where(Meal.date >= week_ago)
        )).scalar()

        # Top 5 products
        top_products = (await session.execute(
            select(Meal.product_name, func.count(Meal.id).label("cnt"))
            .group_by(Meal.product_name)
            .order_by(func.count(Meal.id).desc())
            .limit(5)
        )).fetchall()

        # Total calories today (all users)
        cal_today = (await session.execute(
            select(func.sum(Meal.calories)).where(Meal.date == today)
        )).scalar() or 0

        # Saved products count
        products_count = (await session.execute(
            select(func.count()).select_from(Product)
        )).scalar()

    top_str = "\n".join([f"  {i+1}. {r[0]} — {r[1]} раз" for i, r in enumerate(top_products)]) or "  нет данных"

    await message.answer(
        f"📊 *Статистика бота*\n\n"
        f"👥 *Пользователи:*\n"
        f"  Всего: *{total_users}*\n"
        f"  Активны сегодня: *{active_today}*\n"
        f"  Активны за неделю: *{active_week}*\n\n"
        f"🍽 *Приёмы пищи:*\n"
        f"  Всего в базе: *{total_meals}*\n"
        f"  Записано сегодня: *{today_meals}*\n"
        f"  Калорий съедено сегодня (все): *{cal_today:.0f} ккал*\n\n"
        f"🗄 *База продуктов:*\n"
        f"  Сохранено продуктов: *{products_count}*\n\n"
        f"🏆 *Топ-5 продуктов:*\n{top_str}\n\n"
        f"📅 Дата: {today.strftime('%d.%m.%Y')}",
        parse_mode="Markdown"
    )
