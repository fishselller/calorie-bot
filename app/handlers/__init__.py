from aiogram import Router


def setup_routers() -> Router:
    from app.handlers.start  import router as start_router
    from app.handlers.report import router as report_router
    from app.handlers.photo  import router as photo_router
    from app.handlers.help   import router as help_router
    from app.handlers.stats  import router as stats_router
    from app.handlers.food   import router as food_router

    root = Router()
    root.include_router(start_router)
    root.include_router(report_router)
    root.include_router(photo_router)
    root.include_router(help_router)
    root.include_router(stats_router)
    root.include_router(food_router)
    return root
