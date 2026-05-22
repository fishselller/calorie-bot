from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    texts = {
        "ru": ["📊 Отчёт за сегодня", "📅 Неделя", "⚙️ Моя норма", "❓ Как я работаю"],
        "uk": ["📊 Звіт за сьогодні", "📅 Тиждень", "⚙️ Моя норма", "❓ Як я працюю"],
        "en": ["📊 Today's report",   "📅 Week",     "⚙️ My norm",   "❓ How I work"],
    }
    t = texts.get(lang, texts["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t[0]), KeyboardButton(text=t[1])],
            [KeyboardButton(text=t[2]), KeyboardButton(text=t[3])],
        ],
        resize_keyboard=True,
        persistent=True,
    )
