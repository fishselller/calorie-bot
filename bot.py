import asyncio
import logging
import json
import re
import urllib.request
from datetime import datetime, date
import pytz
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8911085987:AAGeZYdvsZlz3j_YDT30RhASI2dIKDUYLWc"
GEMINI_API_KEY = "AIzaSyC_C67WdsZ02aJ7vkACjAvHFksiyGB2YuA"
KYIV_TZ = pytz.timezone("Europe/Kyiv")
DB_PATH = "calories.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ─── ВСТРОЕННАЯ БАЗА КАЛОРИЙ (на 100г) ───────────────────────────────────────
FOOD_DB = {
    # Фрукты
    "банан": (89, 1.1, 0.3, 23),
    "яблоко": (52, 0.3, 0.2, 14),
    "апельсин": (47, 0.9, 0.1, 12),
    "груша": (57, 0.4, 0.1, 15),
    "виноград": (67, 0.6, 0.2, 17),
    "клубника": (32, 0.7, 0.3, 8),
    "арбуз": (30, 0.6, 0.1, 8),
    "дыня": (35, 0.6, 0.3, 9),
    "персик": (39, 0.9, 0.3, 10),
    "слива": (46, 0.7, 0.3, 11),
    "вишня": (52, 0.8, 0.2, 13),
    "черешня": (50, 1.1, 0.4, 12),
    "манго": (60, 0.8, 0.4, 15),
    "ананас": (50, 0.5, 0.1, 13),
    "киви": (61, 1.1, 0.5, 15),
    "лимон": (29, 1.1, 0.3, 9),
    "авокадо": (160, 2.0, 15, 9),
    "черника": (57, 0.7, 0.3, 14),
    "малина": (52, 1.2, 0.7, 12),
    "смородина": (44, 1.0, 0.2, 11),
    # Овощи
    "огурец": (15, 0.7, 0.1, 3),
    "помидор": (18, 0.9, 0.2, 4),
    "морковь": (41, 0.9, 0.2, 10),
    "капуста": (25, 1.3, 0.1, 6),
    "брокколи": (34, 2.8, 0.4, 7),
    "картофель": (77, 2.0, 0.1, 17),
    "лук": (40, 1.1, 0.1, 9),
    "чеснок": (149, 6.4, 0.5, 33),
    "перец": (31, 1.0, 0.3, 7),
    "свекла": (43, 1.6, 0.1, 10),
    "кабачок": (17, 1.2, 0.3, 3),
    "баклажан": (25, 1.2, 0.2, 6),
    "шпинат": (23, 2.9, 0.4, 4),
    "салат": (15, 1.3, 0.2, 3),
    "тыква": (26, 1.0, 0.1, 7),
    "сельдерей": (16, 0.7, 0.1, 3),
    # Крупы и каши
    "овсянка": (68, 2.4, 1.4, 12),
    "гречка": (92, 3.4, 0.6, 20),
    "рис": (116, 2.2, 0.5, 25),
    "рис варёный": (116, 2.2, 0.5, 25),
    "гречка варёная": (92, 3.4, 0.6, 20),
    "овсяная каша": (68, 2.4, 1.4, 12),
    "геркулес": (352, 12, 6, 68),
    "манная каша": (80, 3.0, 0.5, 17),
    "пшено": (90, 3.3, 1.0, 20),
    "перловка": (109, 3.0, 0.4, 24),
    "макароны": (138, 4.6, 0.7, 29),
    "макароны варёные": (138, 4.6, 0.7, 29),
    "хлеб белый": (265, 7.7, 3.2, 51),
    "хлеб чёрный": (214, 6.7, 1.2, 45),
    "хлебцы": (300, 9.0, 2.0, 65),
    # Мясо и птица
    "куриная грудка": (113, 23, 2.0, 0),
    "куриное филе": (113, 23, 2.0, 0),
    "курица": (165, 20, 9.0, 0),
    "куриное бедро": (209, 18, 15, 0),
    "говядина": (187, 20, 12, 0),
    "свинина": (242, 17, 19, 0),
    "индейка": (157, 22, 8.0, 0),
    "кролик": (183, 21, 11, 0),
    # Рыба и морепродукты
    "лосось": (208, 20, 14, 0),
    "тунец": (130, 29, 1.0, 0),
    "скумбрия": (262, 18, 21, 0),
    "треска": (82, 18, 0.7, 0),
    "минтай": (72, 16, 1.0, 0),
    "креветки": (99, 19, 2.0, 0),
    "сёмга": (208, 20, 14, 0),
    "форель": (97, 19, 2.1, 0),
    # Молочные продукты
    "творог": (121, 16, 5.0, 3),
    "творог 5%": (121, 16, 5.0, 3),
    "творог 0%": (79, 18, 0.6, 3),
    "молоко": (61, 3.2, 3.2, 5),
    "кефир": (51, 2.8, 2.5, 4),
    "йогурт": (68, 5.0, 3.2, 5),
    "греческий йогурт": (97, 9.0, 5.0, 4),
    "сметана": (206, 2.8, 20, 3),
    "сыр": (350, 26, 27, 0),
    "сыр твёрдый": (350, 26, 27, 0),
    "масло сливочное": (748, 0.8, 82, 0.8),
    "яйцо": (155, 13, 11, 1.1),
    "яйца": (155, 13, 11, 1.1),
    # Бобовые
    "фасоль": (127, 8.4, 0.5, 24),
    "горох": (116, 7.2, 0.9, 21),
    "чечевица": (116, 9.0, 0.4, 20),
    "нут": (164, 8.9, 2.6, 27),
    # Орехи
    "грецкий орех": (654, 15, 65, 14),
    "миндаль": (579, 21, 50, 22),
    "кешью": (553, 18, 44, 30),
    "арахис": (567, 26, 49, 16),
    "семечки": (601, 21, 53, 20),
    # Сладкое
    "сахар": (399, 0, 0, 100),
    "мёд": (304, 0.8, 0, 82),
    "шоколад": (546, 5.4, 35, 60),
    "шоколад тёмный": (546, 5.4, 35, 60),
    "мороженое": (207, 3.7, 11, 26),
    "печенье": (417, 6.4, 15, 67),
    # Разное
    "масло растительное": (884, 0, 100, 0),
    "майонез": (680, 2.8, 74, 3.6),
    "кетчуп": (112, 1.8, 0.1, 27),
    "соль": (0, 0, 0, 0),
}

