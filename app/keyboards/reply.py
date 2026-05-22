from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    texts = {
        "ru": ["📊 Отчёт за сегодня", "❓ Как я работаю"],
        "uk": ["📊 Звіт за сьогодні", "❓ Як я працюю"],
        "en": ["📊 Today's report",   "❓ How I work"],
    }
    t = texts.get(lang, texts["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t[0])], [KeyboardButton(text=t[1])]],
        resize_keyboard=True,
        persistent=True,
    )
