import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import TELEGRAM_TOKEN
from app.db import init_db
from app.handlers import setup_routers
from app.scheduler import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Init DB
    await init_db()
    logger.info("Database ready")

    # Bot + dispatcher
    bot        = Bot(token=TELEGRAM_TOKEN)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(setup_routers())

    # Scheduler
    scheduler = create_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    # Start polling
    logger.info("Bot polling started")
    try:
        await dispatcher.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
