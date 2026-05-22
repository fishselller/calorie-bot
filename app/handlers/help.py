from aiogram import Router, F
from aiogram.types import Message

from app.db.engine import AsyncSessionLocal
from app.db.models import User

router = Router()

HELP_TEXTS = {
    "ru": """❓ *Как я работаю*

*Добавить еду текстом:*
Напиши название и вес — я посчитаю БЖУ на основе средних показателей продукта
Например:
`Куриная грудка 200 г`
`Овсянка 150 г`
`Банан 120 г`

*Добавить еду по фото:*
Сфотографируй упаковку так, чтобы было видно БЖУ → я считываю питательную ценность на 100 г → ты называешь продукт → вводишь вес

После этого продукт сохраняется и в следующий раз фото уже не нужно — просто напиши название и вес, например:
`хлеб тостовый 40г` → и я автоматически посчитаю БЖУ

*После добавления* выбери приём пищи:
🍳 Завтрак / 🍲 Обед / 🍖 Ужин / 🍎 Перекус

*Отчёт:*
Нажми 📊 *Отчёт за сегодня* — увидишь все приёмы пищи и итог

*Автоматически:*
☀️ 07:00 — утреннее напоминание
🍲 15:00 — напоминание добавить обед _(только если обед ещё не внесён)_
🍖 18:00 — напоминание добавить ужин _(только если ужин ещё не внесён)_
🌙 21:00 — дневной отчёт

*Команды:*
/today — отчёт за сегодня
/undo — удалить последнюю запись""",

    "uk": """❓ *Як я працюю*

*Додати їжу:*
Напиши назву та вагу — я порахую БЖУ на основі середніх показників цього продукту
Наприклад:
`Куряча грудка 200 г`
`Вівсянка 150 г`
`Банан 120 г`

*Додати їжу за фото:*
Сфотографуй упаковку так, щоб було видно БЖУ → я зчитую поживну цінність на 100 г продукту → ти називаєш продукт → вводиш вагу

Після цього продукт зберігається і наступного разу фото вже не потрібне — просто напиши назву продукту та вагу, наприклад:
`хліб тостовий 40г` → і я автоматично порахую БЖУ

*Після додавання* обери прийом їжі:
🍳 Сніданок / 🍲 Обід / 🍖 Вечеря / 🍎 Перекус

*Звіт:*
Натисни 📊 *Звіт за сьогодні* — побачиш усі прийоми їжі та підсумок

*Автоматично:*
☀️ 07:00 — ранкове нагадування
🍲 15:00 — нагадування додати обід _(лише якщо обід ще не внесено)_
🍖 18:00 — нагадування додати вечерю _(лише якщо вечерю ще не внесено)_
🌙 21:00 — денний звіт

*Команди:*
/today — звіт за сьогодні
/undo — видалити останній запис""",

    "en": """❓ *How I work*

*Add food by text:*
Write name and weight — I'll calculate macros based on average values
For example:
`Chicken breast 200 g`
`Oatmeal 150 g`
`Banana 120 g`

*Add food by photo:*
Photo the packaging so nutrition label is visible → I read nutrition per 100g → you name the product → enter weight

The product is saved and next time no photo needed — just write name and weight, e.g.:
`toast bread 40g` → I'll calculate macros automatically

*After adding* choose meal type:
🍳 Breakfast / 🍲 Lunch / 🍖 Dinner / 🍎 Snack

*Report:*
Tap 📊 *Today's report* — see all meals and daily totals

*Automatic:*
☀️ 07:00 — morning reminder
🍲 15:00 — lunch reminder _(only if lunch not logged yet)_
🍖 18:00 — dinner reminder _(only if dinner not logged yet)_
🌙 21:00 — daily report

*Commands:*
/today — today's report
/undo — delete last entry""",
}

HOW_BUTTONS = {"❓ Как я работаю", "❓ Як я працюю", "❓ How I work"}


async def _get_lang(uid: int) -> str:
    async with AsyncSessionLocal() as session:
        user = await session.get(User, uid)
        return user.language if user else "ru"


@router.message(F.text.in_(HOW_BUTTONS))
async def show_help(message: Message) -> None:
    lang = await _get_lang(message.from_user.id)
    await message.answer(HELP_TEXTS.get(lang, HELP_TEXTS["ru"]), parse_mode="Markdown")
