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
        if user and user.language:
            lang = user.language
            greet = {
                "ru": "👋 Привет! Я считаю калории и БЖУ.",
                "uk": "👋 Привіт! Я рахую калорії та БЖУ.",
                "en": "👋 Hello! I track calories and macros.",
            }
            await message.answer(
                greet.get(lang, greet["ru"]),
                reply_markup=main_menu(lang),
            )
            return

    await message.answer(
        "👋 Привіт! Обери мову / Привет! Выбери язык:",
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

    greet = {
        "ru": "✅ Язык: Русский 🇷🇺\n\nЯ считаю калории и БЖУ.",
        "uk": "✅ Мова: Українська 🇺🇦\n\nЯ рахую калорії та БЖУ.",
        "en": "✅ Language: English 🇬🇧\n\nI track calories and macros.",
    }

    await callback.message.edit_text(greet.get(lang, greet["ru"]))
    await callback.message.answer("👇", reply_markup=main_menu(lang))
    await callback.answer()
