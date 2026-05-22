from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.db.engine import AsyncSessionLocal
from app.db.models import User
from app.keyboards.inline import language_keyboard
from app.keyboards.reply import main_menu
from app.localization.texts import t

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        # If user already has language — go straight to menu
        if user and user.language:
            lang = user.language
            await message.answer(
                t("language_set", lang),
                parse_mode="Markdown",
                reply_markup=main_menu(lang),
            )
            return

    await message.answer(
        t("choose_language", "ru"),
        reply_markup=language_keyboard(),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def set_language(callback: CallbackQuery) -> None:
    lang = callback.data.split(":")[1]
    uid  = callback.from_user.id

    async with AsyncSessionLocal() as session:
        user = await session.get(User, uid)
        if user is None:
            user = User(id=uid, language=lang)
            session.add(user)
        else:
            user.language = lang
        await session.commit()

    await callback.message.edit_text(
        t("language_set", lang), parse_mode="Markdown"
    )
    # Send menu as new message
    await callback.message.answer(
        "👇",
        reply_markup=main_menu(lang),
    )
    await callback.answer()
