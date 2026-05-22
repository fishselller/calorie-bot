from __future__ import annotations
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Meal, User
from app.localization.texts import t


def _progress_bar(current: float, total: float, length: int = 10) -> str:
    if total <= 0:
        return ""
    pct = min(current / total, 1.0)
    filled = round(pct * length)
    bar = "▓" * filled + "░" * (length - filled)
    return f"{bar} {pct*100:.0f}%"


async def build_report(
    user: User,
    session: AsyncSession,
    meal_type: Optional[str] = None,
    report_date: Optional[date] = None,
) -> str:
    lang        = user.language
    report_date = report_date or date.today()

    stmt = select(Meal).where(
        Meal.user_id == user.id,
        Meal.date    == report_date,
    )
    if meal_type and meal_type != "full":
        stmt = stmt.where(Meal.meal_type == meal_type)
    stmt = stmt.order_by(Meal.created_at)

    meals = (await session.execute(stmt)).scalars().all()

    if not meals:
        return t("report_empty", lang)

    title = t("report_title", lang, date=report_date.strftime("%d.%m.%Y"))
    lines = [title, ""]

    if meal_type and meal_type != "full":
        lines.append(f"*{t(meal_type, lang)}*")
        for m in meals:
            lines.append(f"  • {m.product_name} — {m.grams:.0f}г → {m.calories:.0f} ккал")
    else:
        grouped: dict[str, list] = {}
        for m in meals:
            grouped.setdefault(m.meal_type, []).append(m)
        for mt in ("breakfast", "lunch", "dinner", "snack"):
            if mt not in grouped:
                continue
            lines.append(f"*{t(mt, lang)}*")
            for m in grouped[mt]:
                lines.append(f"  • {m.product_name} — {m.grams:.0f}г → {m.calories:.0f} ккал")
            lines.append("")

    tc    = sum(m.calories for m in meals)
    tp    = sum(m.protein  for m in meals)
    tf    = sum(m.fat      for m in meals)
    tcarb = sum(m.carbs    for m in meals)

    lines.append(t("report_total", lang, calories=tc, protein=tp, fat=tf, carbs=tcarb))

    # Progress bars if norms set
    if user.cal_norm:
        norm_label = {"ru": "📈 *Прогресс к норме:*", "uk": "📈 *Прогрес до норми:*", "en": "📈 *Progress to goal:*"}
        lines.append("")
        lines.append(norm_label.get(lang, norm_label["ru"]))
        lines.append(f"🔥 {tc:.0f} / {user.cal_norm:.0f} ккал  {_progress_bar(tc, user.cal_norm)}")
        if user.prot_norm:
            lines.append(f"💪 {tp:.1f} / {user.prot_norm:.0f} г Б  {_progress_bar(tp, user.prot_norm)}")
        if user.fat_norm:
            lines.append(f"🧈 {tf:.1f} / {user.fat_norm:.0f} г Ж  {_progress_bar(tf, user.fat_norm)}")
        if user.carb_norm:
            lines.append(f"🍞 {tcarb:.1f} / {user.carb_norm:.0f} г У  {_progress_bar(tcarb, user.carb_norm)}")

    return "\n".join(lines)
