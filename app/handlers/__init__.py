from aiogram import Router


def setup_routers() -> Router:
    from app.handlers import start, food, photo, report
    root = Router()
    root.include_router(start.router)
    root.include_router(report.router)
    root.include_router(photo.router)
    root.include_router(food.router)
    return root
