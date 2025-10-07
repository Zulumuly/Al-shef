# db/models.py
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from datetime import datetime
import uuid
from .database import Base


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    plan_md = Column(Text, nullable=False)
    requested_days = Column(Integer, nullable=False)
    meals_per_day = Column(Integer, nullable=False)
    feasible_days = Column(Integer, nullable=True)
    decision = Column(String(50), nullable=True)  # "ok", "reduce", "need_purchases"
    ingredients = Column(JSON, nullable=True)  # список продуктов
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NutritionPlan(id={self.id}, user_id={self.user_id}, title={self.title})>"


class SavedRecipe(Base):
    __tablename__ = "saved_recipes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("nutrition_plans.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    recipe_md = Column(Text, nullable=False)  # рецепт в Markdown
    ingredients = Column(JSON, nullable=True)  # продукты рецепта
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SavedRecipe(id={self.id}, user_id={self.user_id}, title={self.title})>"