def find_in_db(product_name: str):
    """Ищет продукт в базе, возвращает (calories, protein, fat, carbs) на 100г или None."""
    name = product_name.lower().strip()
    # Точное совпадение
    if name in FOOD_DB:
        return FOOD_DB[name]
    # Частичное совпадение
    for key in FOOD_DB:
        if key in name or name in key:
            return FOOD_DB[key]
    return None

# ─── GEMINI API (резерв если нет в базе) ─────────────────────────────────────
def ask_gemini(product_name: str, weight_grams: float) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = (
        f'Дай точные данные БЖУ и калории для продукта "{product_name}" на 100г. '
        f'Рассчитай для {weight_grams}г. '
        f'Ответь ТОЛЬКО JSON без markdown: '
        f'{{"product_name":"название","per_100g":{{"calories":0,"protein":0,"fat":0,"carbs":0}},'
        f'"for_weight":{{"calories":0,"protein":0,"fat":0,"carbs":0}}}}'
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300}
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = ""
    for c in data.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            if "text" in p:
                text += p["text"]
    text = text.strip().replace("```json", "").replace("```", "").strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        return json.loads(m.group())
    raise ValueError("No JSON in Gemini response")

def get_nutrition(product_name: str, weight_grams: float) -> dict:
    """Сначала ищет в базе, потом спрашивает Gemini."""
    db_result = find_in_db(product_name)
    if db_result:
        cal100, prot100, fat100, carb100 = db_result
        factor = weight_grams / 100
        return {
            "product_name": product_name,
            "per_100g": {"calories": cal100, "protein": prot100, "fat": fat100, "carbs": carb100},
            "for_weight": {
                "calories": round(cal100 * factor, 1),
                "protein":  round(prot100 * factor, 1),
                "fat":      round(fat100 * factor, 1),
                "carbs":    round(carb100 * factor, 1),
            },
            "source": "база данных"
        }
    # Резерв — Gemini
    result = ask_gemini(product_name, weight_grams)
    p100 = result.get("per_100g", {})
    fw = result.get("for_weight", {})
    if not fw and p100:
        factor = weight_grams / 100
        fw = {k: round(p100[k] * factor, 1) for k in p100}
    result["for_weight"] = fw
    result["source"] = "Gemini AI"
    return result

