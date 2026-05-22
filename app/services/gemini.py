"""
Gemini AI service.
- ask_nutrition(): text-based lookup for unknown products
- analyse_photo():  extract nutrition from packaging photo (base64 JPEG)
"""
import asyncio
import base64
import json
import re
from typing import Optional
import urllib.request

from app.config import GEMINI_API_KEY

_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
_HEADERS = {"Content-Type": "application/json"}

_JSON_SCHEMA = (
    '{"product_name":"string",'
    '"per_100g":{"calories":number,"protein":number,"fat":number,"carbs":number}}'
)


def _call(payload: dict) -> Optional[dict]:
    url = f"{_BASE}?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = json.loads(resp.read().decode())
    except Exception:
        return None

    text = ""
    for c in raw.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            if "text" in p:
                text += p["text"]

    text = re.sub(r'```json|```', '', text).strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except Exception:
        return None


async def ask_nutrition(product_name: str) -> Optional[dict]:
    """Return nutrition per 100g for unknown product using Gemini."""
    prompt = (
        f'Exact nutrition facts per 100g for: "{product_name}". '
        f'Reply ONLY with JSON, no markdown: {_JSON_SCHEMA}'
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300},
    }
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _call, payload)


async def analyse_photo(image_bytes: bytes) -> Optional[dict]:
    """Extract product name + nutrition per 100g from packaging photo."""
    b64 = base64.standard_b64encode(image_bytes).decode()
    prompt = (
        "This is a food packaging photo. Extract the product name and nutrition facts per 100g. "
        f"Reply ONLY with JSON, no markdown: {_JSON_SCHEMA}"
    )
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400},
    }
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _call, payload)
