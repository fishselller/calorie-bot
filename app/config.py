import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL: str   = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nutrition.db")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set")
