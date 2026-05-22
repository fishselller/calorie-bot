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

    prompt = """Look at this food packaging image and extract nutrition facts per 100g.

Output ONLY a JSON object, nothing else, no explanation, no text before or after:
{"product_name":"<name>","per_100g":{"calories":<number>,"protein":<number>,"fat":<number>,"carbs":<number>}}"""

    payload = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 150,
        },
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

            logger.info(f"Attempt {attempt+1}: {text[:300]}")

            # Extract JSON from anywhere in the text
            text_clean = re.sub(r'```json|```', '', text).strip()
            m = re.search(r'\{[^{}]*"per_100g"[^{}]*\{[^{}]*\}[^{}]*\}', text_clean, re.DOTALL)
            if m:
                result = json.loads(m.group())
                p100 = result.get("per_100g", {})
                if p100.get("calories") is not None:
                    logger.info(f"Success: {result}")
                    return result

        except urllib.error.HTTPError as e:
            body = e.read().decode()
            logger.error(f"Attempt {attempt+1} HTTP {e.code}: {body[:200]}")
            if e.code == 503:
                time.sleep(3)
                continue
            break
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Attempt {attempt+1} error: {e}")
            time.sleep(2)

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
