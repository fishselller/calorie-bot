import asyncio
import base64
import json
import logging
import re
import urllib.request
import urllib.error

from aiogram import Router, F, Bot
from aiogram.types import Message

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Product
from app.localization.texts import t
from app.config import GEMINI_API_KEY

router = Router()
logger = logging.getLogger(__name__)


async def _get_or_create_user(uid: int, session) -> User:
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


def _call_gemini_vision(image_bytes: bytes) -> dict | None:
    b64 = base64.standard_b64encode(image_bytes).decode()
    prompt = (
        "На фото упаковка продукта питания. "
        "Найди и извлеки пищевую ценность на 100г продукта. "
        "Верни ТОЛЬКО JSON без markdown: "
        '{"product_name":"название","per_100g":{"calories":0,"protein":0,"fat":0,"carbs":0}}'
    )
    payload = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300},
    }).encode()

    # Try both v1 and v1beta with different models
    attempts = [
        ("v1", "gemini-2.0-flash"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-2.0-flash"),
        ("v1beta", "gemini-2.0-flash-lite"),
    ]

    for version, model in attempts:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            text = ""
            for c in data.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "text" in p:
                        text += p["text"]

            logger.info(f"{version}/{model} response: {text[:200]}")
            text = re.sub(r'```json|```', '', text).strip()
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                result = json.loads(m.group())
                if "per_100g" in result:
                    logger.info(f"Success: {version}/{model}")
                    return result
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            logger.error(f"{version}/{model} HTTP {e.code}: {body[:200]}")
        except Exception as e:
            logger.error(f"{version}/{model} error: {e}")

    return None


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language

    processing = await message.answer(t("photo_processing", lang))

    photo = message.photo[-1]
    file  = await bot.get_file(photo.file_id)
    buf   = await bot.download_file(file.file_path)
    img   = buf.read()

    logger.info(f"Photo size: {len(img)} bytes")

    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _call_gemini_vision(img)
    )

    if not result or "per_100g" not in result:
        await processing.edit_text(t("photo_fail", lang))
        return

    p    = result["per_100g"]
    name = result.get("product_name", "unknown").lower()

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        existing = (await session.execute(
            select(Product).where(Product.name == name)
        )).scalar_one_or_none()
        if not existing:
            prod = Product(
                name     = name,
                calories = float(p.get("calories", 0)),
                protein  = float(p.get("protein",  0)),
                fat      = float(p.get("fat",      0)),
                carbs    = float(p.get("carbs",    0)),
            )
            session.add(prod)
            await session.commit()

    await processing.edit_text(
        t("photo_ok", lang, name=name), parse_mode="Markdown"
    )
