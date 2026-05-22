from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product


@dataclass
class NutritionResult:
    product_name: str
    grams:        float
    calories:     float
    protein:      float
    fat:          float
    carbs:        float
    source:       str


async def resolve(
    raw_name: str,
    grams: float,
    session: AsyncSession,
) -> Optional[NutritionResult]:
    from app.services.food_db import lookup
    from app.services.gemini  import ask_nutrition

    factor = grams / 100.0

    # 1. User-saved products (highest priority)
    stmt = select(Product).where(
        Product.name.ilike(f"%{raw_name.lower()}%")
    ).limit(1)
    result = await session.execute(stmt)
    prod: Optional[Product] = result.scalar_one_or_none()
    if prod:
        return NutritionResult(
            product_name=prod.name, grams=grams,
            calories=round(prod.calories * factor, 1),
            protein=round(prod.protein * factor, 1),
            fat=round(prod.fat * factor, 1),
            carbs=round(prod.carbs * factor, 1),
            source="user_db",
        )

    # 2. Built-in DB
    match = lookup(raw_name)
    if match:
        name, (kcal, prot, fat, carb) = match
        return NutritionResult(
            product_name=name, grams=grams,
            calories=round(kcal * factor, 1),
            protein=round(prot * factor, 1),
            fat=round(fat * factor, 1),
            carbs=round(carb * factor, 1),
            source="db",
        )

    # 3. Gemini AI fallback
    ai = await ask_nutrition(raw_name)
    if ai and "per_100g" in ai:
        p     = ai["per_100g"]
        name  = ai.get("product_name", raw_name)
        kcal  = float(p.get("calories", 0))
        prot  = float(p.get("protein",  0))
        fat_v = float(p.get("fat",      0))
        carb  = float(p.get("carbs",    0))
        new_prod = Product(
            name=raw_name.lower(), calories=kcal,
            protein=prot, fat=fat_v, carbs=carb,
        )
        session.add(new_prod)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        return NutritionResult(
            product_name=name, grams=grams,
            calories=round(kcal * factor, 1),
            protein=round(prot * factor, 1),
            fat=round(fat_v * factor, 1),
            carbs=round(carb * factor, 1),
            source="ai",
        )

    return None
