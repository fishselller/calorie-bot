import re
from datetime import date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Meal
from app.keyboards.inline import meal_type_keyboard
from app.keyboards.reply import main_menu
from app.localization.texts import t
from app.services.nutrition import resolve

router = Router()

ADD_TEXTS = {"➕ Добавить продукт", "➕ Додати продукт", "➕ Add product"}
REPORT_TEXTS = {"📊 Отчёт за сегодня", "📊 Звіт за сьогодні", "📊 Today's report"}


class FoodState(StatesGroup):
    waiting_product   = State()
    waiting_meal_type = State()


def _parse(text: str):
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


@router.message(F.text.in_(ADD_TEXTS))
async def ask_product(message: Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language
    await state.set_state(FoodState.waiting_product)
    hints = {
        "ru": "Напиши продукт и вес:\n`банан 150`\n`куриная грудка 200г`",
        "uk": "Напиши продукт та вагу:\n`банан 150`\n`куряча грудка 200г`",
        "en": "Write product and weight:\n`banana 150`\n`chicken breast 200g`",
    }
    await message.answer(hints.get(lang, hints["ru"]), parse_mode="Markdown")


@router.message(FoodState.waiting_product)
async def handle_product_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _process_food(message)


@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(ADD_TEXTS) & ~F.text.in_(REPORT_TEXTS))
async def handle_food_text(message: Message, state: FSMContext) -> None:
    # Skip if in photo state
    current = await state.get_state()
    if current is not None:
        return
    await _process_food(message)


async def _process_food(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language

    parsed = _parse(message.text)
    if not parsed:
        await message.answer(t("format_hint", lang), parse_mode="Markdown")
        return

    product, weight = parsed
    processing = await message.answer(
        t("processing", lang, product=product), parse_mode="Markdown"
    )

    async with AsyncSessionLocal() as session:
        user   = await _get_or_create_user(message.from_user.id, session)
        result = await resolve(product, weight, session)

    if not result:
        await processing.edit_text(
            t("not_found", lang, product=product), parse_mode="Markdown"
        )
        return

    # Store in dispatcher storage via bot data workaround
    if not hasattr(message.bot, '_pending'):
        message.bot._pending = {}
    message.bot._pending[message.from_user.id] = {
        "product_name": result.product_name,
        "grams":        result.grams,
        "calories":     result.calories,
        "protein":      result.protein,
        "fat":          result.fat,
        "carbs":        result.carbs,
        "lang":         lang,
    }

    await processing.edit_text(
        f"✅ *{result.product_name}* — {result.grams:.0f}г\n"
        f"🔥 {result.calories:.0f} ккал | 💪 Б {result.protein:.1f}г | "
        f"🧈 Ж {result.fat:.1f}г | 🍞 У {result.carbs:.1f}г\n\n"
        + t("ask_meal_type", lang),
        parse_mode="Markdown",
        reply_markup=meal_type_keyboard(lang),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("meal_type:"))
async def save_meal_type(callback: CallbackQuery, state: FSMContext) -> None:
    meal_type = callback.data.split(":")[1]

    # Get pending from bot attribute
    pending = getattr(callback.bot, '_pending', {})
    nutrition = pending.pop(callback.from_user.id, None)

    if not nutrition:
        await callback.answer("Попробуй снова")
        return

    lang = nutrition.get("lang", "ru")

    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(callback.from_user.id, session)
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

    await callback.message.edit_text(
        t("meal_saved", lang,
          product   = nutrition["product_name"],
          grams     = nutrition["grams"],
          calories  = nutrition["calories"],
          protein   = nutrition["protein"],
          fat       = nutrition["fat"],
          carbs     = nutrition["carbs"],
          meal_type = t(meal_type, lang)),
        parse_mode="Markdown",
    )
    await callback.answer()
