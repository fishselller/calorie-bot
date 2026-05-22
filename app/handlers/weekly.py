from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from datetime import date, timedelta
from sqlalchemy import select, func

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Meal

router = Router()

DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
DAYS_UK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


async def _get_or_create_user(uid, session):
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


@router.message(Command("week"))
@router.message(F.text.in_({"📅 Тиждень", "📅 Неделя", "📅 Week"}))
async def cmd_week(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language

        # Get last 7 days
        today = date.today()
        week_start = today - timedelta(days=6)

        # Get all meals for the week
        meals = (await session.execute(
            select(Meal).where(
                Meal.user_id == user.id,
                Meal.date >= week_start,
                Meal.date <= today,
            ).order_by(Meal.date)
        )).scalars().all()

        # Group by date
        by_date: dict = {}
        for m in meals:
            if m.date not in by_date:
                by_date[m.date] = {"cal": 0, "prot": 0, "fat": 0, "carbs": 0, "products": []}
            by_date[m.date]["cal"]   += m.calories
            by_date[m.date]["prot"]  += m.protein
            by_date[m.date]["fat"]   += m.fat
            by_date[m.date]["carbs"] += m.carbs
            by_date[m.date]["products"].append(m.product_name)

        # Top products
        all_products: dict = {}
        for m in meals:
            all_products[m.product_name] = all_products.get(m.product_name, 0) + 1
        top3 = sorted(all_products.items(), key=lambda x: x[1], reverse=True)[:3]

    if not by_date:
        empty = {"ru": "За эту неделю нет записей.", "uk": "За цей тиждень немає записів.", "en": "No records this week."}
        await message.answer(empty.get(lang, empty["ru"]))
        return

    days_names = {"ru": DAYS_RU, "uk": DAYS_UK, "en": DAYS_EN}.get(lang, DAYS_RU)
    titles = {
        "ru": f"📅 *Отчёт за неделю*\n_{week_start.strftime('%d.%m')} — {today.strftime('%d.%m.%Y')}_\n",
        "uk": f"📅 *Звіт за тиждень*\n_{week_start.strftime('%d.%m')} — {today.strftime('%d.%m.%Y')}_\n",
        "en": f"📅 *Weekly report*\n_{week_start.strftime('%d.%m')} — {today.strftime('%d.%m.%Y')}_\n",
    }

    lines = [titles.get(lang, titles["ru"])]

    total_cal = 0
    total_prot = 0
    total_fat = 0
    total_carb = 0
    days_with_data = 0
    best_day = None
    best_diff = float("inf")

    for i in range(7):
        d = week_start + timedelta(days=i)
        day_name = days_names[d.weekday()]
        date_str = d.strftime("%d.%m")

        if d in by_date:
            cal = by_date[d]["cal"]
            total_cal  += cal
            total_prot += by_date[d]["prot"]
            total_fat  += by_date[d]["fat"]
            total_carb += by_date[d]["carbs"]
            days_with_data += 1

            # Check norm
            if user.cal_norm:
                diff = abs(cal - user.cal_norm)
                status = "✅" if cal <= user.cal_norm * 1.1 else "❌"
                if diff < best_diff:
                    best_diff = diff
                    best_day = day_name
            else:
                status = "📝"

            lines.append(f"*{day_name}* {date_str} — {cal:.0f} ккал {status}")
        else:
            no_data = {"ru": "нет записей", "uk": "немає записів", "en": "no records"}
            lines.append(f"*{day_name}* {date_str} — _{no_data.get(lang, no_data['ru'])}_")

    # Totals
    if days_with_data > 0:
        avg_cal  = total_cal  / days_with_data
        avg_prot = total_prot / days_with_data
        avg_fat  = total_fat  / days_with_data
        avg_carb = total_carb / days_with_data

        avg_labels = {
            "ru": f"\n━━━━━━━━━━━━━━━\n📊 *Среднее за день:*\n🔥 {avg_cal:.0f} ккал\n💪 Б {avg_prot:.1f}г | 🧈 Ж {avg_fat:.1f}г | 🍞 У {avg_carb:.1f}г",
            "uk": f"\n━━━━━━━━━━━━━━━\n📊 *Середнє за день:*\n🔥 {avg_cal:.0f} ккал\n💪 Б {avg_prot:.1f}г | 🧈 Ж {avg_fat:.1f}г | 🍞 У {avg_carb:.1f}г",
            "en": f"\n━━━━━━━━━━━━━━━\n📊 *Daily average:*\n🔥 {avg_cal:.0f} kcal\n💪 P {avg_prot:.1f}g | 🧈 F {avg_fat:.1f}g | 🍞 C {avg_carb:.1f}g",
        }
        lines.append(avg_labels.get(lang, avg_labels["ru"]))

        if best_day and user.cal_norm:
            best_labels = {
                "ru": f"🏆 Лучший день: *{best_day}*",
                "uk": f"🏆 Найкращий день: *{best_day}*",
                "en": f"🏆 Best day: *{best_day}*",
            }
            lines.append(best_labels.get(lang, best_labels["ru"]))

        if top3:
            top_labels = {"ru": "\n🍽 *Топ продуктов:*", "uk": "\n🍽 *Топ продуктів:*", "en": "\n🍽 *Top products:*"}
            lines.append(top_labels.get(lang, top_labels["ru"]))
            for i, (name, cnt) in enumerate(top3, 1):
                lines.append(f"  {i}. {name} — {cnt}x")

    await message.answer("\n".join(lines), parse_mode="Markdown")
