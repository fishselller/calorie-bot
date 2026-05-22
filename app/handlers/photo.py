import asyncio
import base64
import json
import logging
import re
import time
import urllib.request
import urllib.error

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Product
from app.localization.texts import t
from app.config import GEMINI_API_KEY

router = Router()
logger = logging.getLogger(__name__)


class PhotoState(StatesGroup):
    waiting_name   = State()
    waiting_weight = State()


async def _get_or_create_user(uid: int, session) -> User:
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


def _extract_json(text: str) -> dict | None:
    text = re.sub(r'```(?:json)?', '', text).strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


def _call_gemini_vision(image_bytes: bytes) -> dict | None:
    b64 = base64.standard_b64encode(image_bytes).decode()
    prompt = (
        "Extract ONLY nutrition facts per 100g from this food label. "
        "Return ONLY JSON:\n"
        '{"per_100g":{"calories":0,"protein":0,"fat":0,"carbs":0}}'
    )
    payload = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 1024},
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    for attempt in range(4):
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                data = json.loads(resp.read().decode())
            text = ""
            for c in data.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "text" in p:
                        text += p["text"]
            logger.info(f"Attempt {attempt+1}: {repr(text)}")
            result = _extract_json(text)
            if result and result.get("per_100g", {}).get("calories") is not None:
                return result
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            logger.error(f"HTTP {e.code}: {body[:200]}")
            if e.code == 503:
                time.sleep(3)
                continue
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(2)
    return None


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language

    processing = await message.answer(t("photo_processing", lang))

    photo = message.photo[-1]
    file  = await bot.get_file(photo.file_id)
    buf   = await bot.download_file(file.file_path)
    img   = buf.read()

    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _call_gemini_vision(img)
    )

    if not result or "per_100g" not in result:
        await processing.edit_text(t("photo_fail", lang))
        return

    p = result["per_100g"]

    # Save nutrition to state
    await state.update_data(photo_nutrition={
        "calories": float(p.get("calories", 0)),
        "protein":  float(p.get("protein",  0)),
        "fat":      float(p.get("fat",      0)),
        "carbs":    float(p.get("carbs",    0)),
        "lang":     lang,
    })
    await state.set_state(PhotoState.waiting_name)

    ask_name = {
        "ru": f"✅ БЖУ считано!\n\n🔥 {p.get('calories',0):.0f} ккал | 💪 Б {p.get('protein',0):.1f}г | 🧈 Ж {p.get('fat',0):.1f}г | 🍞 У {p.get('carbs',0):.1f}г\n\nКак называется этот продукт?",
        "uk": f"✅ БЖУ зчитано!\n\n🔥 {p.get('calories',0):.0f} ккал | 💪 Б {p.get('protein',0):.1f}г | 🧈 Ж {p.get('fat',0):.1f}г | 🍞 У {p.get('carbs',0):.1f}г\n\nЯк називається цей продукт?",
        "en": f"✅ Nutrition read!\n\n🔥 {p.get('calories',0):.0f} kcal | 💪 P {p.get('protein',0):.1f}g | 🧈 F {p.get('fat',0):.1f}g | 🍞 C {p.get('carbs',0):.1f}g\n\nWhat is this product called?",
    }
    await processing.edit_text(ask_name.get(lang, ask_name["ru"]))


@router.message(PhotoState.waiting_name, F.text)
async def handle_product_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    nutrition = data.get("photo_nutrition", {})
    lang = nutrition.get("lang", "ru")
    product_name = message.text.strip()

    await state.update_data(photo_nutrition={**nutrition, "product_name": product_name})
    await state.set_state(PhotoState.waiting_weight)

    ask_weight = {
        "ru": f"Сколько грамм *{product_name}* ты съел?\nНапример: `150`",
        "uk": f"Скільки грамів *{product_name}* ти з'їв?\nНаприклад: `150`",
        "en": f"How many grams of *{product_name}* did you eat?\nE.g.: `150`",
    }
    await message.answer(ask_weight.get(lang, ask_weight["ru"]), parse_mode="Markdown")


@router.message(PhotoState.waiting_weight, F.text)
async def handle_photo_weight(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    nutrition = data.get("photo_nutrition", {})
    lang = nutrition.get("lang", "ru")

    try:
        weight = float(message.text.strip().replace(",", "."))
        if weight <= 0 or weight > 10000:
            raise ValueError
    except ValueError:
        await message.answer("Введи вес числом, например: `150`", parse_mode="Markdown")
        return

    factor = weight / 100
    cal   = round(nutrition["calories"] * factor, 1)
    prot  = round(nutrition["protein"]  * factor, 1)
    fat   = round(nutrition["fat"]      * factor, 1)
    carbs = round(nutrition["carbs"]    * factor, 1)
    name  = nutrition.get("product_name", "продукт")

    # Save product to DB
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        existing = (await session.execute(
            select(Product).where(Product.name == name.lower())
        )).scalar_one_or_none()
        if not existing:
            prod = Product(
                name     = name.lower(),
                calories = nutrition["calories"],
                protein  = nutrition["protein"],
                fat      = nutrition["fat"],
                carbs    = nutrition["carbs"],
            )
            session.add(prod)
            await session.commit()

    await state.update_data(nutrition={
        "product_name": name,
        "grams":    weight,
        "calories": cal,
        "protein":  prot,
        "fat":      fat,
        "carbs":    carbs,
    })

    # Ask meal type
    from app.keyboards.inline import meal_type_keyboard
    ask_meal = {
        "ru": f"✅ *{name}* — {weight:.0f}г\n🔥 {cal:.0f} ккал | 💪 Б {prot:.1f}г | 🧈 Ж {fat:.1f}г | 🍞 У {carbs:.1f}г\n\nК какому приёму пищи?",
        "uk": f"✅ *{name}* — {weight:.0f}г\n🔥 {cal:.0f} ккал | 💪 Б {prot:.1f}г | 🧈 Ж {fat:.1f}г | 🍞 У {carbs:.1f}г\n\nДо якого прийому їжі?",
        "en": f"✅ *{name}* — {weight:.0f}g\n🔥 {cal:.0f} kcal | 💪 P {prot:.1f}g | 🧈 F {fat:.1f}g | 🍞 C {carbs:.1f}g\n\nWhich meal?",
    }
    await message.answer(
        ask_meal.get(lang, ask_meal["ru"]),
        parse_mode="Markdown",
        reply_markup=meal_type_keyboard(lang),
    )

    # Store for meal_type callback
    from datetime import date
    from app.db.models import Meal
    # Will be saved when user picks meal type via callback
    # Store pending in bot data
    message.bot["pending"] = message.bot.get("pending", {})
    message.bot["pending"][message.from_user.id] = {
        "product_name": name,
        "grams":    weight,
        "calories": cal,
        "protein":  prot,
        "fat":      fat,
        "carbs":    carbs,
        "lang":     lang,
    }
    await state.clear()
