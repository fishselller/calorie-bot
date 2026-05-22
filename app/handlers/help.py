from aiogram import Router, F
from aiogram.types import Message

from app.db.engine import AsyncSessionLocal
from app.db.models import User

router = Router()

HELP_TEXTS = {
    "ru": """❓ *Как я работаю*

*Добавить еду текстом:*
Напиши название и вес — я посчитаю БЖУ
`куриная грудка 200`
`овсянка 150г`
`банан 120`

*Добавить еду по фото:*
Отправь фото упаковки → я считаю БЖУ → ты называешь продукт → вводишь вес

*После добавления* выбери приём пищи:
🍳 Завтрак / 🍲 Обед / 🍖 Ужин / 🍎 Перекус

*Отчёт:*
Нажми 📊 *Отчёт за сегодня* — увидишь все приёмы пищи и итог по калориям

*Автоматически:*
☀️ 07:00 — утреннее напоминание
🌙 21:00 — дневной отчёт

*Команды:*
/today — отчёт за сегодня
/undo — удалить последнюю запись""",

    "uk": """❓ *Як я працюю*

*Додати їжу текстом:*
Напиши назву та вагу — я порахую БЖУ
`куряча грудка 200`
`вівсянка 150г`
`банан 120`

*Додати їжу за фото:*
Надішли фото упаковки → я зчитую БЖУ → ти називаєш продукт → вводиш вагу

*Після додавання* обери прийом їжі:
🍳 Сніданок / 🍲 Обід / 🍖 Вечеря / 🍎 Перекус

*Звіт:*
Натисни 📊 *Звіт за сьогодні* — побачиш усі прийоми їжі та підсумок

*Автоматично:*
☀️ 07:00 — ранкове нагадування
🌙 21:00 — денний звіт

*Команди:*
/today — звіт за сьогодні
/undo — видалити останній запис""",

    "en": """❓ *How I work*

*Add food by text:*
Write name and weight — I'll calculate macros
`chicken breast 200`
`oatmeal 150g`
`banana 120`

*Add food by photo:*
Send packaging photo → I read nutrition → you name the product → enter weight

*After adding* choose meal type:
🍳 Breakfast / 🍲 Lunch / 🍖 Dinner / 🍎 Snack

*Report:*
Tap 📊 *Today's report* — see all meals and daily totals

*Automatic:*
☀️ 07:00 — morning reminder
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
