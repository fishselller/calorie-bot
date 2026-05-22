from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.engine import AsyncSessionLocal
from app.db.models import User

router = Router()

NORM_BUTTONS = {"⚙️ Моя норма", "⚙️ My norm"}


class NormState(StatesGroup):
    calories = State()
    protein  = State()
    fat      = State()
    carbs    = State()


async def _get_or_create_user(uid, session):
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


async def _start_norm(message: Message, state: FSMContext, lang: str) -> None:
    # Show current norm if exists
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        current = ""
        if user.cal_norm:
            current_texts = {
                "ru": f"\n\n*Текущая норма:*\n🔥 {user.cal_norm:.0f} ккал | 💪 {user.prot_norm:.0f}г Б | 🧈 {user.fat_norm:.0f}г Ж | 🍞 {user.carb_norm:.0f}г У\n",
                "uk": f"\n\n*Поточна норма:*\n🔥 {user.cal_norm:.0f} ккал | 💪 {user.prot_norm:.0f}г Б | 🧈 {user.fat_norm:.0f}г Ж | 🍞 {user.carb_norm:.0f}г У\n",
                "en": f"\n\n*Current norm:*\n🔥 {user.cal_norm:.0f} kcal | 💪 {user.prot_norm:.0f}g P | 🧈 {user.fat_norm:.0f}g F | 🍞 {user.carb_norm:.0f}g C\n",
            }
            current = current_texts.get(lang, current_texts["ru"])

    texts = {
        "ru": f"⚙️ *Дневная норма*{current}\nВведи норму *калорий* (например: `2000`):",
        "uk": f"⚙️ *Денна норма*{current}\nВведи норму *калорій* (наприклад: `2000`):",
        "en": f"⚙️ *Daily norm*{current}\nEnter *calories* norm (e.g.: `2000`):",
    }
    await state.set_state(NormState.calories)
    await state.update_data(lang=lang)
    await message.answer(texts.get(lang, texts["ru"]), parse_mode="Markdown")


@router.message(Command("norm"))
async def cmd_norm(message: Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language
    await _start_norm(message, state, lang)


@router.message(F.text.in_(NORM_BUTTONS))
async def btn_norm(message: Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language
    await _start_norm(message, state, lang)


@router.message(NormState.calories)
async def get_calories(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        val = float(message.text.strip().replace(",", "."))
        if val <= 0 or val > 10000:
            raise ValueError
    except ValueError:
        await message.answer("Введи число, например: `2000`", parse_mode="Markdown")
        return
    await state.update_data(calories=val)
    await state.set_state(NormState.protein)
    texts = {
        "ru": f"✅ Калории: *{val:.0f}*\n\nТеперь норма *белков* (г, например: `150`):",
        "uk": f"✅ Калорії: *{val:.0f}*\n\nТепер норма *білків* (г, наприклад: `150`):",
        "en": f"✅ Calories: *{val:.0f}*\n\nNow *protein* norm (g, e.g.: `150`):",
    }
    await message.answer(texts.get(lang, texts["ru"]), parse_mode="Markdown")


@router.message(NormState.protein)
async def get_protein(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        val = float(message.text.strip().replace(",", "."))
        if val <= 0 or val > 1000:
            raise ValueError
    except ValueError:
        await message.answer("Введи число, например: `150`", parse_mode="Markdown")
        return
    await state.update_data(protein=val)
    await state.set_state(NormState.fat)
    texts = {
        "ru": f"✅ Белки: *{val:.0f}г*\n\nТеперь норма *жиров* (г, например: `65`):",
        "uk": f"✅ Білки: *{val:.0f}г*\n\nТепер норма *жирів* (г, наприклад: `65`):",
        "en": f"✅ Protein: *{val:.0f}g*\n\nNow *fat* norm (g, e.g.: `65`):",
    }
    await message.answer(texts.get(lang, texts["ru"]), parse_mode="Markdown")


@router.message(NormState.fat)
async def get_fat(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        val = float(message.text.strip().replace(",", "."))
        if val <= 0 or val > 1000:
            raise ValueError
    except ValueError:
        await message.answer("Введи число, например: `65`", parse_mode="Markdown")
        return
    await state.update_data(fat=val)
    await state.set_state(NormState.carbs)
    texts = {
        "ru": f"✅ Жиры: *{val:.0f}г*\n\nТеперь норма *углеводов* (г, например: `250`):",
        "uk": f"✅ Жири: *{val:.0f}г*\n\nТепер норма *вуглеводів* (г, наприклад: `250`):",
        "en": f"✅ Fat: *{val:.0f}g*\n\nNow *carbs* norm (g, e.g.: `250`):",
    }
    await message.answer(texts.get(lang, texts["ru"]), parse_mode="Markdown")


@router.message(NormState.carbs)
async def get_carbs(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        val = float(message.text.strip().replace(",", "."))
        if val <= 0 or val > 2000:
            raise ValueError
    except ValueError:
        await message.answer("Введи число, например: `250`", parse_mode="Markdown")
        return

    cal  = data["calories"]
    prot = data["protein"]
    fat  = data["fat"]

    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        user.cal_norm  = cal
        user.prot_norm = prot
        user.fat_norm  = fat
        user.carb_norm = val
        await session.commit()

    await state.clear()

    texts = {
        "ru": (f"✅ *Норма сохранена!*\n\n"
               f"🔥 Калории: *{cal:.0f} ккал*\n"
               f"💪 Белки: *{prot:.0f} г*\n"
               f"🧈 Жиры: *{fat:.0f} г*\n"
               f"🍞 Углеводы: *{val:.0f} г*\n\n"
               f"Теперь в отчёте будет прогресс-бар! 📊"),
        "uk": (f"✅ *Норму збережено!*\n\n"
               f"🔥 Калорії: *{cal:.0f} ккал*\n"
               f"💪 Білки: *{prot:.0f} г*\n"
               f"🧈 Жири: *{fat:.0f} г*\n"
               f"🍞 Вуглеводи: *{val:.0f} г*\n\n"
               f"Тепер у звіті буде прогрес-бар! 📊"),
        "en": (f"✅ *Norm saved!*\n\n"
               f"🔥 Calories: *{cal:.0f} kcal*\n"
               f"💪 Protein: *{prot:.0f} g*\n"
               f"🧈 Fat: *{fat:.0f} g*\n"
               f"🍞 Carbs: *{val:.0f} g*\n\n"
               f"Now your report will have a progress bar! 📊"),
    }
    await message.answer(texts.get(lang, texts["ru"]), parse_mode="Markdown")
