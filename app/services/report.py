from __future__ import annotations
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Meal, User
from app.localization import t


MEAL_EMOJI = {
    "breakfast": "🍳",
    "lunch":     "🍲",
    "dinner":    "🍖",
    "snack":     "🍎",
}


async def build_report(
    user: User,
    session: AsyncSession,
    meal_type: Optional[str] = None,   # None → full day
    report_date: Optional[date] = None,
) -> str:
    lang = user.language
    report_date = report_date or date.today()

    stmt = select(Meal).where(
        Meal.user_id == user.id,
        Meal.date == report_date,
    )
    if meal_type and meal_type != "full":
        stmt = stmt.where(Meal.meal_type == meal_type)
    stmt = stmt.order_by(Meal.created_at)

    result = await session.execute(stmt)
    meals = result.scalars().all()

    if not meals:
        return t("report_empty", lang)

    title = t("report_title", lang, date=report_date.strftime("%d.%m.%Y"))
    lines = [title, ""]

    if meal_type and meal_type != "full":
        # Single meal section
        lines.append(f"*{t(meal_type, lang)}*")
        for m in meals:
            lines.append(f"  • {m.product_name} — {m.grams:.0f}г → {m.calories:.0f} ккал")
    else:
        # Group by meal_type
        grouped: dict[str, list[Meal]] = {}
        for m in meals:
            grouped.setdefault(m.meal_type, []).append(m)

        for mt in ("breakfast", "lunch", "dinner", "snack"):
            if mt not in grouped:
                continue
            lines.append(f"*{t(mt, lang)}*")
            for m in grouped[mt]:
                lines.append(f"  • {m.product_name} — {m.grams:.0f}г → {m.calories:.0f} ккал")
            lines.append("")

    # Totals
    tc = sum(m.calories for m in meals)
    tp = sum(m.protein  for m in meals)
    tf = sum(m.fat      for m in meals)
    tcarb = sum(m.carbs for m in meals)

    lines.append(t("report_total", lang,
                   calories=tc, protein=tp, fat=tf, carbs=tcarb))

    return "\n".join(lines)
