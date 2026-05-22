from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.localization import t


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский",    callback_data="lang:ru")
    builder.button(text="🇺🇦 Українська", callback_data="lang:uk")
    builder.button(text="🇬🇧 English",    callback_data="lang:en")
    builder.adjust(1)
    return builder.as_markup()


def meal_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for meal_id in ("breakfast", "lunch", "dinner", "snack"):
        builder.button(text=t(meal_id, lang), callback_data=f"meal_type:{meal_id}")
    builder.adjust(2)
    return builder.as_markup()


def report_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for meal_id in ("breakfast", "lunch", "dinner", "snack"):
        builder.button(text=t(meal_id, lang), callback_data=f"report:{meal_id}")
    builder.button(text=t("full_day", lang), callback_data="report:full")
    builder.adjust(2)
    return builder.as_markup()


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("full_day", lang), callback_data="report:full")
    builder.adjust(1)
    return builder.as_markup()
