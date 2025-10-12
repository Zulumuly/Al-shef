from sqlalchemy import Column, Integer, String
from db.database import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # 👈 раньше было String
    products = Column(String)
    days = Column(Integer)
    meals_per_day = Column(Integer)
    plan_text = Column(String)
