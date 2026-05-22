"""
Nutrition resolution pipeline:
  1. Built-in DB  (food_db.lookup)
  2. User-saved products (DB table products)
  3. Gemini AI fallback
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product
from app.services import food_db, gemini


@dataclass
class NutritionResult:
    product_name: str
    grams:        float
    calories:     float
    protein:      float
    fat:          float
    carbs:        float
    source:       str   # "db" | "user_db" | "ai"


async def resolve(
    raw_name: str,
    grams: float,
    session: AsyncSession,
) -> Optional[NutritionResult]:
    """Find nutrition data for a product and calculate for given grams."""

    factor = grams / 100.0

    # 1. Built-in DB
    match = food_db.lookup(raw_name)
    if match:
        name, (kcal, prot, fat, carb) = match
        return NutritionResult(
            product_name=name,
            grams=grams,
            calories=round(kcal * factor, 1),
            protein=round(prot * factor, 1),
            fat=round(fat * factor, 1),
            carbs=round(carb * factor, 1),
            source="db",
        )

    # 2. User-saved products table
    stmt = select(Product).where(Product.name.ilike(f"%{raw_name}%")).limit(1)
    result = await session.execute(stmt)
    prod: Optional[Product] = result.scalar_one_or_none()
    if prod:
        return NutritionResult(
            product_name=prod.name,
            grams=grams,
            calories=round(prod.calories * factor, 1),
            protein=round(prod.protein * factor, 1),
            fat=round(prod.fat * factor, 1),
            carbs=round(prod.carbs * factor, 1),
            source="user_db",
        )

    # 3. Gemini AI
    ai = await gemini.ask_nutrition(raw_name)
    if ai and "per_100g" in ai:
        p = ai["per_100g"]
        name = ai.get("product_name", raw_name)
        kcal  = float(p.get("calories", 0))
        prot  = float(p.get("protein",  0))
        fat_v = float(p.get("fat",      0))
        carb  = float(p.get("carbs",    0))
        # Persist for future use
        new_prod = Product(name=name.lower(), calories=kcal,
                           protein=prot, fat=fat_v, carbs=carb)
        session.add(new_prod)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        return NutritionResult(
            product_name=name,
            grams=grams,
            calories=round(kcal * factor, 1),
            protein=round(prot * factor, 1),
            fat=round(fat_v * factor, 1),
            carbs=round(carb * factor, 1),
            source="ai",
        )

    return None
