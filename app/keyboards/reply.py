from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    texts = {
        "ru": ["📊 Отчёт за сегодня", "📅 Неделя", "⚖️ Вес", "⚙️ Моя норма", "❓ Как я работаю"],
        "uk": ["📊 Звіт за сьогодні", "📅 Тиждень", "⚖️ Вага", "⚙️ Моя норма", "❓ Як я працюю"],
        "en": ["📊 Today's report",   "📅 Week",    "⚖️ Weight", "⚙️ My norm", "❓ How I work"],
    }
    t = texts.get(lang, texts["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t[0]), KeyboardButton(text=t[1])],
            [KeyboardButton(text=t[2]), KeyboardButton(text=t[3])],
            [KeyboardButton(text=t[4])],
        ],
        resize_keyboard=True,
        persistent=True,
    )