# ─── DATABASE ─────────────────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, date TEXT NOT NULL,
            description TEXT, calories REAL, protein REAL,
            fat REAL, carbs REAL, weight REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT)""")
        await db.commit()

async def save_user(uid, username, first_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", (uid, username, first_name))
        await db.commit()

async def save_meal(uid, desc, cal, prot, fat, carbs, weight):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO meals (user_id,date,description,calories,protein,fat,carbs,weight) VALUES (?,?,?,?,?,?,?,?)",
            (uid, date.today().isoformat(), desc, cal, prot, fat, carbs, weight))
        await db.commit()

async def delete_last_meal(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM meals WHERE user_id=? AND date=? ORDER BY created_at DESC LIMIT 1",
            (uid, date.today().isoformat())) as cur:
            row = await cur.fetchone()
        if row:
            await db.execute("DELETE FROM meals WHERE id=?", (row[0],))
            await db.commit()
            return True
    return False

async def get_today_meals(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT description,calories,protein,fat,carbs,weight FROM meals WHERE user_id=? AND date=? ORDER BY created_at",
            (uid, date.today().isoformat())) as cur:
            return await cur.fetchall()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            return [r[0] for r in await cur.fetchall()]

# ─── PARSE ────────────────────────────────────────────────────────────────────
def parse_message(text):
    text = text.strip()
    for i, pat in enumerate([
        r'^(.+?)\s+(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|g)?$',
        r'^(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|g)?\s+(.+)$'
    ]):
        m = re.match(pat, text, re.IGNORECASE)
        if m:
            prod, ws = (m.group(1).strip(), m.group(2)) if i == 0 else (m.group(2).strip(), m.group(1))
            w = float(ws.replace(",", "."))
            if 0 < w <= 10000 and len(prod) >= 2:
                return {"product": prod, "weight": w}
    return None

# ─── REPORT ───────────────────────────────────────────────────────────────────
async def send_daily_report(uid):
    meals = await get_today_meals(uid)
    if not meals:
        await bot.send_message(uid, "🌙 *Вечерний отчёт*\n\nСегодня ничего не записано.", parse_mode="Markdown")
        return
    tc = sum(m[1] for m in meals)
    tp = sum(m[2] for m in meals)
    tf = sum(m[3] for m in meals)
    tcarb = sum(m[4] for m in meals)
    lines = [f"  {i}. {m[0]} — {m[5]:.0f}г → *{m[1]:.0f} ккал*" for i, m in enumerate(meals, 1)]
    verdict = "😟 Маловато!" if tc < 1500 else "✅ Норма!" if tc < 2200 else "🟡 Чуть больше нормы" if tc < 2800 else "🔴 Очень много!"
    await bot.send_message(uid,
        f"🌙 *Отчёт за {date.today().strftime('%d.%m.%Y')}*\n\n" + "\n".join(lines) +
        f"\n\n━━━━━━━━━━━━━━━\n🔥 *{tc:.0f} ккал* | 💪 {tp:.1f}г Б | 🧈 {tf:.1f}г Ж | 🍞 {tcarb:.1f}г У\n\n{verdict}",
        parse_mode="Markdown")

async def scheduler():
    sent = None
    while True:
        now = datetime.now(KYIV_TZ)
        if now.hour == 21 and now.minute == 0 and sent != now.date():
            sent = now.date()
            for uid in await get_all_users():
                try: await send_daily_report(uid)
                except Exception as e: logger.error(e)
        await asyncio.sleep(30)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def start(msg: Message):
    await save_user(msg.from_user.id, msg.from_user.username or "", msg.from_user.first_name or "")
    await msg.answer(
        f"👋 Привет, {msg.from_user.first_name}!\n\n"
        "Пиши продукт и вес — я посчитаю калории 🍎\n\n"
        "`банан 150`\n`куриная грудка 200г`\n`овсянка 200`\n`творог 5% 150`\n\n"
        "📋 /today — сегодня | /report — отчёт | /undo — удалить последнее\n\n"
        "⏰ Каждый день в *21:00* по Киеву — автоматический отчёт",
        parse_mode="Markdown")

@dp.message(Command("today"))
async def today(msg: Message):
    meals = await get_today_meals(msg.from_user.id)
    if not meals:
        await msg.answer("Сегодня ещё ничего не записано.\n\nНапиши, например: `банан 150`", parse_mode="Markdown")
        return
    tc = sum(m[1] for m in meals)
    tp = sum(m[2] for m in meals)
    tf = sum(m[3] for m in meals)
    tcarb = sum(m[4] for m in meals)
    lines = [f"  {i}. {m[0]} — {m[5]:.0f}г → {m[1]:.0f} ккал" for i, m in enumerate(meals, 1)]
    await msg.answer(
        f"📊 *{date.today().strftime('%d.%m.%Y')}*\n\n" + "\n".join(lines) +
        f"\n\n━━━━━━━━━━━━━━━\n🔥 *{tc:.0f} ккал* | 💪 {tp:.1f}г Б | 🧈 {tf:.1f}г Ж | 🍞 {tcarb:.1f}г У",
        parse_mode="Markdown")

@dp.message(Command("report"))
async def report(msg: Message):
    await send_daily_report(msg.from_user.id)

@dp.message(Command("undo"))
async def undo(msg: Message):
    await msg.answer("✅ Удалено!" if await delete_last_meal(msg.from_user.id) else "Нечего удалять.")

@dp.message(F.text)
async def handle(msg: Message):
    parsed = parse_message(msg.text)
    if not parsed:
        await msg.answer(
            "🤔 Напиши продукт и вес:\n`банан 150`\n`куриная грудка 200г`\n`овсянка 200`",
            parse_mode="Markdown")
        return
    product, weight = parsed["product"], parsed["weight"]
    await save_user(msg.from_user.id, msg.from_user.username or "", msg.from_user.first_name or "")
    m = await msg.answer(f"🔍 Считаю *{product}*...", parse_mode="Markdown")
    try:
        result = await asyncio.get_event_loop().run_in_executor(None, lambda: get_nutrition(product, weight))
        d = result["for_weight"]
        p = result["per_100g"]
        await save_meal(msg.from_user.id, result["product_name"], d["calories"], d["protein"], d["fat"], d["carbs"], weight)
        await m.edit_text(
            f"✅ *{result['product_name']}* — {weight:.0f}г\n\n"
            f"🔥 Калории: *{d['calories']:.0f} ккал*\n"
            f"💪 Белки:   *{d['protein']:.1f} г*\n"
            f"🧈 Жиры:    *{d['fat']:.1f} г*\n"
            f"🍞 Углеводы: *{d['carbs']:.1f} г*\n\n"
            f"📊 _На 100г: {p['calories']:.0f} ккал | Б {p['protein']:.1f} | Ж {p['fat']:.1f} | У {p['carbs']:.1f}_\n\n"
            f"_/today — всё за сегодня_",
            parse_mode="Markdown")
    except Exception as e:
        logger.error(e)
        await m.edit_text(f"❌ Не нашёл *{product}*. Попробуй написать иначе.", parse_mode="Markdown")

async def main():
    await init_db()
    asyncio.create_task(scheduler())
    logger.info("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
