import base64
import json
import re
import urllib.request

from aiogram import Router, F, Bot
from aiogram.types import Message

from app.db.engine import AsyncSessionLocal
from app.db.models import User, Product
from app.localization.texts import t
from app.config import OPENAI_API_KEY

router = Router()


async def _get_or_create_user(uid: int, session) -> User:
    user = await session.get(User, uid)
    if user is None:
        user = User(id=uid, language="ru")
        session.add(user)
        await session.commit()
    return user


def _analyse_with_openai(image_bytes: bytes) -> dict | None:
    b64 = base64.standard_b64encode(image_bytes).decode()
    prompt = (
        "This is a food packaging photo. Extract the product name and nutrition facts per 100g. "
        'Reply ONLY with JSON, no markdown: {"product_name":"...","per_100g":{"calories":0,"protein":0,"fat":0,"carbs":0}}'
    )
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "max_tokens": 400,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": prompt},
            ]
        }]
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        text = data["choices"][0]["message"]["content"]
        text = re.sub(r'```json|```', '', text).strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return None


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(message.from_user.id, session)
        lang = user.language

    processing = await message.answer(t("photo_processing", lang))

    photo  = message.photo[-1]
    file   = await bot.get_file(photo.file_id)
    buf    = await bot.download_file(file.file_path)
    img    = buf.read()

    import asyncio
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _analyse_with_openai(img)
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
