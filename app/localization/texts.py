from typing import Dict

TEXTS: Dict[str, Dict[str, str]] = {
    # ── welcome / start ────────────────────────────────────────────────────────
    "choose_language": {
        "ru": "Привет! 👋 Выбери язык:",
        "uk": "Привіт! 👋 Обери мову:",
        "en": "Hello! 👋 Choose your language:",
    },
    "language_set": {
        "ru": "Язык установлен: Русский 🇷🇺\n\nЯ помогу считать калории и БЖУ!\n\nПросто напиши название продукта и вес, например:\n`банан 150`\n`овсянка 200`\n`куриная грудка 180г`",
        "uk": "Мову встановлено: Українська 🇺🇦\n\nЯ допоможу рахувати калорії та БЖУ!\n\nПросто напиши назву продукту та вагу, наприклад:\n`банан 150`\n`вівсянка 200`\n`куряча грудка 180г`",
        "en": "Language set: English 🇬🇧\n\nI'll help you track calories and macros!\n\nJust type a food name and weight, e.g.:\n`banana 150`\n`oatmeal 200`\n`chicken breast 180g`",
    },
    # ── meal type ──────────────────────────────────────────────────────────────
    "ask_meal_type": {
        "ru": "К какому приёму пищи это относится?",
        "uk": "До якого прийому їжі це відноситься?",
        "en": "Which meal does this belong to?",
    },
    "meal_saved": {
        "ru": "✅ *{product}* — {grams:.0f}г\n🔥 {calories:.0f} ккал | 💪 Б {protein:.1f}г | 🧈 Ж {fat:.1f}г | 🍞 У {carbs:.1f}г\n\nЗаписано в: *{meal_type}*",
        "uk": "✅ *{product}* — {grams:.0f}г\n🔥 {calories:.0f} ккал | 💪 Б {protein:.1f}г | 🧈 Ж {fat:.1f}г | 🍞 У {carbs:.1f}г\n\nЗаписано до: *{meal_type}*",
        "en": "✅ *{product}* — {grams:.0f}g\n🔥 {calories:.0f} kcal | 💪 P {protein:.1f}g | 🧈 F {fat:.1f}g | 🍞 C {carbs:.1f}g\n\nSaved to: *{meal_type}*",
    },
    # ── meal type names ────────────────────────────────────────────────────────
    "breakfast": {"ru": "🍳 Завтрак", "uk": "🍳 Сніданок", "en": "🍳 Breakfast"},
    "lunch":     {"ru": "🍲 Обед",    "uk": "🍲 Обід",     "en": "🍲 Lunch"},
    "dinner":    {"ru": "🍖 Ужин",    "uk": "🍖 Вечеря",   "en": "🍖 Dinner"},
    "snack":     {"ru": "🍎 Перекус", "uk": "🍎 Перекус",  "en": "🍎 Snack"},
    # ── report ─────────────────────────────────────────────────────────────────
    "report_title": {
        "ru": "📊 *Отчёт за {date}*",
        "uk": "📊 *Звіт за {date}*",
        "en": "📊 *Report for {date}*",
    },
    "report_empty": {
        "ru": "За этот период ничего не записано.",
        "uk": "За цей період нічого не записано.",
        "en": "Nothing recorded for this period.",
    },
    "report_total": {
        "ru": "━━━━━━━━━━━━━━━\n📊 *ИТОГО:*\n🔥 {calories:.0f} ккал\n💪 Белки: {protein:.1f}г\n🧈 Жиры: {fat:.1f}г\n🍞 Углеводы: {carbs:.1f}г",
        "uk": "━━━━━━━━━━━━━━━\n📊 *РАЗОМ:*\n🔥 {calories:.0f} ккал\n💪 Білки: {protein:.1f}г\n🧈 Жири: {fat:.1f}г\n🍞 Вуглеводи: {carbs:.1f}г",
        "en": "━━━━━━━━━━━━━━━\n📊 *TOTAL:*\n🔥 {calories:.0f} kcal\n💪 Protein: {protein:.1f}g\n🧈 Fat: {fat:.1f}g\n🍞 Carbs: {carbs:.1f}g",
    },
    "choose_report_period": {
        "ru": "Выбери период отчёта:",
        "uk": "Обери період звіту:",
        "en": "Choose report period:",
    },
    "full_day": {
        "ru": "📊 Полный день",
        "uk": "📊 Повний день",
        "en": "📊 Full day",
    },
    # ── morning / evening notifications ────────────────────────────────────────
    "morning": {
        "ru": "☀️ Доброе утро! Не забудь начать подсчёт калорий, хорошего тебе дня! 😊",
        "uk": "☀️ Доброго ранку! Не забудь почати підрахунок калорій, гарного тобі дня! 😊",
        "en": "☀️ Good morning! Don't forget to start tracking your calories today! 😊",
    },
    # ── errors / misc ──────────────────────────────────────────────────────────
    "not_found": {
        "ru": "❌ Не удалось найти *{product}*. Попробуй написать иначе.",
        "uk": "❌ Не вдалося знайти *{product}*. Спробуй написати інакше.",
        "en": "❌ Could not find *{product}*. Try a different spelling.",
    },
    "processing": {
        "ru": "🔍 Считаю *{product}*...",
        "uk": "🔍 Рахую *{product}*...",
        "en": "🔍 Looking up *{product}*...",
    },
    "format_hint": {
        "ru": "🤔 Напиши продукт и вес, например:\n`банан 150`\n`куриная грудка 200г`\n`гречка 250`",
        "uk": "🤔 Напиши продукт та вагу, наприклад:\n`банан 150`\n`куряча грудка 200г`\n`гречка 250`",
        "en": "🤔 Write food name and weight, e.g.:\n`banana 150`\n`chicken breast 200g`\n`oatmeal 250`",
    },
    "undo_ok": {
        "ru": "✅ Последняя запись удалена!",
        "uk": "✅ Останній запис видалено!",
        "en": "✅ Last entry deleted!",
    },
    "undo_empty": {
        "ru": "Нечего удалять.",
        "uk": "Нічого видаляти.",
        "en": "Nothing to delete.",
    },
    "photo_processing": {
        "ru": "📸 Анализирую фото упаковки...",
        "uk": "📸 Аналізую фото упаковки...",
        "en": "📸 Analysing packaging photo...",
    },
    "photo_ok": {
        "ru": "✅ Продукт распознан! Теперь напиши вес, например: `{name} 150`",
        "uk": "✅ Продукт розпізнано! Тепер напиши вагу, наприклад: `{name} 150`",
        "en": "✅ Product recognised! Now enter weight, e.g.: `{name} 150`",
    },
    "photo_fail": {
        "ru": "❌ Не удалось распознать данные с фото. Введи продукт вручную.",
        "uk": "❌ Не вдалося розпізнати дані з фото. Введи продукт вручну.",
        "en": "❌ Could not read nutrition data from photo. Enter product manually.",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    """Get localised text. Falls back to Russian."""
    lang = lang if lang in ("ru", "uk", "en") else "ru"
    template = TEXTS.get(key, {}).get(lang) or TEXTS.get(key, {}).get("ru", key)
    return template.format(**kwargs) if kwargs else template
