from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import MealPlan

async def create_meal_plan(user_id: str, products: list[str], days: int, meals: int, plan_text: str):
    async with AsyncSessionLocal() as session:
        plan = MealPlan(
            user_id=user_id,
            products=", ".join(products),
            days=days,
            meals_per_day=meals,
            plan_text=plan_text
        )
        session.add(plan)
        await session.commit()
        return plan


async def get_meal_plan(user_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MealPlan).where(MealPlan.user_id == user_id)
        )
        return result.scalars().first()
