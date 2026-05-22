from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True)
    language   = Column(String(5), default="ru")
    timezone   = Column(String(50), default="Europe/Kyiv")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Daily norms (set by user)
    cal_norm   = Column(Float, nullable=True)
    prot_norm  = Column(Float, nullable=True)
    fat_norm   = Column(Float, nullable=True)
    carb_norm  = Column(Float, nullable=True)

    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(200), unique=True, nullable=False, index=True)
    calories   = Column(Float, nullable=False)
    protein    = Column(Float, nullable=False)
    fat        = Column(Float, nullable=False)
    carbs      = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Meal(Base):
    __tablename__ = "meals"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    grams        = Column(Float, nullable=False)
    calories     = Column(Float, nullable=False)
    protein      = Column(Float, nullable=False)
    fat          = Column(Float, nullable=False)
    carbs        = Column(Float, nullable=False)
    meal_type    = Column(String(20), nullable=False)
    date         = Column(Date, default=date.today, index=True)
    created_at   = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="meals")


class WeightLog(Base):
    __tablename__ = "weight_log"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    weight     = Column(Float, nullable=False)
    date       = Column(Date, default=date.today, index=True)
    created_at = Column(DateTime, server_default=func.now())
