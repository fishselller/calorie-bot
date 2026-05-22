from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date
from sqlalchemy import select

from app.db.engine import AsyncSessionLocal
from app.db.models import User, WeightLog

router = Router()

WEIGHT_BUTTONS = {"⚖️ Вес", "⚖️ Вага", "⚖️ Weight"}


class WeightState(StatesGroup):
    waiting_weight = State()


async def _get_or_create_user(uid, session):
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


@router.message(Command("weight"))
@router.message(F.text.in_(WEIGHT_BUTTONS))
async def cmd_weight(message: Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language

        # Get last 5 entries
        logs = (await session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user.id)
            .order_by(WeightLog.date.desc())
            .limit(5)
        )).scalars().all()

    history = ""
    if logs:
        lines = []
        for log in reversed(logs):
            lines.append(f"  {log.date.strftime('%d.%m')} — *{log.weight:.1f} кг*")
        hist_label = {"ru": "📈 *История:*", "uk": "📈 *Історія:*", "en": "📈 *History:*"}
        history = f"\n\n{hist_label.get(lang, hist_label['ru'])}\n" + "\n".join(lines)

        # Show trend
        if len(logs) >= 2:
            diff = logs[0].weight - logs[-1].weight
            if diff < 0:
                trend = f"📉 {abs(diff):.1f} кг за период"
            elif diff > 0:
                trend = f"📈 +{diff:.1f} кг за период"
            else:
                trend = "➡️ Вес стабильный"
            history += f"\n{trend}"

    texts = {
        "ru": f"⚖️ *Дневник веса*{history}\n\nВведи свой текущий вес (кг):\nНапример: `75.5`",
        "uk": f"⚖️ *Щоденник ваги*{history}\n\nВведи свою поточну вагу (кг):\nНаприклад: `75.5`",
        "en": f"⚖️ *Weight diary*{history}\n\nEnter your current weight (kg):\nE.g.: `75.5`",
    }
    await state.set_state(WeightState.waiting_weight)
    await state.update_data(lang=lang)
    await message.answer(texts.get(lang, texts["ru"]), parse_mode="Markdown")


@router.message(WeightState.waiting_weight)
async def save_weight(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")

    try:
        weight = float(message.text.strip().replace(",", "."))
        if weight <= 0 or weight > 300:
            raise ValueError
    except ValueError:
        await message.answer("Введи вес числом, например: `75.5`", parse_mode="Markdown")
        return

    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)

        # Check if already logged today
        existing = (await session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user.id, WeightLog.date == date.today())
        )).scalar_one_or_none()

        if existing:
            existing.weight = weight
        else:
            session.add(WeightLog(user_id=user.id, weight=weight, date=date.today()))
        await session.commit()

        # Get previous entry for comparison
        prev = (await session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user.id, WeightLog.date < date.today())
            .order_by(WeightLog.date.desc())
            .limit(1)
        )).scalar_one_or_none()

    diff_str = ""
    if prev:
        diff = weight - prev.weight
        if diff < 0:
            diff_str = f"\n📉 -{abs(diff):.1f} кг с прошлого раза"
        elif diff > 0:
            diff_str = f"\n📈 +{diff:.1f} кг с прошлого раза"
        else:
            diff_str = "\n➡️ Вес не изменился"

    texts = {
        "ru": f"✅ Записано: *{weight:.1f} кг*{diff_str}\n\n_Каждое воскресенье в 20:00 я напомню взвеситься!_",
        "uk": f"✅ Записано: *{weight:.1f} кг*{diff_str}\n\n_Щонеділі о 20:00 я нагадаю зважитися!_",
        "en": f"✅ Saved: *{weight:.1f} kg*{diff_str}\n\n_Every Sunday at 20:00 I'll remind you to weigh in!_",
    }
    await message.answer(texts.get(lang, texts["ru"]), parse_mode="Markdown")
