import asyncio
import logging
import json
import os
from datetime import datetime, date
import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import aiosqlite
import re
import urllib.request

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8911085987:AAGeZYdvsZlz3j_YDT30RhASI2dIKDUYLWc"
GEMINI_API_KEY = "AIzaSyC_C67WdsZ02aJ7vkACjAvHFksiyGB2YuA"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
KYIV_TZ = pytz.timezone("Europe/Kyiv")
DB_PATH = "calories.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ─── DATABASE ─────────────────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                calories REAL,
                protein REAL,
                fat REAL,
                carbs REAL,
                weight REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT
            )
        """)
        await db.commit()

async def save_user(user_id, username, first_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

async def save_meal(user_id, description, calories, protein, fat, carbs, weight):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO meals (user_id, date, description, calories, protein, fat, carbs, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, today, description, calories, protein, fat, carbs, weight)
        )
        await db.commit()

async def delete_last_meal(user_id):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM meals WHERE user_id=? AND date=? ORDER BY created_at DESC LIMIT 1",
            (user_id, today)
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            await db.execute("DELETE FROM meals WHERE id=?", (row[0],))
            await db.commit()
            return True
        return False

async def get_today_meals(user_id):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT description, calories, protein, fat, carbs, weight FROM meals WHERE user_id=? AND date=? ORDER BY created_at",
            (user_id, today)
        ) as cursor:
            return await cursor.fetchall()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return [row[0] for row in await cursor.fetchall()]

# ─── GEMINI (без поиска — встроенные знания) ──────────────────────────────────
def ask_gemini(prompt):
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 500}
    }).encode("utf-8")
    req = urllib.request.Request(
        GEMINI_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                return part["text"]
    return ""

def search_and_calculate(product_name, weight_grams):
    prompt = f"""Ты эксперт по питанию. Дай точные данные о калорийности и БЖУ продукта на 100г.

Продукт: "{product_name}"
Вес порции: {weight_grams}г

Используй стандартные значения (как в USDA или calorizator.ru).
Рассчитай для {weight_grams}г.

