from sqlalchemy import Column, Integer, String, Text
from db.database import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    products = Column(Text)
    days = Column(Integer)
    meals_per_day = Column(Integer)
    plan_text = Column(Text)
