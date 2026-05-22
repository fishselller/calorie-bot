import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db import AsyncSessionLocal, User, Meal
from app.keyboards import meal_type_keyboard, report_keyboard
from app.localization import t
from app.services.nutrition import resolve

router = Router()


class FoodState(StatesGroup):
    waiting_meal_type = State()


def _parse(text: str):
    """Parse 'product 150' or '150 product'. Returns (product, weight) or None."""
    text = text.strip()
    for i, pat in enumerate([
        r'^(.+?)\s+(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|g|gram)?$',
        r'^(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|g|gram)?\s+(.+)$',
    ]):
        m = re.match(pat, text, re.IGNORECASE)
        if m:
            prod = m.group(1).strip() if i == 0 else m.group(2).strip()
            ws   = m.group(2)         if i == 0 else m.group(1)
            w = float(ws.replace(",", "."))
            if 0 < w <= 10000 and len(prod) >= 2:
                return prod, w
    return None


async def _get_or_create_user(uid: int, session) -> User:
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


@router.message(F.text & ~F.text.startswith("/"))
async def handle_food_text(message: Message, state: FSMContext) -> None:
    parsed = _parse(message.text)

    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language

    if not parsed:
        await message.answer(t("format_hint", lang), parse_mode="Markdown")
        return

    product, weight = parsed
    processing = await message.answer(
        t("processing", lang, product=product), parse_mode="Markdown"
    )

    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        result = await resolve(product, weight, session)

    if not result:
        await processing.edit_text(
            t("not_found", lang, product=product), parse_mode="Markdown"
        )
        return

    await state.update_data(nutrition={
        "product_name": result.product_name,
        "grams":        result.grams,
        "calories":     result.calories,
        "protein":      result.protein,
        "fat":          result.fat,
        "carbs":        result.carbs,
    })
    await state.set_state(FoodState.waiting_meal_type)

    await processing.edit_text(
        f"✅ *{result.product_name}* — {result.grams:.0f}г\n"
        f"🔥 {result.calories:.0f} ккал | 💪 Б {result.protein:.1f}г | "
        f"🧈 Ж {result.fat:.1f}г | 🍞 У {result.carbs:.1f}г\n\n"
        + t("ask_meal_type", lang),
        parse_mode="Markdown",
        reply_markup=meal_type_keyboard(lang),
    )


@router.callback_query(FoodState.waiting_meal_type,
                       lambda c: c.data and c.data.startswith("meal_type:"))
async def save_meal_type(callback: CallbackQuery, state: FSMContext) -> None:
    meal_type = callback.data.split(":")[1]
    data      = await state.get_data()
    nutrition = data.get("nutrition", {})

    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(callback.from_user.id, session)
        lang = user.language

        from datetime import date
        meal = Meal(
            user_id      = user.id,
            product_name = nutrition["product_name"],
            grams        = nutrition["grams"],
            calories     = nutrition["calories"],
            protein      = nutrition["protein"],
            fat          = nutrition["fat"],
            carbs        = nutrition["carbs"],
            meal_type    = meal_type,
            date         = date.today(),
        )
        session.add(meal)
        await session.commit()

    await state.clear()

    meal_label = t(meal_type, lang)
    await callback.message.edit_text(
        t("meal_saved", lang,
          product   = nutrition["product_name"],
          grams     = nutrition["grams"],
          calories  = nutrition["calories"],
          protein   = nutrition["protein"],
          fat       = nutrition["fat"],
          carbs     = nutrition["carbs"],
          meal_type = meal_label),
        parse_mode="Markdown",
    )
    await callback.answer()
