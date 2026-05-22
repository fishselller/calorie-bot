from datetime import date

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Meal
from app.keyboards.inline import report_keyboard
from app.localization.texts import t
from app.services.report import build_report

router = Router()


async def _get_or_create_user(uid: int, session) -> User:
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


@router.message(Command("report"))
@router.message(F.text.in_({
    "📊 Отчёт за сегодня", "📊 Звіт за сьогодні", "📊 Today's report"
}))
async def cmd_report(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language
    await message.answer(
        t("choose_report_period", lang),
        reply_markup=report_keyboard(lang),
    )


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        text = await build_report(user, session, meal_type="full")
    await message.answer(text, parse_mode="Markdown")


@router.callback_query(lambda c: c.data and c.data.startswith("report:"))
async def show_report(callback: CallbackQuery) -> None:
    meal_type = callback.data.split(":")[1]
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(callback.from_user.id, session)
        text = await build_report(user, session, meal_type=meal_type)
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


@router.message(Command("undo"))
async def cmd_undo(message: Message) -> None:
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language
        stmt = (
            select(Meal)
            .where(Meal.user_id == user.id, Meal.date == date.today())
            .order_by(Meal.created_at.desc())
            .limit(1)
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row:
            await session.delete(row)
            await session.commit()
            await message.answer(t("undo_ok", lang))
        else:
            await message.answer(t("undo_empty", lang))