Ответь ТОЛЬКО в формате JSON, без лишнего текста, без markdown:
{{"product_name": "название продукта", "per_100g": {{"calories": число, "protein": число, "fat": число, "carbs": число}}, "for_weight": {{"calories": число, "protein": число, "fat": число, "carbs": число}}, "source": "USDA / calorizator.ru"}}"""

    text = ask_gemini(prompt)
    text = text.strip().replace("```json", "").replace("```", "").strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        text = m.group()
    return json.loads(text)

# ─── PARSE ────────────────────────────────────────────────────────────────────
def parse_user_message(text):
    text = text.strip()
    patterns = [
        r'^(.+?)\s+(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|g|gram)?$',
        r'^(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|g|gram)?\s+(.+)$',
    ]
    for i, pattern in enumerate(patterns):
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            if i == 0:
                product, ws = match.group(1).strip(), match.group(2)
            else:
                ws, product = match.group(1), match.group(2).strip()
            weight = float(ws.replace(",", "."))
            if 0 < weight <= 10000 and len(product) >= 2:
                return {"product": product, "weight": weight}
    return None

# ─── REPORT ───────────────────────────────────────────────────────────────────
async def send_daily_report(user_id):
    meals = await get_today_meals(user_id)
    if not meals:
        await bot.send_message(user_id,
            "🌙 *Вечерний отчёт*\n\nСегодня не зафиксировано ни одного приёма пищи.",
            parse_mode="Markdown")
        return
    total_cal   = sum(m[1] for m in meals)
    total_prot  = sum(m[2] for m in meals)
    total_fat   = sum(m[3] for m in meals)
    total_carbs = sum(m[4] for m in meals)
    lines = [f"  {i}. {m[0]} — {m[5]:.0f}г → *{m[1]:.0f} ккал*" for i, m in enumerate(meals, 1)]
    if total_cal < 1500:   verdict = "😟 Маловато, не забудь поесть!"
    elif total_cal < 2200: verdict = "✅ Отличный день, норма!"
    elif total_cal < 2800: verdict = "🟡 Немного больше нормы"
    else:                  verdict = "🔴 Очень калорийный день!"
    await bot.send_message(user_id,
        f"🌙 *Вечерний отчёт — {date.today().strftime('%d.%m.%Y')}*\n\n"
        f"🍽 *Приёмы пищи:*\n" + "\n".join(lines) +
        f"\n\n━━━━━━━━━━━━━━━━━\n"
        f"🔥 Калории: *{total_cal:.0f} ккал*\n"
        f"💪 Белки:   *{total_prot:.1f} г*\n"
        f"🧈 Жиры:    *{total_fat:.1f} г*\n"
        f"🍞 Углеводы: *{total_carbs:.1f} г*\n\n{verdict}",
        parse_mode="Markdown")

# ─── SCHEDULER ────────────────────────────────────────────────────────────────
async def scheduler():
    sent_today = None
    while True:
        now = datetime.now(KYIV_TZ)
        today = now.date()
        if now.hour == 21 and now.minute == 0 and sent_today != today:
            sent_today = today
            for uid in await get_all_users():
                try:
                    await send_daily_report(uid)
                except Exception as e:
                    logger.error(f"Report error {uid}: {e}")
        await asyncio.sleep(30)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await save_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name or "")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я считаю калории по названию продукта 🍎\n\n"
        "📝 *Напиши продукт и вес:*\n"
        "`банан 150`\n`овсянка на воде 200`\n`куриная грудка 180г`\n`греческий йогурт 250`\n\n"
        "📋 *Команды:*\n"
        "/today — что ел сегодня\n/report — отчёт прямо сейчас\n/undo — удалить последнюю запись\n\n"
        "⏰ Каждый день в *21:00* по Киеву — автоматический отчёт",
        parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📝 *Как добавить продукт:*\n\n"
        "`банан 120`\n`рис варёный 200г`\n`творог 5% 150`\n\n"
        "📋 *Команды:*\n"
        "/today — что ел сегодня\n/report — отчёт прямо сейчас\n/undo — удалить последнюю запись",
        parse_mode="Markdown")

@dp.message(Command("today"))
async def cmd_today(message: Message):
    meals = await get_today_meals(message.from_user.id)
    if not meals:
        await message.answer("Сегодня ещё ничего не записано 🤷\n\nНапиши, например: `банан 150`", parse_mode="Markdown")
        return
    total_cal   = sum(m[1] for m in meals)
    total_prot  = sum(m[2] for m in meals)
    total_fat   = sum(m[3] for m in meals)
    total_carbs = sum(m[4] for m in meals)
    lines = [f"  {i}. {m[0]} — {m[5]:.0f}г → {m[1]:.0f} ккал" for i, m in enumerate(meals, 1)]
    await message.answer(
        f"📊 *Сегодня ({date.today().strftime('%d.%m.%Y')}):*\n\n" + "\n".join(lines) +
        f"\n\n━━━━━━━━━━━━━━━\n🔥 *{total_cal:.0f} ккал*  |  💪 {total_prot:.1f}г Б  |  🧈 {total_fat:.1f}г Ж  |  🍞 {total_carbs:.1f}г У",
        parse_mode="Markdown")

@dp.message(Command("report"))
async def cmd_report(message: Message):
    await send_daily_report(message.from_user.id)

@dp.message(Command("undo"))
async def cmd_undo(message: Message):
    if await delete_last_meal(message.from_user.id):
        await message.answer("✅ Последняя запись удалена!")
    else:
        await message.answer("Нечего удалять — сегодня нет записей.")

@dp.message(F.text)
async def handle_text(message: Message):
    text = message.text.strip()
    parsed = parse_user_message(text)
    if not parsed:
        await message.answer(
            "🤔 Не понял формат.\n\nНапиши продукт и вес:\n`банан 150`\n`овсянка 200г`\n`куриная грудка 180`",
            parse_mode="Markdown")
        return

    product, weight = parsed["product"], parsed["weight"]
    await save_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name or "")
    msg = await message.answer(f"🔍 Считаю калории для *{product}*...", parse_mode="Markdown")

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: search_and_calculate(product, weight))

        data = result.get("for_weight", {})
        p100 = result.get("per_100g", {})
        if not data and p100:
            data = {k: round(p100[k] * weight / 100, 1) for k in ("calories", "protein", "fat", "carbs")}

        await save_meal(message.from_user.id, result["product_name"],
                        data["calories"], data["protein"], data["fat"], data["carbs"], weight)

        await msg.edit_text(
            f"✅ *{result['product_name']}* — {weight:.0f}г\n\n"
            f"🔥 Калории: *{data['calories']:.0f} ккал*\n"
            f"💪 Белки:   *{data['protein']:.1f} г*\n"
            f"🧈 Жиры:    *{data['fat']:.1f} г*\n"
            f"🍞 Углеводы: *{data['carbs']:.1f} г*\n\n"
            f"📊 _На 100г: {p100.get('calories',0):.0f} ккал | Б {p100.get('protein',0):.1f} | Ж {p100.get('fat',0):.1f} | У {p100.get('carbs',0):.1f}_\n\n"
            f"_Записано! /today — посмотреть всё за сегодня_",
            parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text(
            f"❌ Не удалось найти *{product}*.\n\nПопробуй написать по-другому, например:\n`банан спелый 150` или `овсяная каша 200`",
            parse_mode="Markdown")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    await init_db()
    asyncio.create_task(scheduler())
    logger.info("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
