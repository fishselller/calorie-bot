from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    texts = {
        "ru": ["📊 Отчёт за сегодня", "➕ Добавить продукт"],
        "uk": ["📊 Звіт за сьогодні", "➕ Додати продукт"],
        "en": ["📊 Today's report",   "➕ Add product"],
    }
    t = texts.get(lang, texts["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t[0])], [KeyboardButton(text=t[1])]],
        resize_keyboard=True,
        persistent=True,
    )
